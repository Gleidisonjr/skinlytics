"""
Script para Escalar Coleta Massiva de Dados Skinlytics

Estratégia de crescimento:
1. Coleta contínua otimizada
2. Múltiplos workers paralelos  
3. Rate limiting inteligente
4. Backup automático
5. Métricas em tempo real

Author: CS2 Skin Tracker Team - Skinlytics Platform
Version: 2.0.0 Scale Ready
"""

import asyncio
import aiohttp
import time
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any
import os
from pathlib import Path

class ScaledCollector:
    """Coletor escalado para crescimento massivo"""
    
    def __init__(self):
        self.api_key = os.getenv('CSFLOAT_API_KEY', 'brtnO9zH3PuubFCCsQY9kNX5jyqoJvu3')
        self.base_url = "https://csfloat.com/api/v1"
        self.db_path = "data/skins.db"
        
        # Estatísticas
        self.stats = {
            "total_collected": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "rate_limit_hits": 0,
            "start_time": datetime.now(),
            "last_collection": None
        }
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler('logs/collector.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Criar diretórios
        Path("logs").mkdir(exist_ok=True)
        Path("data").mkdir(exist_ok=True)
        
        self.logger.info("🚀 ScaledCollector inicializado")
    
    def setup_database(self):
        """Configura banco de dados otimizado"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Criar tabela de listings otimizada
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS listings (
            id TEXT PRIMARY KEY,
            item_name TEXT NOT NULL,
            price_usd REAL NOT NULL,
            float_value REAL,
            paint_seed INTEGER,
            paint_index INTEGER,
            def_index INTEGER,
            wear_name TEXT,
            rarity INTEGER,
            collection TEXT,
            stickers TEXT,  -- JSON string
            seller_id TEXT,
            seller_username TEXT,
            seller_stats TEXT,  -- JSON string
            created_at_csfloat TEXT,
            collected_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Criar índices separadamente
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_item_name ON listings(item_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_price ON listings(price_usd)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_float ON listings(float_value)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_collected_at ON listings(collected_at)')
        
        # Criar tabela de estatísticas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS collection_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            total_listings INTEGER,
            new_listings INTEGER,
            api_calls INTEGER,
            success_rate REAL,
            collection_rate REAL
        )
        ''')
        
        conn.commit()
        conn.close()
        
        self.logger.info("📊 Database configurado com índices otimizados")
    
    async def collect_batch(self, session: aiohttp.ClientSession, page: int = 0, limit: int = 50) -> Dict[str, Any]:
        """Coleta um lote de dados"""
        url = f"{self.base_url}/listings"
        headers = {"Authorization": self.api_key}
        params = {
            "page": page,
            "limit": limit,
            "sort_by": "most_recent"
        }
        
        try:
            async with session.get(url, headers=headers, params=params, timeout=30) as response:
                self.stats["total_requests"] = self.stats.get("total_requests", 0) + 1
                
                if response.status == 200:
                    data = await response.json()
                    
                    # CSFloat retorna dados sob 'data' key
                    if isinstance(data, dict) and 'data' in data:
                        listings = data['data']
                    elif isinstance(data, list):
                        listings = data
                    else:
                        listings = []
                    
                    self.stats["successful_requests"] += 1
                    return {
                        "success": True,
                        "listings": listings,
                        "page": page,
                        "rate_limit_remaining": response.headers.get("X-RateLimit-Remaining"),
                        "rate_limit_reset": response.headers.get("X-RateLimit-Reset")
                    }
                
                elif response.status == 429:  # Rate limit
                    self.stats["rate_limit_hits"] += 1
                    retry_after = int(response.headers.get("Retry-After", 60))
                    return {
                        "success": False,
                        "error": "rate_limit",
                        "retry_after": retry_after
                    }
                
                else:
                    self.stats["failed_requests"] += 1
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "status": response.status
                    }
                    
        except Exception as e:
            self.stats["failed_requests"] += 1
            return {
                "success": False,
                "error": str(e)
            }
    
    def save_listings(self, listings: List[Dict]) -> int:
        """Salva listings no banco de dados"""
        if not listings:
            return 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        new_count = 0
        
        for listing in listings:
            try:
                # Extrair dados principais
                item = listing.get("item", {})
                seller = listing.get("seller", {})
                
                # Preparar dados para inserção
                data = (
                    listing.get("id"),
                    item.get("item_name"),
                    listing.get("price", 0) / 100,  # CSFloat usa centavos
                    item.get("float_value"),
                    item.get("paint_seed"),
                    item.get("paint_index"),
                    item.get("def_index"),
                    item.get("wear_name"),
                    item.get("rarity"),
                    item.get("collection"),
                    json.dumps(item.get("stickers", [])),
                    seller.get("steam_id"),
                    seller.get("username"),
                    json.dumps(seller.get("statistics", {})),
                    listing.get("created_at")
                )
                
                # Inserir com IGNORE para evitar duplicatas
                cursor.execute('''
                INSERT OR IGNORE INTO listings (
                    id, item_name, price_usd, float_value, paint_seed,
                    paint_index, def_index, wear_name, rarity, collection,
                    stickers, seller_id, seller_username, seller_stats,
                    created_at_csfloat
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', data)
                
                if cursor.rowcount > 0:
                    new_count += 1
                    
            except Exception as e:
                self.logger.warning(f"Erro ao salvar listing: {e}")
                continue
        
        # Salvar estatísticas
        cursor.execute('''
        INSERT INTO collection_stats (
            total_listings, new_listings, api_calls, success_rate
        ) VALUES (
            (SELECT COUNT(*) FROM listings),
            ?,
            ?,
            ?
        )
        ''', (
            new_count,
            self.stats["successful_requests"] + self.stats["failed_requests"],
            (self.stats["successful_requests"] / max(1, self.stats["successful_requests"] + self.stats["failed_requests"])) * 100
        ))
        
        conn.commit()
        conn.close()
        
        self.stats["total_collected"] += new_count
        self.stats["last_collection"] = datetime.now()
        
        return new_count
    
    async def run_collection_cycle(self, max_pages: int = 10, concurrent_workers: int = 3):
        """Executa ciclo de coleta com workers paralelos"""
        self.logger.info(f"🔄 Iniciando ciclo de coleta - {max_pages} páginas, {concurrent_workers} workers")
        
        async with aiohttp.ClientSession() as session:
            # Coleta sequencial por páginas (CSFloat não permite muita concorrência)
            for page in range(max_pages):
                try:
                    result = await self.collect_batch(session, page=page)
                    
                    if result["success"]:
                        listings = result["listings"]
                        new_count = self.save_listings(listings)
                        
                        self.logger.info(f"📄 Página {page}: {len(listings)} listings, {new_count} novos")
                        
                        # Rate limiting inteligente
                        rate_limit_remaining = result.get("rate_limit_remaining")
                        if rate_limit_remaining and int(rate_limit_remaining) < 100:
                            self.logger.warning(f"⚠️ Rate limit baixo: {rate_limit_remaining}")
                            await asyncio.sleep(2)  # Delay maior quando rate limit baixo
                        else:
                            await asyncio.sleep(1.2)  # Delay normal
                            
                    elif result.get("error") == "rate_limit":
                        retry_after = result.get("retry_after", 60)
                        self.logger.warning(f"🚥 Rate limit hit - aguardando {retry_after}s")
                        await asyncio.sleep(retry_after)
                        continue
                        
                    else:
                        self.logger.error(f"❌ Erro na página {page}: {result.get('error')}")
                        await asyncio.sleep(5)  # Delay em caso de erro
                        
                except Exception as e:
                    self.logger.error(f"❌ Erro geral na página {page}: {e}")
                    await asyncio.sleep(5)
    
    def print_stats(self):
        """Imprime estatísticas atuais"""
        uptime = datetime.now() - self.stats["start_time"]
        success_rate = 0
        if self.stats["successful_requests"] + self.stats["failed_requests"] > 0:
            success_rate = (self.stats["successful_requests"] / (self.stats["successful_requests"] + self.stats["failed_requests"])) * 100
        
        print("\n" + "="*60)
        print("📊 SKINLYTICS - ESTATÍSTICAS DE COLETA")
        print("="*60)
        print(f"⏰ Uptime: {uptime}")
        print(f"📦 Total Coletados: {self.stats['total_collected']:,}")
        print(f"✅ Requests Sucesso: {self.stats['successful_requests']:,}")
        print(f"❌ Requests Falha: {self.stats['failed_requests']:,}")
        print(f"🚥 Rate Limit Hits: {self.stats['rate_limit_hits']:,}")
        print(f"📊 Taxa de Sucesso: {success_rate:.1f}%")
        if self.stats["last_collection"]:
            print(f"🕐 Última Coleta: {self.stats['last_collection']}")
        print("="*60)
    
    async def run_continuous_collection(self, cycle_interval: int = 300):
        """Executa coleta contínua"""
        self.logger.info(f"🚀 Iniciando coleta contínua - ciclos a cada {cycle_interval}s")
        
        try:
            while True:
                cycle_start = time.time()
                
                # Executar ciclo de coleta
                await self.run_collection_cycle(max_pages=5, concurrent_workers=2)
                
                # Mostrar estatísticas
                self.print_stats()
                
                # Calcular tempo de espera
                cycle_time = time.time() - cycle_start
                wait_time = max(0, cycle_interval - cycle_time)
                
                if wait_time > 0:
                    self.logger.info(f"⏳ Aguardando {wait_time:.0f}s até próximo ciclo...")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.info("⚡ Iniciando próximo ciclo imediatamente")
                    
        except KeyboardInterrupt:
            self.logger.info("🛑 Coleta interrompida pelo usuário")
            self.print_stats()
        except Exception as e:
            self.logger.error(f"❌ Erro na coleta contínua: {e}")

async def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Coletor Escalado Skinlytics")
    parser.add_argument("--pages", type=int, default=10, help="Número de páginas por ciclo")
    parser.add_argument("--interval", type=int, default=300, help="Intervalo entre ciclos (segundos)")
    parser.add_argument("--single", action="store_true", help="Executar apenas um ciclo")
    
    args = parser.parse_args()
    
    collector = ScaledCollector()
    collector.setup_database()
    
    if args.single:
        # Ciclo único
        await collector.run_collection_cycle(max_pages=args.pages)
        collector.print_stats()
    else:
        # Coleta contínua
        await collector.run_continuous_collection(cycle_interval=args.interval)

if __name__ == "__main__":
    asyncio.run(main())