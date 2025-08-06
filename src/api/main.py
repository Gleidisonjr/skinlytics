from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from src.models.database import get_session, Skin, Price
from src.services.csfloat_service import CSFloatService
from src.schemas.skin_schemas import SkinResponse, PriceResponse, SkinSearchResponse
from src.api.endpoints import router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CS2 Skin Tracker API",
    description="API para rastreamento de preços de skins do CS2 via CSFloat",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "CS2 Skin Tracker API", "status": "running"}

@app.get("/skins", response_model=List[SkinResponse])
async def get_skins(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    weapon: Optional[str] = None,
    rarity: Optional[str] = None,
    db: Session = Depends(get_session)
):
    """Get list of skins with optional filters"""
    query = db.query(Skin)
    
    if weapon:
        query = query.filter(Skin.weapon.ilike(f"%{weapon}%"))
    if rarity:
        query = query.filter(Skin.rarity.ilike(f"%{rarity}%"))
    
    skins = query.offset(skip).limit(limit).all()
    return skins

@app.get("/skins/{skin_id}", response_model=SkinResponse)
async def get_skin(skin_id: int, db: Session = Depends(get_session)):
    """Get specific skin by ID"""
    skin = db.query(Skin).filter(Skin.id == skin_id).first()
    if not skin:
        raise HTTPException(status_code=404, detail="Skin not found")
    return skin

@app.get("/skins/search/{query}", response_model=List[SkinSearchResponse])
async def search_skins(
    query: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_session)
):
    """Search skins by name"""
    skins = db.query(Skin).filter(
        Skin.market_hash_name.ilike(f"%{query}%")
    ).limit(limit).all()
    return skins

@app.get("/skins/{skin_id}/prices", response_model=List[PriceResponse])
async def get_skin_prices(
    skin_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_session)
):
    """Get price history for a skin"""
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    prices = db.query(Price).filter(
        Price.skin_id == skin_id,
        Price.collected_at >= cutoff_date
    ).order_by(Price.collected_at.desc()).all()
    
    if not prices:
        raise HTTPException(status_code=404, detail="No price data found")
    
    return prices

@app.get("/skins/{skin_id}/current-price")
async def get_current_price(skin_id: int, db: Session = Depends(get_session)):
    """Get current price for a skin (latest from database)"""
    latest_price = db.query(Price).filter(
        Price.skin_id == skin_id
    ).order_by(Price.collected_at.desc()).first()
    
    if not latest_price:
        raise HTTPException(status_code=404, detail="No price data found")
    
    return {
        "skin_id": skin_id,
        "price_median": latest_price.price_median,
        "price_min": latest_price.price_min,
        "price_max": latest_price.price_max,
        "volume": latest_price.volume,
        "currency": latest_price.currency,
        "source": latest_price.source,
        "collected_at": latest_price.collected_at
    }

@app.post("/skins/{skin_id}/refresh-price")
async def refresh_skin_price(skin_id: int, db: Session = Depends(get_session)):
    """Manually refresh price for a skin from Steam Market"""
    skin = db.query(Skin).filter(Skin.id == skin_id).first()
    if not skin:
        raise HTTPException(status_code=404, detail="Skin not found")
    
    try:
        # Get current price from Steam
        price_data = steam_service.get_skin_price(skin.market_hash_name)
        
        if not price_data:
            raise HTTPException(status_code=404, detail="Could not fetch price from Steam")
        
        # Save to database
        new_price = Price(
            skin_id=skin_id,
            source=price_data["source"],
            price_median=price_data["price_median"],
            price_min=price_data["price_min"],
            price_max=price_data["price_max"],
            volume=price_data["volume"],
            currency=price_data["currency"],
            collected_at=price_data["collected_at"]
        )
        
        db.add(new_price)
        db.commit()
        db.refresh(new_price)
        
        logger.info(f"Refreshed price for skin {skin_id}: {price_data['price_median']}")
        
        return {
            "message": "Price refreshed successfully",
            "price_data": price_data
        }
        
    except Exception as e:
        logger.error(f"Error refreshing price for skin {skin_id}: {e}")
        raise HTTPException(status_code=500, detail="Error refreshing price")

@app.get("/stats/summary")
async def get_stats_summary(db: Session = Depends(get_session)):
    """Get summary statistics"""
    total_skins = db.query(Skin).count()
    total_prices = db.query(Price).count()
    
    # Get latest price count
    from datetime import datetime, timedelta
    today = datetime.utcnow().date()
    today_prices = db.query(Price).filter(
        Price.collected_at >= today
    ).count()
    
    return {
        "total_skins": total_skins,
        "total_prices": total_prices,
        "prices_today": today_prices,
        "last_updated": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 