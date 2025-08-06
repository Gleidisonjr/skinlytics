"""
CS2 Skin Trading Database Models - OTIMIZED VERSION
Versão otimizada focada em performance e insights de trading

Esta versão remove campos desnecessários para manter o banco leve,
rápido e focado nos dados essenciais para análise de mercado.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Base declarativa para todos os modelos
Base = declarative_base()

class Skin(Base):
    """
    Modelo otimizado para skin de CS2 - apenas dados essenciais
    """
    __tablename__ = 'skins_optimized'
    
    # Identificador único
    id = Column(Integer, primary_key=True)
    
    # Identificadores essenciais da skin
    market_hash_name = Column(String(500), unique=True, nullable=False, index=True)
    item_name = Column(String(200), index=True)  # Para filtros rápidos
    wear_name = Column(String(50), index=True)   # Para filtros rápidos
    
    # Identificadores do jogo (essenciais para ML)
    def_index = Column(Integer, index=True)
    paint_index = Column(Integer, index=True)
    
    # Propriedades essenciais
    rarity = Column(Integer, index=True)  # Importante para segmentação
    
    # Flags especiais (importantes para trading)
    is_stattrak = Column(Boolean, default=False, index=True)
    is_souvenir = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    listings = relationship('ListingOptimized', back_populates='skin', cascade='all, delete-orphan')

class ListingOptimized(Base):
    """
    Modelo otimizado para listings - foco em dados de trading
    """
    __tablename__ = 'listings_optimized'
    
    # Identificadores
    id = Column(String(50), primary_key=True)
    skin_id = Column(Integer, ForeignKey('skins_optimized.id'), index=True)
    
    # Dados temporais (essenciais para análise de tendências)
    created_at_csfloat = Column(DateTime, index=True)
    collected_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Dados de mercado (CORE para trading)
    price = Column(Integer, index=True)  # Preço em centavos
    type = Column(String(20), index=True)  # buy_now/auction
    state = Column(String(20), index=True)  # listed/sold
    
    # Propriedades do item (essenciais para ML/pricing)
    paint_seed = Column(Integer)  # Importante para patterns especiais
    float_value = Column(Float, index=True)  # Crucial para pricing
    
    # Dados de mercado (importantes para insights)
    watchers = Column(Integer, default=0, index=True)  # Demanda
    min_offer_price = Column(Integer)  # Floor price
    max_offer_discount = Column(Integer)  # Flexibilidade do seller
    
    # Seller credibility (essencial para confiança)
    seller_total_trades = Column(Integer, index=True)
    seller_verified_trades = Column(Integer)
    seller_median_trade_time = Column(Integer)  # Velocidade de venda
    seller_failed_trades = Column(Integer)
    
    # Hash do seller (privacidade + tracking)
    seller_hash = Column(String(64), index=True)  # Hash do steam_id
    
    # Relacionamentos
    skin = relationship('Skin', back_populates='listings')
    
    # Índices compostos para consultas frequentes
    __table_args__ = (
        Index('idx_skin_price_date', 'skin_id', 'price', 'collected_at'),
        Index('idx_price_float', 'price', 'float_value'),
        Index('idx_seller_performance', 'seller_total_trades', 'seller_verified_trades'),
    )

class PriceHistory(Base):
    """
    Tabela agregada para histórico de preços (performance)
    """
    __tablename__ = 'price_history'
    
    id = Column(Integer, primary_key=True)
    skin_id = Column(Integer, ForeignKey('skins_optimized.id'), index=True)
    date = Column(DateTime, index=True)
    
    # Agregações diárias
    avg_price = Column(Float)
    min_price = Column(Float)
    max_price = Column(Float)
    volume = Column(Integer)  # Número de listings
    avg_float = Column(Float)
    
    # Índices para consultas rápidas e constraint único
    __table_args__ = (
        Index('idx_skin_date', 'skin_id', 'date'),
        Index('idx_skin_date_unique', 'skin_id', 'date', unique=True),  # Para ON CONFLICT
    )

class MarketInsights(Base):
    """
    Tabela para insights pré-calculados (performance)
    """
    __tablename__ = 'market_insights'
    
    id = Column(Integer, primary_key=True)
    skin_id = Column(Integer, ForeignKey('skins_optimized.id'), unique=True, index=True)
    
    # Métricas de mercado
    current_avg_price = Column(Float)
    price_trend_7d = Column(Float)  # % change last 7 days
    price_trend_30d = Column(Float)  # % change last 30 days
    volume_trend_7d = Column(Float)
    liquidity_score = Column(Float)  # Volume/Price ratio
    
    # Oportunidades
    is_undervalued = Column(Boolean, default=False, index=True)
    opportunity_score = Column(Float, index=True)  # 0-100
    
    # Timestamps
    last_updated = Column(DateTime, default=datetime.utcnow, index=True)

# Database configuration (mesmas funções)
def get_database_url():
    """Get database URL from environment or use SQLite as fallback"""
    if os.getenv('DATABASE_URL'):
        return os.getenv('DATABASE_URL')
    return 'sqlite:///./data/skins_optimized.db'

def get_engine():
    """Create database engine"""
    database_url = get_database_url()
    return create_engine(database_url, echo=False)  # Desabilitar echo para performance

def create_tables():
    """Create all tables"""
    engine = get_engine()
    Base.metadata.create_all(engine)
    logger.info("Tabelas otimizadas criadas com sucesso!")

def get_session():
    """Create database session"""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()

if __name__ == "__main__":
    create_tables()