from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.db.database import get_db
from app.models.tool import AITool
from app.schemas.tool import AIToolResponse, AIToolCreate, AIToolUpdate, AIToolList

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=AIToolList)
async def get_all_tools(
    active_only: bool = Query(True, description="Only return actively monitored tools"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get list of all AI coding tools"""
    
    query = db.query(AITool)
    
    if active_only:
        query = query.filter(AITool.is_actively_monitored == True)
    
    query = query.order_by(AITool.name)
    
    total = query.count()
    tools = query.offset(offset).limit(limit).all()
    
    return AIToolList(
        tools=[tool.to_dict() for tool in tools],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/{tool_name}", response_model=AIToolResponse)
async def get_tool_by_name(
    tool_name: str,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific AI tool"""
    
    tool = db.query(AITool).filter(AITool.name == tool_name).first()
    
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    
    return AIToolResponse(**tool.to_dict())


@router.get("/{tool_name}/vulnerabilities")
async def get_tool_vulnerabilities(
    tool_name: str,
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get vulnerabilities for a specific tool"""
    
    tool = db.query(AITool).filter(AITool.name == tool_name).first()
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    
    # Get vulnerabilities with pagination
    vulnerabilities = tool.vulnerabilities[offset:offset + limit]
    
    return {
        "tool": tool_name,
        "vulnerabilities": [vuln.to_dict() for vuln in vulnerabilities],
        "total": len(tool.vulnerabilities),
        "limit": limit,
        "offset": offset
    }


@router.post("/", response_model=AIToolResponse)
async def create_tool(
    tool_data: AIToolCreate,
    db: Session = Depends(get_db)
):
    """Create a new AI tool entry"""
    
    # Check if tool already exists
    existing_tool = db.query(AITool).filter(AITool.name == tool_data.name).first()
    if existing_tool:
        raise HTTPException(status_code=400, detail="Tool with this name already exists")
    
    tool = AITool(**tool_data.dict())
    db.add(tool)
    db.commit()
    db.refresh(tool)
    
    logger.info(f"Created new tool: {tool.name}")
    return AIToolResponse(**tool.to_dict())


@router.put("/{tool_name}", response_model=AIToolResponse)
async def update_tool(
    tool_name: str,
    tool_data: AIToolUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing AI tool"""
    
    tool = db.query(AITool).filter(AITool.name == tool_name).first()
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    
    # Update fields
    for field, value in tool_data.dict(exclude_unset=True).items():
        setattr(tool, field, value)
    
    db.commit()
    db.refresh(tool)
    
    logger.info(f"Updated tool: {tool_name}")
    return AIToolResponse(**tool.to_dict())


@router.delete("/{tool_name}")
async def delete_tool(
    tool_name: str,
    db: Session = Depends(get_db)
):
    """Delete an AI tool (admin only)"""
    
    tool = db.query(AITool).filter(AITool.name == tool_name).first()
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    
    db.delete(tool)
    db.commit()
    
    logger.info(f"Deleted tool: {tool_name}")
    return {"message": f"Tool '{tool_name}' deleted successfully"}