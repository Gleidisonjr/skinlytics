"""
ClickHouse Models for Big Data Analytics and ML

Modelos otimizados para ClickHouse focados em analytics de alta performance,
time series e preparação de dados para Machine Learning.

Features:
    - Schema otimizado para consultas analíticas
    - Particionamento automático por data
    - Índices especializados para ML
    - Compressão avançada de dados
    - Suporte a operações vetoriais

Author: CS2 Skin Tracker Team
Version: 2.0.0
"""

from clickhouse_connect import get_client
from typing import Dict, List, Any, Optional
from datetime import datetime, date
import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class ClickHouseConnection:
    """Gerenciador de conexão ClickHouse otimizado"""
    
    def __init__(self):
        self.host = os.getenv('CLICKHOUSE_HOST', 'localhost')
        self.port = int(os.getenv('CLICKHOUSE_PORT', 8123))
        self.username = os.getenv('CLICKHOUSE_USER', 'default')
        self.password = os.getenv('CLICKHOUSE_PASSWORD', '')
        self.database = os.getenv('CLICKHOUSE_DATABASE', 'cs2_analytics')
        self.client = None
    
    def connect(self):
        """Estabelece conexão com ClickHouse"""
        try:
            self.client = get_client(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                database=self.database
            )
            logger.info(f"🔗 Conectado ao ClickHouse: {self.host}:{self.port}/{self.database}")
            return self.client
        except Exception as e:
            logger.error(f"❌ Erro ao conectar ClickHouse: {e}")
            raise
    
    def disconnect(self):
        """Fecha conexão"""
        if self.client:
            self.client.close()
            logger.info("🔌 Conexão ClickHouse fechada")

