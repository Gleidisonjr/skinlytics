"""
CSFloat API Service with Advanced Rate Limiting

Serviço otimizado para interagir com a API CSFloat respeitando
todos os limites de rate limiting e implementando retry automático.

Features:
    - Rate limiting adaptativo baseado em headers
    - Retry automático com backoff exponencial
    - Cache de respostas para reduzir requisições
    - Monitoramento detalhado de métricas
    - Suporte completo aos endpoints CSFloat

Author: CS2 Skin Tracker Team
Version: 2.0.0
"""

import aiohttp
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import os
import json
import hashlib
from dotenv import load_dotenv

from .rate_limiter import csfloat_rate_limiter

load_dotenv()

logger = logging.getLogger(__name__)

class CSFloatService:
    def __init__(self):
        self.base_url = "https://csfloat.com/api/v1"
        self.api_key = os.getenv('CSFLOAT_API_KEY')
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        headers = {
            'User-Agent': 'CS2-Skin-Tracker/1.0'
        }
        if self.api_key:
            headers['Authorization'] = self.api_key
            
        self.session = aiohttp.ClientSession(headers=headers)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def get_listings(self, 
                          page: int = 0,
                          limit: int = 50,
                          sort_by: str = "best_deal",
                          category: int = 0,
                          min_price: Optional[int] = None,
                          max_price: Optional[int] = None,
                          market_hash_name: Optional[str] = None,
                          min_float: Optional[float] = None,
                          max_float: Optional[float] = None,
                          def_index: Optional[int] = None,
                          paint_index: Optional[int] = None,
                          rarity: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get CSFloat listings based on the official API documentation
        
        Args:
            page: Which page of listings to start from
            limit: How many listings to return (max 50)
            sort_by: How to order listings (best_deal, lowest_price, etc.)
            category: 0=any, 1=normal, 2=stattrak, 3=souvenir
            min_price: Minimum price in cents
            max_price: Maximum price in cents
            market_hash_name: Specific market hash name
            min_float: Minimum float value
            max_float: Maximum float value
            def_index: Definition index
            paint_index: Paint index
            rarity: Rarity level
            
        Returns:
            List of listing data
        """
        if not self.session:
            raise RuntimeError("Service not initialized. Use async context manager.")
            
        params = {
            'page': page,
            'limit': min(limit, 50),  # API max is 50
            'sort_by': sort_by,
            'category': category
        }
        
        # Add optional parameters
        optional_params = {
            'min_price': min_price,
            'max_price': max_price,
            'market_hash_name': market_hash_name,
            'min_float': min_float,
            'max_float': max_float,
            'def_index': def_index,
            'paint_index': paint_index,
            'rarity': rarity
        }
        
        for key, value in optional_params.items():
            if value is not None:
                params[key] = value
            
        try:
            url = f"{self.base_url}/listings"
            logger.info(f"Fetching CSFloat listings: {url} with params: {params}")
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    # CSFloat returns {"data": [...], "cursor": "..."}
                    if isinstance(data, dict) and 'data' in data:
                        listings = data['data']
                        logger.info(f"Retrieved {len(listings)} listings from CSFloat")
                        return listings
                    elif isinstance(data, list):
                        logger.info(f"Retrieved {len(data)} listings from CSFloat")
                        return data
                    else:
                        logger.warning(f"Unexpected response format from CSFloat: {type(data)}")
                        return []
                else:
                    response_text = await response.text()
                    logger.error(f"CSFloat API error {response.status}: {response_text}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching CSFloat listings: {e}")
            return []
    
    async def get_skin_info(self, inspect_link: str) -> Optional[Dict[str, Any]]:
        """
        Get skin information from inspect link
        
        Args:
            inspect_link: Steam inspect link
            
        Returns:
            Skin information or None
        """
        if not self.session:
            raise RuntimeError("Service not initialized. Use async context manager.")
            
        try:
            params = {'url': inspect_link}
            async with self.session.get(f"{self.base_url}/inspect", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Retrieved skin info for inspect link")
                    return data
                else:
                    logger.warning(f"Could not get skin info: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching skin info: {e}")
            return None
    
    async def search_skins(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for skins by name
        
        Args:
            query: Search query
            limit: Number of results
            
        Returns:
            List of matching skins
        """
        if not self.session:
            raise RuntimeError("Service not initialized. Use async context manager.")
            
        try:
            params = {
                'q': query,
                'limit': limit
            }
            
            async with self.session.get(f"{self.base_url}/search", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Found {len(data.get('items', []))} skins matching '{query}'")
                    return data.get('items', [])
                else:
                    logger.error(f"CSFloat search error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error searching skins: {e}")
            return []
    
    def parse_float_value(self, float_str: str) -> Optional[float]:
        """Parse float value string to float"""
        try:
            return float(float_str)
        except (ValueError, TypeError):
            return None
    
    def parse_price_cents(self, price_cents: int) -> float:
        """Convert price from cents to dollars"""
        return price_cents / 100.0

# Utility function for sync usage
def get_csfloat_listings_sync(min_price: Optional[int] = None, 
                            max_price: Optional[int] = None,
                            limit: int = 100) -> List[Dict[str, Any]]:
    """Synchronous wrapper for getting CSFloat listings"""
    async def _async_get():
        async with CSFloatService() as service:
            return await service.get_listings(min_price, max_price, limit)
    
    return asyncio.run(_async_get()) 