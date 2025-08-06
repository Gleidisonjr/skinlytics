"""
Hybrid Database Manager - PostgreSQL + ClickHouse

Sistema híbrido que combina PostgreSQL (dados operacionais) com 
ClickHouse (analytics e ML) para máxima performance e escalabilidade.

Arquitetura:
    - PostgreSQL: APIs, relacionamentos, dados transacionais
    - ClickHouse: Analytics, ML features, time series, big data
    - Pipeline: Sincronização automática entre os bancos
    - Cache: Redis para queries frequentes

Features:
    - Sincronização automática bidirecional
    - Particionamento inteligente de dados
    - Queries otimizadas para cada tipo de workload
    - Fallback automático em caso de falha
    - Métricas de performance em tempo real

Author: CS2 Skin Tracker Team
Version: 2.0.0
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
import json
import hashlib

# Database drivers
import asyncpg
from clickhouse_connect import get_client
import redis.asyncio as redis

# SQLAlchemy para PostgreSQL
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, select, and_, or_

# Nossos modelos
from .database import Skin, Listing, StickerApplication
from .clickhouse_models import ClickHouseConnection, ClickHouseAnalytics

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Configuração dos bancos de dados"""
    # PostgreSQL
    postgres_url: str
    postgres_pool_size: int = 20
    postgres_max_overflow: int = 30
    
    # ClickHouse
    clickhouse_host: str = 'localhost'
    clickhouse_port: int = 8123
    clickhouse_user: str = 'default'
    clickhouse_password: str = ''
    clickhouse_database: str = 'cs2_analytics'
    
    # Redis Cache
    redis_url: str = 'redis://localhost:6379'
    cache_ttl: int = 3600  # 1 hora
    
    # Sync settings
    sync_batch_size: int = 1000
    sync_interval: int = 60  # segundos

@dataclass
class QueryMetrics:
    """Métricas de performance de queries"""
    query_type: str
    database: str
    duration: float
    rows_returned: int
    timestamp: datetime
    cache_hit: bool = False

class DatabaseRouter:
    """Roteador inteligente de queries"""
    
    def __init__(self):
        self.routing_rules = {
            # Operações transacionais -> PostgreSQL
            'INSERT': 'postgres',
            'UPDATE': 'postgres',
            'DELETE': 'postgres',
            
            # Analytics e agregações -> ClickHouse
            'ANALYTICS': 'clickhouse',
            'AGGREGATION': 'clickhouse',
            'TIME_SERIES': 'clickhouse',
            'ML_FEATURES': 'clickhouse',
            
            # Leituras simples -> Cache primeiro, depois PostgreSQL
            'SELECT_SIMPLE': 'cache_postgres',
            'SELECT_DETAIL': 'postgres'
        }
    
    def route_query(self, operation: str, table: str, complexity: str = 'simple') -> str:
        """
        Determina qual banco usar baseado na operação
        
        Args:
            operation: Tipo de operação (SELECT, INSERT, etc.)
            table: Tabela alvo
            complexity: Complexidade da query (simple, complex, analytics)
        
        Returns:
            Nome do banco a usar ('postgres', 'clickhouse', 'cache')
        """
        # Regras específicas por tabela
        if table in ['ml_features', 'price_history_ts', 'listings_analytics']:
            if operation == 'SELECT' and complexity == 'analytics':
                return 'clickhouse'
        
        # Regras por operação
        if operation in ['COUNT', 'SUM', 'AVG', 'GROUP BY']:
            return 'clickhouse'
        
        # Regras por complexidade
        if complexity == 'analytics':
            return 'clickhouse'
        elif complexity == 'simple' and operation == 'SELECT':
            return 'cache_postgres'
        
        return self.routing_rules.get(operation, 'postgres')

