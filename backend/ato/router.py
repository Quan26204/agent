
from uuid import uuid4

import requests

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from .models import ATOPlan, ATOJob
from .schemas import PlanRequest
from .planner import create_plan
from .execution import execute_plan


router = APIRouter(
    prefix="/orchestrator",
    tags=["Orchestrator"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def serialize_plan(plan: ATOPlan):
    return {
        "id": plan.id,
        "conversation_id": plan.conversation_id,
        "user_request": plan.user_request,
        "title": plan.title,
        "summary": plan.summary,
        "status": plan.status,
        "clarification_questions": plan.clarification_questions or [],
        "created_at": (
            plan.created_at.isoformat()
            if plan.created_at else None
        ),
        "jobs": [
            {
                "id": job.id,
                "job_key": job.job_key,
                "job_type": job.job_type,
                "target_agent": job.target_agent,
                "description": job.description,
                "payload": job.payload or {},
                "schedule": job.schedule or {},
                "depends_on": job.depends_on or [],
                "status": job.status,
                "output": job.output,
                "error": job.error,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "progress": {
                    "current": job.progress_current or 0,
                    "total": job.progress_total or 0,
                    "stage": job.progress_stage,
                    "percent": round((job.progress_current or 0) * 100 / job.progress_total) if job.progress_total else 0,
                },
            }
            for job in plan.jobs
        ],
    }


# =====================================================
# 1. CREATE PLAN
# =====================================================

@router.post("/plans")
def draft_plan(
    body: PlanRequest,
    db: Session = Depends(get_db)
):
    if body.conversation_id is not None:
        from backend.models import Conversation

        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == body.conversation_id
            )
            .first()
        )

        if conversation is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )

    try:
        proposal = create_plan(body.request)

        plan = ATOPlan(
            id=str(uuid4()),
            conversation_id=body.conversation_id,
            user_request=body.request,
            title=proposal.title,
            summary=proposal.summary,
            status=(
                "needs_clarification"
                if proposal.needs_clarification
                else "pending_approval"
            ),
            clarification_questions=proposal.clarification_questions,
        )

        db.add(plan)

        key_to_id = {
            job.job_key: str(uuid4())
            for job in proposal.jobs
        }

        for item in proposal.jobs:
            db.add(
                ATOJob(
                    id=key_to_id[item.job_key],
                    plan_id=plan.id,
                    job_key=item.job_key,
                    job_type=item.job_type,
                    target_agent=item.target_agent,
                    description=item.description,
                    payload=item.payload,
                    schedule=item.schedule,
                    depends_on=[
                        key_to_id[key]
                        for key in item.depends_on
                    ],
                    status="awaiting_approval",
                )
            )

        db.commit()
        db.refresh(plan)

        return serialize_plan(plan)

    except requests.RequestException as exc:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail=f"Ollama request failed: {exc}"
        ) from exc

    except Exception as exc:
        db.rollback()

        if isinstance(exc, HTTPException):
            raise

        raise HTTPException(
            status_code=422,
            detail=str(exc)
        ) from exc


# =====================================================
# 2. GET ALL PLANS
# =====================================================

@router.get("/plans")
def list_plans(
    status: str | None = Query(
        default=None,
        description="Filter by plan status"
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100
    ),
    offset: int = Query(
        default=0,
        ge=0
    ),
    db: Session = Depends(get_db)
):
    query = db.query(ATOPlan)

    if status:
        query = query.filter(
            ATOPlan.status == status
        )

    total = query.count()

    plans = (
        query
        .order_by(ATOPlan.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            serialize_plan(plan)
            for plan in plans
        ],
    }


# =====================================================
# 3. GET PENDING PLANS
# =====================================================

@router.get("/plans/pending")
def get_pending_plans(
    limit: int = Query(
        default=20,
        ge=1,
        le=100
    ),
    offset: int = Query(
        default=0,
        ge=0
    ),
    db: Session = Depends(get_db)
):
    query = db.query(ATOPlan).filter(
        ATOPlan.status == "pending_approval"
    )

    total = query.count()

    plans = (
        query
        .order_by(ATOPlan.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            serialize_plan(plan)
            for plan in plans
        ],
    }


# =====================================================
# 4. GET PLAN BY ID
# =====================================================

