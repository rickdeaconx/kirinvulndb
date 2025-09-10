from typing import Dict, List, Any
from sqlalchemy.orm import Query


def paginate(query: Query, page: int = 1, per_page: int = 50) -> Dict[str, Any]:
    """
    Paginate a SQLAlchemy query
    
    Args:
        query: SQLAlchemy query object
        page: Page number (1-based)
        per_page: Items per page
        
    Returns:
        Dictionary with pagination info and items
    """
    # Ensure page is at least 1
    page = max(1, page)
    
    # Calculate offset
    offset = (page - 1) * per_page
    
    # Get total count
    total = query.count()
    
    # Get items for current page
    items = query.offset(offset).limit(per_page).all()
    
    # Calculate pagination metadata
    total_pages = (total + per_page - 1) // per_page  # Ceiling division
    has_prev = page > 1
    has_next = page < total_pages
    prev_page = page - 1 if has_prev else None
    next_page = page + 1 if has_next else None
    
    return {
        "items": items,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_prev": has_prev,
            "has_next": has_next,
            "prev_page": prev_page,
            "next_page": next_page
        }
    }


def paginate_list(items: List[Any], page: int = 1, per_page: int = 50) -> Dict[str, Any]:
    """
    Paginate a list of items
    
    Args:
        items: List of items to paginate
        page: Page number (1-based)
        per_page: Items per page
        
    Returns:
        Dictionary with pagination info and items
    """
    # Ensure page is at least 1
    page = max(1, page)
    
    # Calculate bounds
    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    
    # Get items for current page
    page_items = items[start:end]
    
    # Calculate pagination metadata
    total_pages = (total + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages
    prev_page = page - 1 if has_prev else None
    next_page = page + 1 if has_next else None
    
    return {
        "items": page_items,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_prev": has_prev,
            "has_next": has_next,
            "prev_page": prev_page,
            "next_page": next_page
        }
    }