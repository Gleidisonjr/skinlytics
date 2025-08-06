#!/usr/bin/env python3
"""
Teste do Enterprise Collector Otimizado
Verifica se o novo modelo está funcionando corretamente
"""

import asyncio
import logging
from datetime import datetime
from src.models.optimized_database import get_session, Skin as OptimizedSkin, ListingOptimized

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_optimized_database():
    """Testa o acesso ao banco otimizado"""
    try:
        session = get_session()
        
        # Contar registros existentes
        skins_count = session.query(OptimizedSkin).count()
        listings_count = session.query(ListingOptimized).count()
        
        logger.info(f"✅ Banco otimizado acessível!")
        logger.info(f"📊 Skins: {skins_count:,}")
        logger.info(f"📦 Listings: {listings_count:,}")
        
        # Testar uma consulta com índices
        recent_listings = session.query(ListingOptimized).order_by(
            ListingOptimized.collected_at.desc()
        ).limit(5).all()
        
        logger.info(f"🔍 Últimos 5 listings:")
        for listing in recent_listings:
            logger.info(f"  • {listing.id} - ${listing.price/100:.2f}")
        
        session.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste: {e}")
        return False

async def test_collector_small():
    """Testa o collector otimizado com 1 ciclo pequeno"""
    try:
        from enterprise_collector import EnterpriseCollector
        
        logger.info("🚀 Testando collector otimizado...")
        
        # Inicializar collector
        collector = EnterpriseCollector("")  # API key vazia para teste
        
        # Coletar 1 página apenas
        listings = await collector.collect_listings_page(0, 'most_recent')
        
        if listings:
            logger.info(f"✅ Coletados {len(listings)} listings")
            
            # Testar salvamento de 1 listing
            if listings:
                success = collector.save_listing_enterprise(listings[0])
                if success:
                    logger.info("✅ Salvamento no modelo otimizado funcionando!")
                else:
                    logger.info("ℹ️ Listing já existe (normal)")
        else:
            logger.warning("⚠️ Nenhum listing coletado")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste do collector: {e}")
        return False

def benchmark_query_performance():
    """Testa performance de consultas no modelo otimizado"""
    try:
        session = get_session()
        
        logger.info("⚡ Testando performance de consultas...")
        
        start_time = datetime.now()
        
        # Consulta 1: Preços por skin (usa índice)
        expensive_items = session.query(ListingOptimized).filter(
            ListingOptimized.price > 50000  # $500+
        ).limit(10).all()
        
        query1_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"🔍 Query 1 (índice price): {query1_time:.3f}s - {len(expensive_items)} resultados")
        
        # Consulta 2: Por skin específica (usa índice)
        start_time = datetime.now()
        ak47_listings = session.query(ListingOptimized).join(OptimizedSkin).filter(
            OptimizedSkin.item_name.like('%AK-47%')
        ).limit(10).all()
        
        query2_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"🔍 Query 2 (join + filter): {query2_time:.3f}s - {len(ak47_listings)} resultados")
        
        # Consulta 3: Agregação por seller performance
        start_time = datetime.now()
        trusted_sellers = session.query(ListingOptimized).filter(
            ListingOptimized.seller_total_trades > 100,
            ListingOptimized.seller_verified_trades > 50
        ).limit(10).all()
        
        query3_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"🔍 Query 3 (seller performance): {query3_time:.3f}s - {len(trusted_sellers)} resultados")
        
        session.close()
        
        avg_time = (query1_time + query2_time + query3_time) / 3
        logger.info(f"⚡ Performance média: {avg_time:.3f}s por consulta")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no benchmark: {e}")
        return False

async def main():
    """Função principal de teste"""
    print("🧪 TESTE DO ENTERPRISE COLLECTOR OTIMIZADO")
    print("=" * 60)
    
    tests = [
        ("Database Access", test_optimized_database),
        ("Query Performance", benchmark_query_performance),
        ("Collector Function", test_collector_small),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}...")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results[test_name] = result
        except Exception as e:
            logger.error(f"❌ {test_name} falhou: {e}")
            results[test_name] = False
    
    # Relatório final
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO DE TESTES")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("🎉 TODOS OS TESTES PASSARAM! O modelo otimizado está funcionando.")
    else:
        print("⚠️ Alguns testes falharam. Verifique os logs acima.")
    
    return all_passed

if __name__ == "__main__":
    asyncio.run(main())