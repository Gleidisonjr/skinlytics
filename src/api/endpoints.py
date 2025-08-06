from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
import logging

from src.models.database import get_session, Skin, Listing, StickerApplication
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["market"])

@router.get("/stats/summary")
async def get_market_summary(db: Session = Depends(get_session)):
    """Get market summary statistics"""
    try:
        # Total listings
        total_listings = db.query(Listing).count()
        
        # Unique skins
        unique_skins = db.query(Skin).count()
        
        # Average price (convert cents to dollars)
        avg_price_cents = db.query(func.avg(Listing.price)).scalar() or 0
        avg_price = avg_price_cents / 100
        
        # Total market value
        total_value_cents = db.query(func.sum(Listing.price)).scalar() or 0
        market_cap = total_value_cents / 100
        
        # Recent activity (last 24h)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_listings = db.query(Listing).filter(
            Listing.collected_at >= yesterday
        ).count()
        
        return {
            "total_listings": total_listings,
            "unique_skins": unique_skins,
            "average_price": round(avg_price, 2),
            "market_cap": round(market_cap, 2),
            "recent_listings_24h": recent_listings,
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting market summary: {e}")
        raise HTTPException(status_code=500, detail="Error fetching market data")

@router.get("/listings")
async def get_listings(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    category: Optional[str] = None,
    sort_by: str = Query("price_desc", regex="^(price_asc|price_desc|float_asc|float_desc|recent)$"),
    db: Session = Depends(get_session)
):
    """Get market listings with filters and sorting"""
    try:
        query = db.query(Listing, Skin).join(Skin)
        
        # Search filter
        if search:
            query = query.filter(Skin.market_hash_name.ilike(f"%{search}%"))
        
        # Category filter
        if category:
            if category == "rifle":
                query = query.filter(
                    Skin.market_hash_name.ilike("%AK-47%") |
                    Skin.market_hash_name.ilike("%M4A%") |
                    Skin.market_hash_name.ilike("%AWP%") |
                    Skin.market_hash_name.ilike("%Galil%") |
                    Skin.market_hash_name.ilike("%FAMAS%")
                )
            elif category == "pistol":
                query = query.filter(
                    Skin.market_hash_name.ilike("%Glock%") |
                    Skin.market_hash_name.ilike("%USP%") |
                    Skin.market_hash_name.ilike("%P250%") |
                    Skin.market_hash_name.ilike("%Desert Eagle%") |
                    Skin.market_hash_name.ilike("%Dual Berettas%")
                )
            elif category == "knife":
                query = query.filter(
                    Skin.market_hash_name.ilike("%Knife%") |
                    Skin.market_hash_name.ilike("%Bayonet%") |
                    Skin.market_hash_name.ilike("%Karambit%")
                )
        
        # Sorting
        if sort_by == "price_asc":
            query = query.order_by(Listing.price.asc())
        elif sort_by == "price_desc":
            query = query.order_by(Listing.price.desc())
        elif sort_by == "float_asc":
            query = query.order_by(Listing.float_value.asc())
        elif sort_by == "float_desc":
            query = query.order_by(Listing.float_value.desc())
        else:  # recent
            query = query.order_by(Listing.collected_at.desc())
        
        # Pagination
        results = query.offset(offset).limit(limit).all()
        
        # Format response
        listings = []
        for listing, skin in results:
            listings.append({
                "id": listing.id,
                "skin_name": skin.market_hash_name,
                "price_usd": round(listing.price / 100, 2),
                "price_cents": listing.price,
                "float_value": listing.float_value,
                "seller_username": listing.seller_username,
                "seller_steam_id": listing.seller_steam_id,
                "state": listing.state,
                "created_at": listing.created_at_csfloat.isoformat() if listing.created_at_csfloat else None,
                "collected_at": listing.collected_at.isoformat(),
                "inspect_link": listing.inspect_link,
                "has_screenshot": listing.has_screenshot,
                "watchers": listing.watchers
            })
        
        return {
            "listings": listings,
            "total": len(listings),
            "offset": offset,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error getting listings: {e}")
        raise HTTPException(status_code=500, detail="Error fetching listings")

@router.get("/skins/trending")
async def get_trending_skins(
    limit: int = Query(10, ge=1, le=50),
    timeframe: str = Query("24h", regex="^(1h|6h|24h|7d)$"),
    db: Session = Depends(get_session)
):
    """Get trending skins based on listing activity"""
    try:
        # Calculate time threshold
        if timeframe == "1h":
            threshold = datetime.utcnow() - timedelta(hours=1)
        elif timeframe == "6h":
            threshold = datetime.utcnow() - timedelta(hours=6)
        elif timeframe == "24h":
            threshold = datetime.utcnow() - timedelta(days=1)
        else:  # 7d
            threshold = datetime.utcnow() - timedelta(days=7)
        
        # Get skins with most listings in timeframe
        trending = db.query(
            Skin.market_hash_name,
            Skin.item_name,
            func.count(Listing.id).label('listing_count'),
            func.avg(Listing.price).label('avg_price'),
            func.min(Listing.price).label('min_price'),
            func.max(Listing.price).label('max_price')
        ).join(Listing).filter(
            Listing.collected_at >= threshold
        ).group_by(
            Skin.id, Skin.market_hash_name, Skin.item_name
        ).order_by(
            desc('listing_count')
        ).limit(limit).all()
        
        results = []
        for item in trending:
            results.append({
                "market_hash_name": item.market_hash_name,
                "item_name": item.item_name,
                "listing_count": item.listing_count,
                "avg_price": round(item.avg_price / 100, 2),
                "min_price": round(item.min_price / 100, 2),
                "max_price": round(item.max_price / 100, 2),
                "timeframe": timeframe
            })
        
        return {
            "trending_skins": results,
            "timeframe": timeframe,
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting trending skins: {e}")
        raise HTTPException(status_code=500, detail="Error fetching trending data")

@router.get("/skins/{skin_name}/history")
async def get_skin_price_history(
    skin_name: str,
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_session)
):
    """Get price history for a specific skin"""
    try:
        # Find skin
        skin = db.query(Skin).filter(
            Skin.market_hash_name.ilike(f"%{skin_name}%")
        ).first()
        
        if not skin:
            raise HTTPException(status_code=404, detail="Skin not found")
        
        # Get price history
        threshold = datetime.utcnow() - timedelta(days=days)
        history = db.query(Listing).filter(
            Listing.skin_id == skin.id,
            Listing.collected_at >= threshold
        ).order_by(Listing.collected_at.asc()).all()
        
        price_points = []
        for listing in history:
            price_points.append({
                "timestamp": listing.collected_at.isoformat(),
                "price_usd": round(listing.price / 100, 2),
                "float_value": listing.float_value,
                "state": listing.state
            })
        
        return {
            "skin": {
                "market_hash_name": skin.market_hash_name,
                "item_name": skin.item_name,
                "wear_name": skin.wear_name
            },
            "price_history": price_points,
            "days": days,
            "total_points": len(price_points)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting price history: {e}")
        raise HTTPException(status_code=500, detail="Error fetching price history")