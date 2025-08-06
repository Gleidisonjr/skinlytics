import pandas as pd
import logging
from datetime import datetime
from typing import List, Dict, Any
import asyncio
import os
from dotenv import load_dotenv

from src.models.database import get_session, Skin, Price, create_tables
from src.services.steam_service import SteamMarketService
from src.services.csfloat_service import CSFloatService

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('data/collector.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class DataCollector:
    def __init__(self):
        self.steam_service = SteamMarketService()
        self.session = get_session()
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
    
    def populate_skins_from_csv(self, csv_path: str) -> int:
        """Populate skins table from CSV file"""
        try:
            df = pd.read_csv(csv_path)
            logger.info(f"Loading {len(df)} skins from {csv_path}")
            
            added_count = 0
            for _, row in df.iterrows():
                try:
                    # Check if skin already exists
                    existing_skin = self.session.query(Skin).filter_by(
                        market_hash_name=row['market_hash_name']
                    ).first()
                    
                    if existing_skin:
                        continue
                    
                    # Create new skin
                    skin = Skin(
                        market_hash_name=row['market_hash_name'],
                        weapon=row.get('arma'),
                        pattern=row.get('padrao'),
                        rarity=row.get('raridade'),
                        exterior=row.get('exterior')
                    )
                    
                    self.session.add(skin)
                    added_count += 1
                    
                except Exception as e:
                    logger.error(f"Error adding skin {row.get('market_hash_name', 'unknown')}: {e}")
                    continue
            
            self.session.commit()
            logger.info(f"Added {added_count} new skins to database")
            return added_count
            
        except Exception as e:
            logger.error(f"Error populating skins: {e}")
            self.session.rollback()
            return 0
    
    def collect_steam_prices(self, limit: int = None) -> int:
        """Collect prices from Steam Market for all skins"""
        try:
            # Get all skins
            query = self.session.query(Skin)
            if limit:
                query = query.limit(limit)
            
            skins = query.all()
            logger.info(f"Collecting Steam prices for {len(skins)} skins")
            
            collected_count = 0
            for i, skin in enumerate(skins):
                try:
                    logger.info(f"Processing {i+1}/{len(skins)}: {skin.market_hash_name}")
                    
                    # Get price from Steam
                    price_data = self.steam_service.get_skin_price(skin.market_hash_name)
                    
                    if price_data and price_data.get('price_median'):
                        # Save price to database
                        price = Price(
                            skin_id=skin.id,
                            source=price_data['source'],
                            price_median=price_data['price_median'],
                            price_min=price_data['price_min'],
                            price_max=price_data['price_max'],
                            volume=price_data['volume'],
                            currency=price_data['currency'],
                            collected_at=price_data['collected_at']
                        )
                        
                        self.session.add(price)
                        collected_count += 1
                        logger.info(f"Collected price: R$ {price_data['price_median']}")
                    else:
                        logger.warning(f"No price data for {skin.market_hash_name}")
                    
                    # Rate limiting
                    if i < len(skins) - 1:
                        import time
                        time.sleep(1.5)
                        
                except Exception as e:
                    logger.error(f"Error collecting price for {skin.market_hash_name}: {e}")
                    continue
            
            self.session.commit()
            logger.info(f"Collected {collected_count} prices from Steam")
            return collected_count
            
        except Exception as e:
            logger.error(f"Error in Steam price collection: {e}")
            self.session.rollback()
            return 0
    
    async def collect_csfloat_data(self, limit: int = 100) -> int:
        """Collect data from CSFloat API"""
        try:
            async with CSFloatService() as csfloat_service:
                logger.info(f"Collecting CSFloat data (limit: {limit})")
                
                # Get listings from CSFloat
                listings = await csfloat_service.get_listings(limit=limit)
                
                collected_count = 0
                for listing in listings:
                    try:
                        market_hash_name = listing.get('market_hash_name')
                        if not market_hash_name:
                            continue
                        
                        # Find or create skin
                        skin = self.session.query(Skin).filter_by(
                            market_hash_name=market_hash_name
                        ).first()
                        
                        if not skin:
                            # Create new skin from CSFloat data
                            skin = Skin(
                                market_hash_name=market_hash_name,
                                weapon=listing.get('weapon'),
                                pattern=listing.get('pattern'),
                                rarity=listing.get('rarity'),
                                exterior=listing.get('wear_name'),
                                float_min=csfloat_service.parse_float_value(listing.get('float_value')),
                                float_max=csfloat_service.parse_float_value(listing.get('float_value')),
                                is_stattrak=listing.get('is_stattrak', False)
                            )
                            self.session.add(skin)
                            self.session.flush()  # Get the ID
                        
                        # Save price data
                        price_cents = listing.get('price')
                        if price_cents:
                            price = Price(
                                skin_id=skin.id,
                                source='csfloat',
                                price_median=csfloat_service.parse_price_cents(price_cents),
                                price_min=csfloat_service.parse_price_cents(price_cents),
                                price_max=csfloat_service.parse_price_cents(price_cents),
                                currency='USD',
                                collected_at=datetime.utcnow()
                            )
                            
                            self.session.add(price)
                            collected_count += 1
                            
                    except Exception as e:
                        logger.error(f"Error processing CSFloat listing: {e}")
                        continue
                
                self.session.commit()
                logger.info(f"Collected {collected_count} CSFloat prices")
                return collected_count
                
        except Exception as e:
            logger.error(f"Error in CSFloat data collection: {e}")
            self.session.rollback()
            return 0
    
    def run_full_collection(self, csv_path: str = None, steam_limit: int = None, csfloat_limit: int = 100):
        """Run complete data collection pipeline"""
        logger.info("Starting full data collection pipeline")
        
        # Step 1: Populate skins from CSV if provided
        if csv_path:
            self.populate_skins_from_csv(csv_path)
        
        # Step 2: Collect Steam prices
        steam_count = self.collect_steam_prices(limit=steam_limit)
        
        # Step 3: Collect CSFloat data
        csfloat_count = asyncio.run(self.collect_csfloat_data(limit=csfloat_limit))
        
        logger.info(f"Collection complete! Steam: {steam_count}, CSFloat: {csfloat_count}")
        return {
            'steam_prices': steam_count,
            'csfloat_prices': csfloat_count
        }

def main():
    """Main function to run data collection"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CS2 Skin Data Collector')
    parser.add_argument('--csv', type=str, help='CSV file with skins to populate')
    parser.add_argument('--steam-limit', type=int, help='Limit for Steam price collection')
    parser.add_argument('--csfloat-limit', type=int, default=100, help='Limit for CSFloat data collection')
    parser.add_argument('--create-tables', action='store_true', help='Create database tables')
    
    args = parser.parse_args()
    
    if args.create_tables:
        create_tables()
        logger.info("Database tables created")
    
    with DataCollector() as collector:
        results = collector.run_full_collection(
            csv_path=args.csv,
            steam_limit=args.steam_limit,
            csfloat_limit=args.csfloat_limit
        )
        
        print(f"Collection Results: {results}")

if __name__ == "__main__":
    main() 