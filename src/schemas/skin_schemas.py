from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class SkinBase(BaseModel):
    market_hash_name: str
    weapon: Optional[str] = None
    pattern: Optional[str] = None
    rarity: Optional[str] = None
    exterior: Optional[str] = None
    float_min: Optional[float] = None
    float_max: Optional[float] = None
    image_url: Optional[str] = None
    is_stattrak: bool = False
    is_souvenir: bool = False

class SkinCreate(SkinBase):
    pass

class SkinResponse(SkinBase):
    id: int
    steam_app_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SkinSearchResponse(BaseModel):
    id: int
    market_hash_name: str
    weapon: Optional[str] = None
    pattern: Optional[str] = None
    rarity: Optional[str] = None
    exterior: Optional[str] = None
    
    class Config:
        from_attributes = True

class PriceBase(BaseModel):
    source: str
    price_median: Optional[float] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    volume: Optional[int] = None
    currency: str = "BRL"

class PriceCreate(PriceBase):
    skin_id: int

class PriceResponse(PriceBase):
    id: int
    skin_id: int
    collected_at: datetime
    
    class Config:
        from_attributes = True

class PriceHistoryResponse(BaseModel):
    skin_id: int
    market_hash_name: str
    prices: List[PriceResponse]
    
    class Config:
        from_attributes = True

class CurrentPriceResponse(BaseModel):
    skin_id: int
    price_median: Optional[float] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    volume: Optional[int] = None
    currency: str
    source: str
    collected_at: datetime

class AlertBase(BaseModel):
    alert_type: str
    threshold_value: float
    is_active: bool = True

class AlertCreate(AlertBase):
    skin_id: int
    user_id: int

class AlertResponse(AlertBase):
    id: int
    skin_id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: str
    username: Optional[str] = None
    is_active: bool = True
    is_premium: bool = False

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class StatsSummaryResponse(BaseModel):
    total_skins: int
    total_prices: int
    prices_today: int
    last_updated: str

class SearchResponse(BaseModel):
    query: str
    results: List[SkinSearchResponse]
    total: int
    limit: int 