@router.get("/plans/{plan_id}")
def get_plan(
    plan_id: str,
    db: Session = Depends(get_db)
):
    plan = (
        db.query(ATOPlan)
        .filter(ATOPlan.id == plan_id)
        .first()
    )

    if plan is None:
        raise HTTPException(
            status_code=404,
            detail="Plan not found"
        )

    return serialize_plan(plan)


# =====================================================
# 5. APPROVE PLAN
# =====================================================

@router.post("/plans/{plan_id}/approve")
def approve_plan(
    plan_id: str,
    db: Session = Depends(get_db)
):
    plan = (
        db.query(ATOPlan)
        .filter(ATOPlan.id == plan_id)
        .first()
    )

    if plan is None:
        raise HTTPException(
            status_code=404,
            detail="Plan not found"
        )

    if plan.status != "pending_approval":
        raise HTTPException(
            status_code=409,
            detail=(
                f"Plan cannot be approved "
                f"from state {plan.status}"
            )
        )

    plan.status = "approved"

    for job in plan.jobs:
        job.status = "queued"

    db.commit()
    db.refresh(plan)

    # Execution engine will be connected later.
    return serialize_plan(plan)


# =====================================================
# 6. EXECUTE APPROVED PLAN
# =====================================================

def _run_plan_in_background(plan_id: str):
    """Run an approved plan using a worker-owned database session."""
    db = SessionLocal()
    try:
        execute_plan(db, plan_id)
    except Exception as exc:
        db.rollback()
        plan = db.query(ATOPlan).filter(ATOPlan.id == plan_id).first()
        if plan is not None:
            plan.status = "failed"
            for job in plan.jobs:
                if job.status in ("queued", "running"):
                    job.status = "failed"
                    job.error = f"Background execution failed: {str(exc)[:3500]}"
                    job.progress_stage = "failed"
            db.commit()
    finally:
        db.close()


@router.post("/plans/{plan_id}/execute", status_code=202)
def run_approved_plan(
    plan_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    plan = db.query(ATOPlan).filter(ATOPlan.id == plan_id).first()
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    if plan.status != "approved":
        raise HTTPException(
            status_code=409,
            detail=f"Plan must be approved before execution (current: {plan.status}).",
        )
    if not plan.jobs:
        raise HTTPException(status_code=409, detail="Plan has no jobs to execute.")

    # Claim the plan before scheduling so repeated execute requests cannot enqueue it twice.
    plan.status = "queued"
    for job in plan.jobs:
        if job.status not in ("completed", "failed", "cancelled"):
            job.status = "queued"
            job.progress_current = 0
            job.progress_total = 0
            job.progress_stage = "queued"
    db.commit()
    db.refresh(plan)
    background_tasks.add_task(_run_plan_in_background, plan_id)

    result = serialize_plan(plan)
    result["message"] = "Execution accepted. Poll GET /orchestrator/plans/{plan_id} for progress."
    return result


@router.get("/plans/{plan_id}/progress")
def get_plan_progress(plan_id: str, db: Session = Depends(get_db)):
    plan = db.query(ATOPlan).filter(ATOPlan.id == plan_id).first()
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    jobs = []
    for job in plan.jobs:
        jobs.append({
            "job_id": job.id,
            "job_key": job.job_key,
            "status": job.status,
            "progress": {
                "current": job.progress_current or 0,
                "total": job.progress_total or 0,
                "stage": job.progress_stage,
                "percent": round((job.progress_current or 0) * 100 / job.progress_total) if job.progress_total else (100 if job.status == "completed" else 0),
            },
            "error": job.error,
        })
    return {"plan_id": plan.id, "status": plan.status, "jobs": jobs}


# =====================================================
# 7. REJECT PLAN
# =====================================================

@router.post("/plans/{plan_id}/reject")
def reject_plan(
    plan_id: str,
    db: Session = Depends(get_db)
):
    plan = (
        db.query(ATOPlan)
        .filter(ATOPlan.id == plan_id)
        .first()
    )

    if plan is None:
        raise HTTPException(
            status_code=404,
            detail="Plan not found"
        )

    if plan.status != "pending_approval":
        raise HTTPException(
            status_code=409,
            detail=(
                f"Plan cannot be rejected "
                f"from state {plan.status}"
            )
        )

    plan.status = "rejected"

    for job in plan.jobs:
        job.status = "cancelled"

    db.commit()
    db.refresh(plan)

    return serialize_plan(plan)
