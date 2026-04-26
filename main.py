from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
import os
import calendar as cal

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tasks.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    done = Column(Boolean, default=False)
    priority = Column(Integer, default=4)
    project = Column(String, default="Inbox")
    due_date = Column(String, nullable=True)
    owner = Column(String, default="Anish", server_default="Anish")
    recurrence = Column(String, nullable=True)  # 'daily' | 'weekdays' | 'weekly' | 'monthly'
    is_frog = Column(Boolean, default=False, server_default="false")
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    color = Column(String, default="#4073ff")
    owner = Column(String, nullable=False)


Base.metadata.create_all(bind=engine)

# Lightweight migrations for columns added after the initial schema.
# ALTER ADD COLUMN throws if the column already exists; swallow that.
with engine.connect() as conn:
    for ddl in [
        "ALTER TABLE tasks ADD COLUMN owner VARCHAR DEFAULT 'Anish'",
        "ALTER TABLE tasks ADD COLUMN recurrence VARCHAR",
        "ALTER TABLE tasks ADD COLUMN deleted_at TIMESTAMP",
        "ALTER TABLE tasks ADD COLUMN is_frog BOOLEAN DEFAULT FALSE",
    ]:
        try:
            conn.execute(text(ddl))
            conn.commit()
        except Exception:
            conn.rollback()

# Hard-purge soft-deleted tasks older than 30 days on startup.
with SessionLocal() as db:
    cutoff = datetime.utcnow() - timedelta(days=30)
    db.query(Task).filter(Task.deleted_at != None, Task.deleted_at < cutoff).delete(synchronize_session=False)
    db.commit()


app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def advance_due_date(due: Optional[str], recurrence: str) -> Optional[str]:
    """Bump an ISO date forward according to the recurrence rule.
    If no due date set, base the next occurrence on today."""
    base = datetime.fromisoformat(due).date() if due else datetime.utcnow().date()
    if recurrence == "daily":
        nxt = base + timedelta(days=1)
    elif recurrence == "weekly":
        nxt = base + timedelta(days=7)
    elif recurrence == "weekdays":
        nxt = base + timedelta(days=1)
        while nxt.weekday() >= 5:
            nxt += timedelta(days=1)
    elif recurrence == "monthly":
        m = base.month + 1
        y = base.year + (1 if m > 12 else 0)
        m = ((m - 1) % 12) + 1
        last = cal.monthrange(y, m)[1]
        nxt = base.replace(year=y, month=m, day=min(base.day, last))
    else:
        return due
    return nxt.isoformat()


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: int = 4
    project: str = "Inbox"
    due_date: Optional[str] = None
    owner: str = "Anish"
    recurrence: Optional[str] = None
    done: Optional[bool] = False


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    done: Optional[bool] = None
    priority: Optional[int] = None
    project: Optional[str] = None
    due_date: Optional[str] = None
    recurrence: Optional[str] = None
    is_frog: Optional[bool] = None


class ProjectCreate(BaseModel):
    name: str
    color: str = "#4073ff"
    owner: str = "Anish"


class ProjectUpdate(BaseModel):
    color: str


@app.get("/api/tasks")
def get_tasks(
    project: Optional[str] = None,
    done: Optional[bool] = None,
    owner: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Task).filter(Task.deleted_at == None)
    if owner:
        query = query.filter(Task.owner == owner)
    if project:
        query = query.filter(Task.project == project)
    if done is not None:
        query = query.filter(Task.done == done)
    return query.order_by(Task.priority, Task.created_at).all()


@app.post("/api/tasks")
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    data = task.dict()
    if data.get("done"):
        data["completed_at"] = datetime.utcnow()
    db_task = Task(**data)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@app.patch("/api/tasks/{task_id}")
def update_task(task_id: int, task: TaskUpdate, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    update_data = task.dict(exclude_unset=True)

    # Recurring task completion: spawn the next instance, then mark current done.
    if update_data.get("done") and db_task.recurrence and not db_task.done:
        next_due = advance_due_date(db_task.due_date, db_task.recurrence)
        spawn = Task(
            title=db_task.title,
            description=db_task.description,
            priority=db_task.priority,
            project=db_task.project,
            owner=db_task.owner,
            due_date=next_due,
            recurrence=db_task.recurrence,
        )
        db.add(spawn)

    if update_data.get("done"):
        update_data["completed_at"] = datetime.utcnow()
        # Completing a frog task naturally retires it.
        update_data["is_frog"] = False
    elif "done" in update_data and not update_data["done"]:
        update_data["completed_at"] = None

    # Only one frog at a time per user — clear it on others when setting.
    if update_data.get("is_frog"):
        db.query(Task).filter(
            Task.owner == db_task.owner,
            Task.id != db_task.id,
            Task.is_frog == True,
        ).update({"is_frog": False}, synchronize_session=False)

    for key, value in update_data.items():
        setattr(db_task, key, value)
    db.commit()
    db.refresh(db_task)
    return db_task


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Soft-delete: set deleted_at. Auto-purged after 30 days on startup."""
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    db_task.deleted_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "id": task_id}


@app.post("/api/tasks/{task_id}/restore")
def restore_task(task_id: int, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    db_task.deleted_at = None
    db.commit()
    db.refresh(db_task)
    return db_task


@app.get("/api/projects")
def get_projects(owner: Optional[str] = None, db: Session = Depends(get_db)):
    task_query = db.query(Task.project, Task.done).filter(Task.deleted_at == None)
    if owner:
        task_query = task_query.filter(Task.owner == owner)
    counts: dict = {}
    for row in task_query.all():
        p = row[0]
        if p not in counts:
            counts[p] = {"total": 0, "pending": 0}
        counts[p]["total"] += 1
        if not row[1]:
            counts[p]["pending"] += 1

    proj_query = db.query(Project)
    if owner:
        proj_query = proj_query.filter(Project.owner == owner)
    color_map = {p.name: p.color for p in proj_query.all()}

    all_names = set(counts.keys()) | set(color_map.keys())
    return [
        {
            "name": name,
            "color": color_map.get(name, "#4073ff"),
            "total": counts.get(name, {}).get("total", 0),
            "pending": counts.get(name, {}).get("pending", 0),
        }
        for name in all_names
    ]


@app.post("/api/projects")
def create_project(proj: ProjectCreate, db: Session = Depends(get_db)):
    existing = db.query(Project).filter(Project.name == proj.name, Project.owner == proj.owner).first()
    if existing:
        existing.color = proj.color
        db.commit()
        db.refresh(existing)
        return existing
    db_proj = Project(**proj.dict())
    db.add(db_proj)
    db.commit()
    db.refresh(db_proj)
    return db_proj


@app.patch("/api/projects/{project_name}")
def update_project_color(project_name: str, update: ProjectUpdate, owner: str = "Anish", db: Session = Depends(get_db)):
    proj = db.query(Project).filter(Project.name == project_name, Project.owner == owner).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    proj.color = update.color
    db.commit()
    db.refresh(proj)
    return proj


@app.delete("/api/projects/{project_name}")
def delete_project(project_name: str, owner: str = "Anish", db: Session = Depends(get_db)):
    proj = db.query(Project).filter(Project.name == project_name, Project.owner == owner).first()
    if proj:
        db.delete(proj)
        db.commit()
    return {"ok": True}


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/{full_path:path}")
def catch_all(full_path: str):
    return FileResponse("static/index.html")
