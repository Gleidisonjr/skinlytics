"""
CS2 Skin Trading Database Models

Este módulo define os modelos de dados para o sistema de trading de skins CS2.
Utiliza SQLAlchemy como ORM para gerenciar as operações do banco de dados.

Classes:
    Skin: Representa uma skin de CS2 com suas propriedades básicas
    Listing: Representa um listing de venda/leilão no CSFloat
    StickerApplication: Representa stickers aplicados em skins
    Alert: Sistema de alertas para monitoramento de preços
    User: Usuários do sistema (para futuras implementações)

Author: CS2 Skin Tracker Team
Version: 2.0.0
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
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
    Modelo que representa uma skin de CS2.
    
    Esta classe armazena todas as informações básicas de uma skin, incluindo
    seus identificadores únicos, propriedades visuais e metadados do jogo.
    
    Attributes:
        id (int): Chave primária auto-incrementada
        market_hash_name (str): Nome único da skin no Steam Market (máx 500 chars)
        item_name (str): Nome do item base (ex: "AK-47", "AWP") (máx 200 chars)
        wear_name (str): Condição da skin (ex: "Factory New") (máx 50 chars)
        def_index (int): Índice de definição do item no jogo
        paint_index (int): Índice da pintura/padrão da skin
        rarity (int): Nível de raridade (0-7, onde 7 = mais raro)
        quality (int): Qualidade do item no sistema Steam
        collection (str): Coleção à qual a skin pertence (máx 200 chars)
        description (str): Descrição detalhada da skin
        icon_url (str): URL da imagem/ícone da skin (máx 500 chars)
        is_stattrak (bool): Se a skin possui contador StatTrak
        is_souvenir (bool): Se a skin é uma versão Souvenir
        created_at (datetime): Timestamp de criação do registro
        updated_at (datetime): Timestamp da última atualização
        
    Relationships:
        listings: Lista de todos os listings desta skin
        alerts: Lista de alertas configurados para esta skin
    """
    __tablename__ = 'skins'
    
    # Identificador único
    id = Column(Integer, primary_key=True, comment="Chave primária auto-incrementada")
    
    # Identificadores da skin
    market_hash_name = Column(String(500), unique=True, nullable=False, 
                             comment="Nome único da skin no Steam Market")
    item_name = Column(String(200), comment="Nome do item base (ex: AK-47)")
    wear_name = Column(String(50), comment="Condição da skin (ex: Factory New)")
    
    # Identificadores do jogo
    def_index = Column(Integer, comment="Índice de definição do item no CS2")
    paint_index = Column(Integer, comment="Índice da pintura/padrão da skin")
    
    # Propriedades da skin
    rarity = Column(Integer, comment="Nível de raridade (0-7)")
    quality = Column(Integer, comment="Qualidade do item no sistema Steam")
    collection = Column(String(200), comment="Coleção à qual pertence")
    description = Column(Text, comment="Descrição detalhada da skin")
    icon_url = Column(String(500), comment="URL da imagem da skin")
    
    # Flags especiais
    is_stattrak = Column(Boolean, default=False, comment="Possui contador StatTrak")
    is_souvenir = Column(Boolean, default=False, comment="É versão Souvenir")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, comment="Data de criação")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, 
                       comment="Data da última atualização")
    
    # Relacionamentos
    listings = relationship('Listing', back_populates='skin', cascade='all, delete-orphan',
                           doc="Todos os listings desta skin")
    alerts = relationship('Alert', back_populates='skin', cascade='all, delete-orphan',
                         doc="Alertas configurados para esta skin")

class Listing(Base):
    __tablename__ = 'listings'
    
    id = Column(String(50), primary_key=True)  # CSFloat listing ID
    skin_id = Column(Integer, ForeignKey('skins.id'))
    created_at_csfloat = Column(DateTime)
    type = Column(String(20))  # 'buy_now' or 'auction'
    price = Column(Integer)  # Price in cents
    state = Column(String(20))  # 'listed', 'sold', etc.
    
    # Item details
    asset_id = Column(String(50))
    paint_seed = Column(Integer)
    float_value = Column(Float)
    tradable = Column(Integer)
    inspect_link = Column(Text)
    has_screenshot = Column(Boolean, default=False)
    
    # Seller info
    seller_steam_id = Column(String(50))
    seller_username = Column(String(100))
    seller_avatar = Column(String(500))
    seller_online = Column(Boolean, default=False)
    
    # Market data
    min_offer_price = Column(Integer)
    max_offer_discount = Column(Integer)
    watchers = Column(Integer, default=0)
    is_watchlisted = Column(Boolean, default=False)
    
    # Seller statistics (expandido)
    seller_total_trades = Column(Integer)
    seller_verified_trades = Column(Integer)
    seller_median_trade_time = Column(Integer)
    seller_failed_trades = Column(Integer)
    
    # Our tracking
    collected_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    skin = relationship('Skin', back_populates='listings')
    stickers = relationship('StickerApplication', back_populates='listing', cascade='all, delete-orphan')

class StickerApplication(Base):
    __tablename__ = 'sticker_applications'
    
    id = Column(Integer, primary_key=True)
    listing_id = Column(String(50), ForeignKey('listings.id'))
    sticker_id = Column(Integer)
    slot = Column(Integer)
    wear = Column(Float)
    icon_url = Column(String(500))
    name = Column(String(200))
    scm_price = Column(Integer)  # Steam Community Market price
    scm_volume = Column(Integer)
    
    # Relationships
    listing = relationship('Listing', back_populates='stickers')

class Alert(Base):
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    skin_id = Column(Integer, ForeignKey('skins.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    alert_type = Column(String(50))  # 'price_drop', 'price_rise', 'volume_spike'
    threshold_value = Column(Float)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    skin = relationship('Skin', back_populates='alerts')
    user = relationship('User', back_populates='alerts')

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True)
    password_hash = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    alerts = relationship('Alert', back_populates='user')

# Database configuration
def get_database_url():
    """Get database URL from environment or use SQLite as fallback"""
    if os.getenv('DATABASE_URL'):
        return os.getenv('DATABASE_URL')
    return 'sqlite:///./data/skins_saas.db'

def get_engine():
    """Create database engine"""
    database_url = get_database_url()
    return create_engine(database_url)

def create_tables():
    """Create all tables"""
    engine = get_engine()
    Base.metadata.create_all(engine)
    return engine

def get_session():
    """Get database session"""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session() 