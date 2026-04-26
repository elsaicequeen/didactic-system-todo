from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import os

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
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


Base.metadata.create_all(bind=engine)

# Add owner column to existing tables that predate this migration
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE tasks ADD COLUMN owner VARCHAR DEFAULT 'Anish'"))
        conn.commit()
    except Exception:
        pass  # column already exists

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: int = 4
    project: str = "Inbox"
    due_date: Optional[str] = None
    owner: str = "Anish"


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    done: Optional[bool] = None
    priority: Optional[int] = None
    project: Optional[str] = None
    due_date: Optional[str] = None


@app.get("/api/tasks")
def get_tasks(
    project: Optional[str] = None,
    done: Optional[bool] = None,
    owner: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Task)
    if owner:
        query = query.filter(Task.owner == owner)
    if project:
        query = query.filter(Task.project == project)
    if done is not None:
        query = query.filter(Task.done == done)
    return query.order_by(Task.priority, Task.created_at).all()


@app.post("/api/tasks")
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    db_task = Task(**task.dict())
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
    if update_data.get("done"):
        update_data["completed_at"] = datetime.utcnow()
    elif "done" in update_data and not update_data["done"]:
        update_data["completed_at"] = None
    for key, value in update_data.items():
        setattr(db_task, key, value)
    db.commit()
    db.refresh(db_task)
    return db_task


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(db_task)
    db.commit()
    return {"ok": True}


@app.get("/api/projects")
def get_projects(owner: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Task.project, Task.done)
    if owner:
        query = query.filter(Task.owner == owner)
    counts = {}
    for row in query.all():
        p = row[0]
        if p not in counts:
            counts[p] = {"total": 0, "pending": 0}
        counts[p]["total"] += 1
        if not row[1]:
            counts[p]["pending"] += 1
    return [{"name": p, "total": v["total"], "pending": v["pending"]} for p, v in counts.items()]


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/{full_path:path}")
def catch_all(full_path: str):
    return FileResponse("static/index.html")
