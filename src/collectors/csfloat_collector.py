import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

from src.models.database import get_session, Skin, Listing, StickerApplication, create_tables
from src.services.csfloat_service import CSFloatService

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('data/csfloat_collector.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class CSFloatCollector:
    def __init__(self):
        self.session = get_session()
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
    
    async def collect_listings(self, 
                             limit: int = 50, 
                             market_hash_name: str = None,
                             min_price: int = None,
                             max_price: int = None) -> int:
        """Collect listings from CSFloat API"""
        try:
            async with CSFloatService() as csfloat_service:
                logger.info(f"Collecting CSFloat listings (limit: {limit})")
                
                # Get listings from CSFloat
                listings = await csfloat_service.get_listings(
                    limit=limit,
                    market_hash_name=market_hash_name,
                    min_price=min_price,
                    max_price=max_price,
                    sort_by="most_recent"
                )
                
                collected_count = 0
                for listing_data in listings:
                    try:
                        collected_count += self._process_listing(listing_data)
                    except Exception as e:
                        logger.error(f"Error processing listing {listing_data.get('id', 'unknown')}: {e}")
                        continue
                
                self.session.commit()
                logger.info(f"Collected {collected_count} listings from CSFloat")
                return collected_count
                
        except Exception as e:
            logger.error(f"Error in CSFloat data collection: {e}")
            self.session.rollback()
            return 0
    
    def _process_listing(self, listing_data: Dict[str, Any]) -> int:
        """Process a single listing from CSFloat API"""
        try:
            item_data = listing_data.get('item', {})
            seller_data = listing_data.get('seller', {})
            
            market_hash_name = item_data.get('market_hash_name')
            if not market_hash_name:
                logger.warning("Listing without market_hash_name, skipping")
                return 0
            
            # Find or create skin
            skin = self.session.query(Skin).filter_by(
                market_hash_name=market_hash_name
            ).first()
            
            if not skin:
                # Create new skin from CSFloat data
                skin = Skin(
                    market_hash_name=market_hash_name,
                    item_name=item_data.get('item_name'),
                    wear_name=item_data.get('wear_name'),
                    def_index=item_data.get('def_index'),
                    paint_index=item_data.get('paint_index'),
                    rarity=item_data.get('rarity'),
                    quality=item_data.get('quality'),
                    collection=item_data.get('collection'),
                    description=item_data.get('description'),
                    icon_url=item_data.get('icon_url'),
                    is_stattrak=item_data.get('is_stattrak', False),
                    is_souvenir=item_data.get('is_souvenir', False)
                )
                self.session.add(skin)
                self.session.flush()  # Get the ID
            
            # Check if listing already exists
            listing_id = listing_data.get('id')
            existing_listing = self.session.query(Listing).filter_by(id=listing_id).first()
            
            if existing_listing:
                # Update existing listing
                existing_listing.state = listing_data.get('state')
                existing_listing.price = listing_data.get('price')
                existing_listing.seller_online = seller_data.get('online', False)
                existing_listing.watchers = listing_data.get('watchers', 0)
                existing_listing.collected_at = datetime.utcnow()
                logger.info(f"Updated existing listing {listing_id}")
                return 0
            else:
                # Create new listing
                listing = Listing(
                    id=listing_id,
                    skin_id=skin.id,
                    created_at_csfloat=datetime.fromisoformat(listing_data.get('created_at', '').replace('Z', '+00:00')),
                    type=listing_data.get('type'),
                    price=listing_data.get('price'),
                    state=listing_data.get('state'),
                    
                    # Item details
                    asset_id=item_data.get('asset_id'),
                    paint_seed=item_data.get('paint_seed'),
                    float_value=item_data.get('float_value'),
                    tradable=item_data.get('tradable'),
                    inspect_link=item_data.get('inspect_link'),
                    has_screenshot=item_data.get('has_screenshot', False),
                    
                    # Seller info
                    seller_steam_id=seller_data.get('steam_id'),
                    seller_username=seller_data.get('username'),
                    seller_avatar=seller_data.get('avatar'),
                    seller_online=seller_data.get('online', False),
                    
                    # Market data
                    min_offer_price=listing_data.get('min_offer_price'),
                    max_offer_discount=listing_data.get('max_offer_discount'),
                    watchers=listing_data.get('watchers', 0),
                    is_watchlisted=listing_data.get('is_watchlisted', False)
                )
                
                self.session.add(listing)
                self.session.flush()  # Get the ID
                
                # Process stickers
                stickers = item_data.get('stickers', [])
                for sticker_data in stickers:
                    sticker = StickerApplication(
                        listing_id=listing.id,
                        sticker_id=sticker_data.get('stickerId'),
                        slot=sticker_data.get('slot'),
                        wear=sticker_data.get('wear'),
                        icon_url=sticker_data.get('icon_url'),
                        name=sticker_data.get('name'),
                        scm_price=sticker_data.get('scm', {}).get('price'),
                        scm_volume=sticker_data.get('scm', {}).get('volume')
                    )
                    self.session.add(sticker)
                
                price_usd = listing_data.get('price', 0) / 100
                logger.info(f"Added new listing: {market_hash_name} - ${price_usd:.2f}")
                return 1
                
        except Exception as e:
            logger.error(f"Error processing listing: {e}")
            return 0
    
    async def collect_specific_skins(self, market_hash_names: List[str]) -> Dict[str, int]:
        """Collect listings for specific skins"""
        results = {}
        
        for market_hash_name in market_hash_names:
            logger.info(f"Collecting listings for: {market_hash_name}")
            count = await self.collect_listings(
                limit=20,
                market_hash_name=market_hash_name
            )
            results[market_hash_name] = count
            
            # Small delay to be respectful to the API
            await asyncio.sleep(1)
        
        return results

def main():
    """Main function to run CSFloat data collection"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CSFloat Data Collector')
    parser.add_argument('--limit', type=int, default=50, help='Number of listings to collect')
    parser.add_argument('--market-hash-name', type=str, help='Specific skin to collect')
    parser.add_argument('--min-price', type=int, help='Minimum price in cents')
    parser.add_argument('--max-price', type=int, help='Maximum price in cents')
    parser.add_argument('--create-tables', action='store_true', help='Create database tables')
    parser.add_argument('--test-skins', action='store_true', help='Test with specific popular skins')
    
    args = parser.parse_args()
    
    if args.create_tables:
        create_tables()
        logger.info("Database tables created")
    
    async def run_collection():
        with CSFloatCollector() as collector:
            if args.test_skins:
                # Test with some popular skins
                test_skins = [
                    "AK-47 | Redline (Field-Tested)",
                    "AWP | Asiimov (Field-Tested)",
                    "M4A4 | Howl (Field-Tested)",
                    "Glock-18 | Fade (Factory New)",
                    "Desert Eagle | Blaze (Factory New)"
                ]
                results = await collector.collect_specific_skins(test_skins)
                print(f"Collection Results: {results}")
                total = sum(results.values())
                print(f"Total listings collected: {total}")
            else:
                count = await collector.collect_listings(
                    limit=args.limit,
                    market_hash_name=args.market_hash_name,
                    min_price=args.min_price,
                    max_price=args.max_price
                )
                print(f"Collected {count} listings")
    
    asyncio.run(run_collection())

if __name__ == "__main__":
    main()