class HybridDatabase:
    """Gerenciador híbrido de banco de dados"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.router = DatabaseRouter()
        
        # Connections
        self.postgres_engine = None
        self.postgres_session_factory = None
        self.clickhouse_client = None
        self.redis_client = None
        
        # Estado
        self.is_connected = False
        self.sync_task = None
        self.metrics: List[QueryMetrics] = []
        
        logger.info("🔧 HybridDatabase inicializado")
    
    async def connect(self):
        """Conecta a todos os bancos de dados"""
        try:
            # PostgreSQL
            self.postgres_engine = create_async_engine(
                self.config.postgres_url,
                pool_size=self.config.postgres_pool_size,
                max_overflow=self.config.postgres_max_overflow,
                echo=False  # Set True for query debugging
            )
            
            self.postgres_session_factory = sessionmaker(
                self.postgres_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # ClickHouse
            clickhouse_conn = ClickHouseConnection()
            clickhouse_conn.host = self.config.clickhouse_host
            clickhouse_conn.port = self.config.clickhouse_port
            clickhouse_conn.username = self.config.clickhouse_user
            clickhouse_conn.password = self.config.clickhouse_password
            clickhouse_conn.database = self.config.clickhouse_database
            
            self.clickhouse_client = clickhouse_conn.connect()
            
            # Redis
            self.redis_client = redis.from_url(self.config.redis_url)
            await self.redis_client.ping()
            
            self.is_connected = True
            logger.info("🔗 Todos os bancos conectados com sucesso")
            
            # Iniciar sincronização automática
            await self.setup_tables()
            self.start_sync_task()
            
        except Exception as e:
            logger.error(f"❌ Erro ao conectar bancos: {e}")
            raise
    
    async def disconnect(self):
        """Desconecta de todos os bancos"""
        self.is_connected = False
        
        # Parar sincronização
        if self.sync_task:
            self.sync_task.cancel()
        
        # Fechar conexões
        if self.postgres_engine:
            await self.postgres_engine.dispose()
        
        if self.clickhouse_client:
            self.clickhouse_client.close()
        
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("🔌 Todos os bancos desconectados")
    
    async def setup_tables(self):
        """Configura tabelas em todos os bancos"""
        # ClickHouse tables
        async with ClickHouseAnalytics() as analytics:
            analytics.client = self.clickhouse_client
            analytics.create_tables()
            analytics.create_materialized_views()
        
        logger.info("✅ Tabelas configuradas em todos os bancos")
    
    def start_sync_task(self):
        """Inicia tarefa de sincronização automática"""
        if not self.sync_task or self.sync_task.done():
            self.sync_task = asyncio.create_task(self._sync_loop())
            logger.info("🔄 Sincronização automática iniciada")
    
    async def _sync_loop(self):
        """Loop de sincronização entre bancos"""
        while self.is_connected:
            try:
                await self.sync_postgres_to_clickhouse()
                await asyncio.sleep(self.config.sync_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Erro na sincronização: {e}")
                await asyncio.sleep(30)  # Wait antes de tentar novamente
    
    async def sync_postgres_to_clickhouse(self) -> int:
        """
        Sincroniza dados novos do PostgreSQL para ClickHouse
        
        Returns:
            Número de registros sincronizados
        """
        try:
            # Buscar último timestamp sincronizado
            last_sync = await self._get_last_sync_timestamp()
            
            async with self.postgres_session_factory() as session:
                # Query para novos listings
                query = select(Listing).where(
                    Listing.collected_at > last_sync
                ).limit(self.config.sync_batch_size)
                
                result = await session.execute(query)
                new_listings = result.scalars().all()
                
                if not new_listings:
                    return 0
                
                # Preparar dados para ClickHouse
                clickhouse_data = []
                for listing in new_listings:
                    # Buscar skin relacionada
                    skin_query = select(Skin).where(Skin.id == listing.skin_id)
                    skin_result = await session.execute(skin_query)
                    skin = skin_result.scalar_one_or_none()
                    
                    if skin:
                        clickhouse_data.append({
                            'listing_id': listing.id,
                            'skin_id': listing.skin_id,
                            'created_at_csfloat': listing.created_at_csfloat,
                            'price_cents': listing.price,
                            'item_name': skin.item_name,
                            'wear_name': skin.wear_name,
                            'def_index': skin.def_index,
                            'paint_index': skin.paint_index,
                            'rarity': skin.rarity,
                            'quality': skin.quality,
                            'collection': skin.collection,
                            'float_value': listing.float_value,
                            'paint_seed': listing.paint_seed,
                            'seller_steam_id': listing.seller_steam_id,
                            'seller_total_trades': listing.seller_total_trades,
                            'seller_verified_trades': listing.seller_verified_trades,
                            'seller_median_trade_time': listing.seller_median_trade_time,
                            'seller_failed_trades': listing.seller_failed_trades,
                            'listing_type': listing.type,
                            'listing_state': listing.state
                        })
                
                # Inserir no ClickHouse
                if clickhouse_data:
                    async with ClickHouseAnalytics() as analytics:
                        analytics.client = self.clickhouse_client
                        inserted = analytics.bulk_insert_listings(clickhouse_data)
                    
                    # Atualizar timestamp de sincronização
                    latest_timestamp = max(l.collected_at for l in new_listings)
                    await self._update_last_sync_timestamp(latest_timestamp)
                    
                    logger.info(f"🔄 {inserted} registros sincronizados para ClickHouse")
                    return inserted
                
                return 0
                
        except Exception as e:
            logger.error(f"❌ Erro na sincronização: {e}")
            raise
    
    async def _get_last_sync_timestamp(self) -> datetime:
        """Obtém timestamp da última sincronização"""
        try:
            cached = await self.redis_client.get('last_sync_timestamp')
            if cached:
                return datetime.fromisoformat(cached.decode())
        except Exception:
            pass
        
        # Default: últimas 24 horas
        return datetime.utcnow() - timedelta(days=1)
    
    async def _update_last_sync_timestamp(self, timestamp: datetime):
        """Atualiza timestamp da última sincronização"""
        try:
            await self.redis_client.set(
                'last_sync_timestamp',
                timestamp.isoformat(),
                ex=86400 * 7  # 7 dias TTL
            )
        except Exception as e:
            logger.warning(f"⚠️ Erro ao atualizar timestamp de sync: {e}")
    
    async def query(self, 
                   query_sql: str,
                   params: Dict[str, Any] = None,
                   operation: str = 'SELECT',
                   complexity: str = 'simple',
                   cache_key: str = None) -> List[Dict[str, Any]]:
        """
        Executa query no banco apropriado
        
        Args:
            query_sql: SQL da query
            params: Parâmetros da query
            operation: Tipo de operação
            complexity: Complexidade (simple, complex, analytics)
            cache_key: Chave para cache (opcional)
        
        Returns:
            Resultados da query
        """
        start_time = datetime.utcnow()
        
        # Determinar banco
        database = self.router.route_query(operation, '', complexity)
        
        # Tentar cache primeiro se aplicável
        if cache_key and database.startswith('cache'):
            cached_result = await self._get_cached_result(cache_key)
            if cached_result:
                self._record_metrics('cache', 'cache', 0.001, len(cached_result), True)
                return cached_result
        
        # Executar query no banco apropriado
        if database.endswith('postgres') or database == 'postgres':
            result = await self._execute_postgres_query(query_sql, params)
        elif database == 'clickhouse':
            result = await self._execute_clickhouse_query(query_sql, params)
        else:
            # Fallback para PostgreSQL
            result = await self._execute_postgres_query(query_sql, params)
        
        # Cache resultado se aplicável
        if cache_key and len(result) < 10000:  # Não cachear resultados muito grandes
            await self._cache_result(cache_key, result)
        
        # Registrar métricas
        duration = (datetime.utcnow() - start_time).total_seconds()
        self._record_metrics(operation, database, duration, len(result))
        
        return result
    
    async def _execute_postgres_query(self, query_sql: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Executa query no PostgreSQL"""
        async with self.postgres_session_factory() as session:
            result = await session.execute(text(query_sql), params or {})
            rows = result.fetchall()
            
            # Converter para lista de dicionários
            if rows:
                columns = result.keys()
                return [dict(zip(columns, row)) for row in rows]
            
            return []
    
    async def _execute_clickhouse_query(self, query_sql: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Executa query no ClickHouse"""
        # ClickHouse usa sintaxe diferente para parâmetros
        if params:
            for key, value in params.items():
                if isinstance(value, str):
                    query_sql = query_sql.replace(f':{key}', f"'{value}'")
                else:
                    query_sql = query_sql.replace(f':{key}', str(value))
        
        result = self.clickhouse_client.query(query_sql)
        
        # Converter para lista de dicionários
        if result.result_rows:
            columns = result.column_names
            return [dict(zip(columns, row)) for row in result.result_rows]
        
        return []
    
    async def _get_cached_result(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Obtém resultado do cache"""
        try:
            cached = await self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached.decode())
        except Exception as e:
            logger.debug(f"Cache miss para {cache_key}: {e}")
        
        return None
    
    async def _cache_result(self, cache_key: str, result: List[Dict[str, Any]]):
        """Cacheia resultado"""
        try:
            await self.redis_client.set(
                cache_key,
                json.dumps(result, default=str),
                ex=self.config.cache_ttl
            )
        except Exception as e:
            logger.warning(f"⚠️ Erro ao cachear resultado: {e}")
    
    def _record_metrics(self, operation: str, database: str, duration: float, rows: int, cache_hit: bool = False):
        """Registra métricas de performance"""
        metric = QueryMetrics(
            query_type=operation,
            database=database,
            duration=duration,
            rows_returned=rows,
            timestamp=datetime.utcnow(),
            cache_hit=cache_hit
        )
        
        self.metrics.append(metric)
        
        # Manter apenas últimas 1000 métricas
        if len(self.metrics) > 1000:
            self.metrics = self.metrics[-1000:]
        
        # Log de queries lentas
        if duration > 1.0:
            logger.warning(f"🐌 Query lenta: {operation} em {database} - {duration:.2f}s")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de performance"""
        if not self.metrics:
            return {"message": "Nenhuma métrica disponível"}
        
        # Análise por banco
        by_database = {}
        for metric in self.metrics:
            db = metric.database
            if db not in by_database:
                by_database[db] = []
            by_database[db].append(metric.duration)
        
        stats = {}
        for db, durations in by_database.items():
            stats[db] = {
                'queries': len(durations),
                'avg_duration': sum(durations) / len(durations),
                'min_duration': min(durations),
                'max_duration': max(durations)
            }
        
        # Cache hit rate
        cache_hits = sum(1 for m in self.metrics if m.cache_hit)
        cache_rate = (cache_hits / len(self.metrics)) * 100
        
        return {
            'by_database': stats,
            'cache_hit_rate': cache_rate,
            'total_queries': len(self.metrics),
            'slow_queries': len([m for m in self.metrics if m.duration > 1.0])
        }

# Factory function para criar instância configurada
def create_hybrid_database() -> HybridDatabase:
    """Cria instância configurada do banco híbrido"""
    import os
    
    config = DatabaseConfig(
        postgres_url=os.getenv('DATABASE_URL', 'postgresql+asyncpg://user:pass@localhost/cs2_saas'),
        clickhouse_host=os.getenv('CLICKHOUSE_HOST', 'localhost'),
        clickhouse_port=int(os.getenv('CLICKHOUSE_PORT', 8123)),
        clickhouse_user=os.getenv('CLICKHOUSE_USER', 'default'),
        clickhouse_password=os.getenv('CLICKHOUSE_PASSWORD', ''),
        clickhouse_database=os.getenv('CLICKHOUSE_DATABASE', 'cs2_analytics'),
        redis_url=os.getenv('REDIS_URL', 'redis://localhost:6379')
    )
    
    return HybridDatabase(config)