@dataclass
class ClickHouseSchemas:
    """Schemas otimizados para ClickHouse"""
    
    @staticmethod
    def get_listings_analytics_schema() -> str:
        """
        Schema para análise de listings - otimizado para ML e analytics
        
        Features:
            - Particionamento por data para queries rápidas
            - Índices especializados para campos ML
            - Compressão LZ4 para economia de espaço
            - TTL automático para dados antigos
        """
        return """
        CREATE TABLE IF NOT EXISTS listings_analytics (
            -- Identificação
            listing_id String CODEC(LZ4),
            skin_id UInt32 CODEC(Delta, LZ4),
            
            -- Timestamps otimizados
            created_at_csfloat DateTime CODEC(Delta, LZ4),
            collected_at DateTime DEFAULT now() CODEC(Delta, LZ4),
            date_partition Date MATERIALIZED toDate(created_at_csfloat),
            
            -- Dados de preço (otimizados para ML)
            price_cents UInt32 CODEC(Delta, LZ4),
            price_usd Float32 MATERIALIZED price_cents / 100.0,
            log_price Float32 MATERIALIZED log(price_usd + 1),
            
            -- Características do item (features para ML)
            item_name LowCardinality(String) CODEC(LZ4),
            wear_name LowCardinality(String) CODEC(LZ4),
            def_index UInt16 CODEC(LZ4),
            paint_index UInt16 CODEC(LZ4),
            rarity LowCardinality(String) CODEC(LZ4),
            quality LowCardinality(String) CODEC(LZ4),
            collection LowCardinality(String) CODEC(LZ4),
            
            -- Float e condições (crítico para ML)
            float_value Float32 CODEC(LZ4),
            float_category LowCardinality(String) MATERIALIZED
                CASE 
                    WHEN float_value <= 0.07 THEN 'Factory New'
                    WHEN float_value <= 0.15 THEN 'Minimal Wear'
                    WHEN float_value <= 0.38 THEN 'Field-Tested'
                    WHEN float_value <= 0.45 THEN 'Well-Worn'
                    ELSE 'Battle-Scarred'
                END,
            paint_seed UInt32 CODEC(LZ4),
            
            -- Dados do vendedor (features comportamentais)
            seller_steam_id String CODEC(LZ4),
            seller_total_trades UInt32 CODEC(Delta, LZ4),
            seller_verified_trades UInt32 CODEC(Delta, LZ4),
            seller_median_trade_time UInt32 CODEC(Delta, LZ4),
            seller_failed_trades UInt16 CODEC(LZ4),
            seller_success_rate Float32 MATERIALIZED 
                CASE 
                    WHEN seller_total_trades > 0 
                    THEN (seller_verified_trades - seller_failed_trades) / seller_total_trades
                    ELSE 0
                END,
            
            -- Estado e tipo
            listing_type LowCardinality(String) CODEC(LZ4),
            listing_state LowCardinality(String) CODEC(LZ4),
            
            -- Features derivadas para ML
            price_percentile_by_item Float32 DEFAULT 0,
            float_rarity_score Float32 DEFAULT 0,
            seller_reputation_score Float32 DEFAULT 0,
            time_of_day UInt8 MATERIALIZED toHour(created_at_csfloat),
            day_of_week UInt8 MATERIALIZED toDayOfWeek(created_at_csfloat),
            
            -- Metadados
            data_source LowCardinality(String) DEFAULT 'csfloat' CODEC(LZ4),
            processing_version UInt8 DEFAULT 1 CODEC(LZ4)
            
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(date_partition)
        ORDER BY (item_name, float_value, created_at_csfloat, listing_id)
        PRIMARY KEY (item_name, float_value, created_at_csfloat)
        SETTINGS 
            index_granularity = 8192,
            ttl_only_drop_parts = 1
        TTL date_partition + INTERVAL 2 YEAR DELETE
        """
    
    @staticmethod
    def get_price_history_schema() -> str:
        """Schema para histórico de preços - otimizado para time series"""
        return """
        CREATE TABLE IF NOT EXISTS price_history_ts (
            -- Time series otimizado
            timestamp DateTime CODEC(Delta, LZ4),
            date_partition Date MATERIALIZED toDate(timestamp),
            
            -- Identificação
            item_name LowCardinality(String) CODEC(LZ4),
            wear_name LowCardinality(String) CODEC(LZ4),
            float_range LowCardinality(String) CODEC(LZ4),
            
            -- Métricas de preço
            min_price Float32 CODEC(LZ4),
            max_price Float32 CODEC(LZ4),
            avg_price Float32 CODEC(LZ4),
            median_price Float32 CODEC(LZ4),
            volume UInt32 CODEC(Delta, LZ4),
            
            -- Estatísticas avançadas
            price_volatility Float32 CODEC(LZ4),
            price_trend Float32 CODEC(LZ4),
            market_cap Float64 CODEC(LZ4),
            
            -- Features para ML
            price_ma_7d Float32 DEFAULT 0,
            price_ma_30d Float32 DEFAULT 0,
            volume_ma_7d Float32 DEFAULT 0,
            rsi_14d Float32 DEFAULT 50,
            bollinger_upper Float32 DEFAULT 0,
            bollinger_lower Float32 DEFAULT 0
            
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(date_partition)
        ORDER BY (item_name, timestamp)
        PRIMARY KEY (item_name, timestamp)
        SETTINGS index_granularity = 8192
        TTL date_partition + INTERVAL 5 YEAR DELETE
        """
    
    @staticmethod
    def get_ml_features_schema() -> str:
        """Schema para features de ML pré-computadas"""
        return """
        CREATE TABLE IF NOT EXISTS ml_features (
            -- Identificação
            feature_id String CODEC(LZ4),
            item_name LowCardinality(String) CODEC(LZ4),
            timestamp DateTime CODEC(Delta, LZ4),
            
            -- Features categóricas (encoded)
            wear_encoded UInt8 CODEC(LZ4),
            rarity_encoded UInt8 CODEC(LZ4),
            collection_encoded UInt16 CODEC(LZ4),
            
            -- Features numéricas (normalizadas)
            float_normalized Float32 CODEC(LZ4),
            price_log_normalized Float32 CODEC(LZ4),
            volume_normalized Float32 CODEC(LZ4),
            
            -- Features temporais
            hour_sin Float32 CODEC(LZ4),
            hour_cos Float32 CODEC(LZ4),
            day_sin Float32 CODEC(LZ4),
            day_cos Float32 CODEC(LZ4),
            month_sin Float32 CODEC(LZ4),
            month_cos Float32 CODEC(LZ4),
            
            -- Features de vendedor
            seller_reputation_norm Float32 CODEC(LZ4),
            seller_volume_norm Float32 CODEC(LZ4),
            seller_speed_norm Float32 CODEC(LZ4),
            
            -- Features de mercado
            market_volatility Float32 CODEC(LZ4),
            market_trend Float32 CODEC(LZ4),
            market_momentum Float32 CODEC(LZ4),
            
            -- Target variables
            price_next_1h Float32 DEFAULT 0,
            price_next_6h Float32 DEFAULT 0,
            price_next_24h Float32 DEFAULT 0,
            price_change_1h Float32 DEFAULT 0,
            price_change_6h Float32 DEFAULT 0,
            price_change_24h Float32 DEFAULT 0,
            
            -- Metadados
            feature_version UInt8 DEFAULT 1,
            created_at DateTime DEFAULT now()
            
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(toDate(timestamp))
        ORDER BY (item_name, timestamp, feature_id)
        PRIMARY KEY (item_name, timestamp)
        SETTINGS index_granularity = 8192
        """

