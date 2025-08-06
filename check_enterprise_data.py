#!/usr/bin/env python3
"""
📊 Verificação de dados da arquitetura enterprise
"""
from src.models.database import get_session, Listing, Skin, StickerApplication
from datetime import datetime
import sys

def check_enterprise_data():
    session = get_session()
    
    try:
        # Contagens básicas
        listings_count = session.query(Listing).count()
        skins_count = session.query(Skin).count()
        stickers_count = session.query(StickerApplication).count()
        
        print("🚀 VERIFICAÇÃO ARQUITETURA ENTERPRISE")
        print("=" * 60)
        print(f"📦 LISTINGS: {listings_count:,}")
        print(f"🎨 SKINS ÚNICAS: {skins_count:,}")
        print(f"🏷️  STICKERS: {stickers_count:,}")
        
        if listings_count > 0:
            # Valor total
            total_value = sum([l.price for l in session.query(Listing).all() if l.price])
            print(f"💰 VALOR TOTAL: ${total_value:,.2f}")
            
            # Último listing
            recent = session.query(Listing).order_by(Listing.id.desc()).first()
            print(f"🕐 ÚLTIMO LISTING: {recent.id}")
            
            # Faixa de preços
            prices = [l.price for l in session.query(Listing).all() if l.price and l.price > 0]
            if prices:
                min_price = min(prices)
                max_price = max(prices)
                avg_price = sum(prices) / len(prices)
                print(f"💵 PREÇO MIN: ${min_price:.2f}")
                print(f"💵 PREÇO MAX: ${max_price:.2f}")
                print(f"💵 PREÇO MÉDIO: ${avg_price:.2f}")
            
            # Top 5 skins mais caras
            top_listings = session.query(Listing).join(Skin).order_by(Listing.price.desc()).limit(5).all()
            print("\n🏆 TOP 5 MAIS CAROS:")
            for i, listing in enumerate(top_listings, 1):
                skin_name = listing.skin.market_hash_name if listing.skin else "Unknown"
                print(f"  {i}. ${listing.price:.2f} - {skin_name[:50]}")
            
            # Vendedores únicos
            unique_sellers = session.query(Listing.seller_steam_id).distinct().count()
            print(f"\n👥 VENDEDORES ÚNICOS: {unique_sellers:,}")
            
        print("\n✅ VERIFICAÇÃO CONCLUÍDA!")
        
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")
        
    finally:
        session.close()

if __name__ == "__main__":
    check_enterprise_data()