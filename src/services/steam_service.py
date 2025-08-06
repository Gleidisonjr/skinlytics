import requests
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import time

logger = logging.getLogger(__name__)

class SteamMarketService:
    def __init__(self):
        self.base_url = "https://steamcommunity.com/market/priceoverview/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_skin_price(self, market_hash_name: str, currency: int = 7) -> Optional[Dict[str, Any]]:
        """
        Get skin price from Steam Market
        
        Args:
            market_hash_name: Steam market hash name
            currency: Currency code (7 = BRL, 1 = USD)
            
        Returns:
            Dict with price data or None if error
        """
        params = {
            "currency": currency,
            "appid": 730,  # CS2
            "market_hash_name": market_hash_name
        }
        
        try:
            logger.info(f"Fetching price for: {market_hash_name}")
            response = self.session.get(self.base_url, params=params, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"HTTP {response.status_code} for {market_hash_name}")
                return None
                
            data = response.json()
            
            if not data.get("success"):
                logger.warning(f"Steam API returned success=False for {market_hash_name}")
                return None
                
            # Parse price strings to float
            median_price = self._parse_price(data.get("median_price"))
            lowest_price = self._parse_price(data.get("lowest_price"))
            volume = self._parse_volume(data.get("volume"))
            
            return {
                "market_hash_name": market_hash_name,
                "price_median": median_price,
                "price_min": lowest_price,
                "price_max": median_price,  # Steam doesn't provide max
                "volume": volume,
                "currency": "BRL" if currency == 7 else "USD",
                "source": "steam",
                "collected_at": datetime.utcnow(),
                "raw_data": data
            }
            
        except requests.Timeout:
            logger.error(f"Timeout fetching {market_hash_name}")
            return None
        except requests.RequestException as e:
            logger.error(f"Request error for {market_hash_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for {market_hash_name}: {e}")
            return None
    
    def _parse_price(self, price_str: str) -> Optional[float]:
        """Parse Steam price string to float"""
        if not price_str:
            return None
            
        try:
            # Remove currency symbol and convert to float
            price_clean = price_str.replace('R$', '').replace('$', '').replace(',', '').strip()
            return float(price_clean)
        except (ValueError, AttributeError):
            logger.warning(f"Could not parse price: {price_str}")
            return None
    
    def _parse_volume(self, volume_str: str) -> Optional[int]:
        """Parse Steam volume string to integer"""
        if not volume_str:
            return None
            
        try:
            # Remove commas and convert to int
            volume_clean = volume_str.replace(',', '').strip()
            return int(volume_clean)
        except (ValueError, AttributeError):
            logger.warning(f"Could not parse volume: {volume_str}")
            return None
    
    def batch_get_prices(self, market_hash_names: list, delay: float = 1.5) -> list:
        """
        Get prices for multiple skins with rate limiting
        
        Args:
            market_hash_names: List of market hash names
            delay: Delay between requests in seconds
            
        Returns:
            List of price data dictionaries
        """
        results = []
        
        for i, market_hash_name in enumerate(market_hash_names):
            logger.info(f"Processing {i+1}/{len(market_hash_names)}: {market_hash_name}")
            
            price_data = self.get_skin_price(market_hash_name)
            if price_data:
                results.append(price_data)
            
            # Rate limiting
            if i < len(market_hash_names) - 1:  # Don't sleep after last request
                time.sleep(delay)
        
        logger.info(f"Completed batch request. Got {len(results)}/{len(market_hash_names)} prices")
        return results 