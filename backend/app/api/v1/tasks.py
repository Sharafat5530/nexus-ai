from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.tenant import User
from app.models.workflow import Task, TaskStatus
from app.models.audit import AuditEvent, AuditEventType
from app.schemas.workflow import TaskCreate, TaskRead
from app.core.security import get_current_user

router = APIRouter(prefix="/tasks", tags=["Autonomous Tasks"])

@router.get("", response_model=List[TaskRead])
def list_tasks(
    status_filter: Optional[TaskStatus] = Query(None, alias="status"),
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists all tasks strictly scoped to the authenticated tenant."""
    query = db.query(Task).filter(Task.organization_id == current_user.organization_id)
    if status_filter:
        query = query.filter(Task.status == status_filter)
    
    return query.order_by(Task.created_at.desc()).offset(offset).limit(limit).all()

@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creates a new autonomous task for agent execution."""
    new_task = Task(
        organization_id=current_user.organization_id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        workflow_type=payload.workflow_type,
        customer_id=payload.customer_id,
        status=TaskStatus.CREATED,
        meta=payload.meta or {}
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    # Record audit event
    audit = AuditEvent(
        organization_id=current_user.organization_id,
        event_type=AuditEventType.ACTION_PROPOSED,
        actor_id=current_user.id,
        target_id=new_task.id,
        summary=f"Task '{new_task.title}' created by {current_user.full_name}",
        details={"priority": new_task.priority, "workflow_type": new_task.workflow_type}
    )
    db.add(audit)
    db.commit()

    return new_task

@router.get("/{task_id}", response_model=TaskRead)
def get_task_details(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves full task execution graph with action proposals and proof of outcome."""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.organization_id == current_user.organization_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found or access unauthorized")
    return task
