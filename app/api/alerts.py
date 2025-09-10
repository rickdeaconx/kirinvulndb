from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from app.db.database import get_db
from app.models.alert import Alert, AlertTypeEnum, AlertPriorityEnum, AlertStatusEnum
from app.schemas.alert import AlertResponse, AlertCreate, AlertUpdate, AlertList

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=AlertList)
async def get_alerts(
    status: Optional[AlertStatusEnum] = Query(None, description="Filter by status"),
    priority: Optional[AlertPriorityEnum] = Query(None, description="Filter by priority"), 
    alert_type: Optional[AlertTypeEnum] = Query(None, description="Filter by alert type"),
    hours: int = Query(24, description="Hours to look back", ge=1, le=168),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get alerts with optional filtering"""
    
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    query = db.query(Alert).filter(Alert.created_at >= cutoff_time)
    
    # Apply filters
    if status:
        query = query.filter(Alert.status == status)
    
    if priority:
        query = query.filter(Alert.priority == priority)
    
    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)
    
    query = query.order_by(Alert.created_at.desc())
    
    total = query.count()
    alerts = query.offset(offset).limit(limit).all()
    
    return AlertList(
        alerts=[alert.to_dict() for alert in alerts],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/critical", response_model=AlertList)
async def get_critical_alerts(
    pending_only: bool = Query(True, description="Only show pending alerts"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get critical priority alerts"""
    
    query = db.query(Alert).filter(Alert.priority == AlertPriorityEnum.CRITICAL)
    
    if pending_only:
        query = query.filter(Alert.status == AlertStatusEnum.PENDING)
    
    query = query.order_by(Alert.created_at.desc())
    
    total = query.count()
    alerts = query.offset(offset).limit(limit).all()
    
    return AlertList(
        alerts=[alert.to_dict() for alert in alerts],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/stats")
async def get_alert_statistics(
    days: int = Query(7, description="Days to analyze", ge=1, le=30),
    db: Session = Depends(get_db)
):
    """Get alert statistics and metrics"""
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Total counts
    total_alerts = db.query(Alert).filter(Alert.created_at >= cutoff_date).count()
    
    # Priority breakdown
    priority_counts = {}
    for priority in AlertPriorityEnum:
        count = db.query(Alert).filter(
            Alert.priority == priority,
            Alert.created_at >= cutoff_date
        ).count()
        priority_counts[priority.value] = count
    
    # Status breakdown
    status_counts = {}
    for status in AlertStatusEnum:
        count = db.query(Alert).filter(
            Alert.status == status,
            Alert.created_at >= cutoff_date
        ).count()
        status_counts[status.value] = count
    
    # Type breakdown
    type_counts = {}
    for alert_type in AlertTypeEnum:
        count = db.query(Alert).filter(
            Alert.alert_type == alert_type,
            Alert.created_at >= cutoff_date
        ).count()
        type_counts[alert_type.value] = count
    
    return {
        "period_days": days,
        "total_alerts": total_alerts,
        "priority_distribution": priority_counts,
        "status_distribution": status_counts,
        "type_distribution": type_counts,
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert_by_id(
    alert_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific alert"""
    
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return AlertResponse(**alert.to_dict())


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    db: Session = Depends(get_db)
):
    """Mark an alert as acknowledged"""
    
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.mark_acknowledged()
    db.commit()
    
    logger.info(f"Alert {alert_id} acknowledged")
    return {"message": "Alert acknowledged successfully"}


@router.post("/{alert_id}/resolve") 
async def resolve_alert(
    alert_id: str,
    db: Session = Depends(get_db)
):
    """Mark an alert as resolved"""
    
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.status = AlertStatusEnum.RESOLVED
    db.commit()
    
    logger.info(f"Alert {alert_id} resolved")
    return {"message": "Alert resolved successfully"}


@router.post("/", response_model=AlertResponse)
async def create_alert(
    alert_data: AlertCreate,
    db: Session = Depends(get_db)
):
    """Create a new alert"""
    
    alert = Alert(**alert_data.dict())
    db.add(alert)
    db.commit()
    db.refresh(alert)
    
    logger.info(f"Created alert: {alert.id}")
    return AlertResponse(**alert.to_dict())