class ClickHouseAnalytics:
    """Classe para operações analíticas no ClickHouse"""
    
    def __init__(self):
        self.conn = ClickHouseConnection()
        self.client = None
    
    async def __aenter__(self):
        """Async context manager"""
        self.client = self.conn.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        self.conn.disconnect()
    
    def create_tables(self):
        """Cria todas as tabelas necessárias"""
        schemas = ClickHouseSchemas()
        
        tables = [
            ("listings_analytics", schemas.get_listings_analytics_schema()),
            ("price_history_ts", schemas.get_price_history_schema()),
            ("ml_features", schemas.get_ml_features_schema())
        ]
        
        for table_name, schema in tables:
            try:
                self.client.command(schema)
                logger.info(f"✅ Tabela {table_name} criada/verificada")
            except Exception as e:
                logger.error(f"❌ Erro ao criar tabela {table_name}: {e}")
                raise
    
    def create_materialized_views(self):
        """Cria views materializadas para agregações automáticas"""
        views = [
            # Agregação horária de preços
            """
            CREATE MATERIALIZED VIEW IF NOT EXISTS price_hourly_mv
            TO price_history_ts
            AS SELECT
                toStartOfHour(created_at_csfloat) as timestamp,
                item_name,
                wear_name,
                CASE 
                    WHEN float_value <= 0.07 THEN 'Factory New'
                    WHEN float_value <= 0.15 THEN 'Minimal Wear'
                    WHEN float_value <= 0.38 THEN 'Field-Tested'
                    WHEN float_value <= 0.45 THEN 'Well-Worn'
                    ELSE 'Battle-Scarred'
                END as float_range,
                min(price_usd) as min_price,
                max(price_usd) as max_price,
                avg(price_usd) as avg_price,
                quantile(0.5)(price_usd) as median_price,
                count() as volume,
                stddevPop(price_usd) as price_volatility,
                0 as price_trend,
                sum(price_usd) as market_cap
            FROM listings_analytics
            WHERE created_at_csfloat >= now() - INTERVAL 1 DAY
            GROUP BY timestamp, item_name, wear_name, float_range
            """,
            
            # Ranking de items por popularidade
            """
            CREATE MATERIALIZED VIEW IF NOT EXISTS item_popularity_mv
            ENGINE = AggregatingMergeTree()
            PARTITION BY toYYYYMM(date_partition)
            ORDER BY (date_partition, item_name)
            AS SELECT
                date_partition,
                item_name,
                wear_name,
                countState() as listing_count,
                avgState(price_usd) as avg_price,
                minState(price_usd) as min_price,
                maxState(price_usd) as max_price,
                uniqState(seller_steam_id) as unique_sellers
            FROM listings_analytics
            GROUP BY date_partition, item_name, wear_name
            """
        ]
        
        for view_sql in views:
            try:
                self.client.command(view_sql)
                logger.info("✅ Materialized view criada")
            except Exception as e:
                logger.error(f"❌ Erro ao criar view: {e}")
    
    def bulk_insert_listings(self, listings_data: List[Dict[str, Any]]) -> int:
        """
        Inserção em massa otimizada para ClickHouse
        
        Args:
            listings_data: Lista de dicionários com dados dos listings
            
        Returns:
            Número de registros inseridos
        """
        if not listings_data:
            return 0
        
        try:
            # Preparar dados para inserção
            columns = [
                'listing_id', 'skin_id', 'created_at_csfloat', 'price_cents',
                'item_name', 'wear_name', 'def_index', 'paint_index',
                'rarity', 'quality', 'collection', 'float_value', 'paint_seed',
                'seller_steam_id', 'seller_total_trades', 'seller_verified_trades',
                'seller_median_trade_time', 'seller_failed_trades',
                'listing_type', 'listing_state'
            ]
            
            # Converter dados para formato ClickHouse
            formatted_data = []
            for listing in listings_data:
                row = []
                for col in columns:
                    value = listing.get(col)
                    # Tratar valores None
                    if value is None:
                        if 'price' in col or col.endswith('_trades') or col.endswith('_time'):
                            value = 0
                        elif col == 'float_value':
                            value = 0.0
                        else:
                            value = ''
                    row.append(value)
                formatted_data.append(row)
            
            # Inserção em massa
            self.client.insert(
                table='listings_analytics',
                data=formatted_data,
                column_names=columns
            )
            
            inserted_count = len(formatted_data)
            logger.info(f"📊 {inserted_count} registros inseridos no ClickHouse")
            return inserted_count
            
        except Exception as e:
            logger.error(f"❌ Erro na inserção em massa: {e}")
            raise
    
    def get_analytics_query(self, query_type: str, **params) -> str:
        """
        Retorna queries otimizadas para analytics comuns
        
        Args:
            query_type: Tipo de query (price_trends, volume_analysis, etc.)
            **params: Parâmetros específicos da query
        """
        queries = {
            'price_trends': """
                SELECT 
                    item_name,
                    toStartOfHour(created_at_csfloat) as hour,
                    avg(price_usd) as avg_price,
                    count() as volume,
                    stddevPop(price_usd) as volatility
                FROM listings_analytics 
                WHERE created_at_csfloat >= now() - INTERVAL {days} DAY
                    AND item_name ILIKE '%{item_filter}%'
                GROUP BY item_name, hour
                ORDER BY hour DESC
                LIMIT {limit}
            """,
            
            'top_items': """
                SELECT 
                    item_name,
                    wear_name,
                    count() as listings_count,
                    avg(price_usd) as avg_price,
                    min(price_usd) as min_price,
                    max(price_usd) as max_price,
                    quantile(0.5)(price_usd) as median_price
                FROM listings_analytics
                WHERE date_partition >= today() - {days}
                GROUP BY item_name, wear_name
                HAVING listings_count >= {min_listings}
                ORDER BY listings_count DESC, avg_price DESC
                LIMIT {limit}
            """,
            
            'float_analysis': """
                SELECT 
                    item_name,
                    float_category,
                    count() as count,
                    avg(price_usd) as avg_price,
                    avg(float_value) as avg_float,
                    quantile(0.95)(price_usd) as p95_price
                FROM listings_analytics
                WHERE item_name = '{item_name}'
                    AND date_partition >= today() - {days}
                GROUP BY item_name, float_category
                ORDER BY avg_price DESC
            """
        }
        
        query_template = queries.get(query_type)
        if not query_template:
            raise ValueError(f"Query type '{query_type}' não suportado")
        
        return query_template.format(**params)