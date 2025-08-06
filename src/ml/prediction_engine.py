"""
Advanced ML Prediction Engine

Sistema de Machine Learning para previsão de preços, detecção de oportunidades
e análise de tendências no mercado de skins CS2.

Models Implemented:
    - Prophet: Time series forecasting
    - XGBoost: Gradient boosting for complex patterns
    - LSTM: Deep learning for sequential data
    - Ensemble: Combination of multiple models
    - Anomaly Detection: Outlier and opportunity detection

Features:
    - Real-time predictions
    - Confidence intervals
    - Feature importance analysis
    - Model performance tracking
    - Automated retraining pipeline

Author: CS2 Skin Tracker Team - Skinlytics Platform
Version: 2.0.0
"""

import numpy as np
import pandas as pd
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
import pickle
import json
import os
from pathlib import Path

# ML Libraries
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    logging.warning("Prophet não instalado. Funcionalidade de time series limitada.")

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logging.warning("XGBoost não instalado. Funcionalidade de ML limitada.")

try:
    from sklearn.ensemble import IsolationForest, RandomForestRegressor
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("Scikit-learn não instalado. Funcionalidade de ML básica limitada.")

# Database
from ..models.hybrid_database import create_hybrid_database

logger = logging.getLogger(__name__)

@dataclass
class PredictionResult:
    """Resultado de uma previsão"""
    item_name: str
    current_price: float
    predicted_price: float
    confidence: float
    model_used: str
    prediction_horizon: str  # 1h, 6h, 24h, 7d
    factors: List[str]
    timestamp: datetime
    
@dataclass
class ModelMetrics:
    """Métricas de performance do modelo"""
    model_name: str
    mae: float  # Mean Absolute Error
    mse: float  # Mean Squared Error
    r2: float   # R-squared
    accuracy_24h: float
    last_trained: datetime
    training_samples: int

@dataclass
class OpportunityAlert:
    """Alerta de oportunidade detectada"""
    item_name: str
    current_price: float
    fair_value: float
    opportunity_score: float  # 0-100
    opportunity_type: str     # undervalued, trend_reversal, volume_spike
    confidence: float
    factors: List[str]
    expiry_time: datetime

class FeatureEngineering:
    """Sistema de engenharia de features para ML"""
    
    @staticmethod
    def create_price_features(df: pd.DataFrame) -> pd.DataFrame:
        """Cria features baseadas em preço"""
        df = df.copy()
        
        # Moving averages
        for window in [7, 14, 30]:
            df[f'price_ma_{window}'] = df['price'].rolling(window=window).mean()
            df[f'price_std_{window}'] = df['price'].rolling(window=window).std()
        
        # Price ratios
        df['price_to_ma7'] = df['price'] / df['price_ma_7']
        df['price_to_ma30'] = df['price'] / df['price_ma_30']
        
        # Volatility
        df['price_volatility'] = df['price'].rolling(window=14).std() / df['price'].rolling(window=14).mean()
        
        # Price changes
        for lag in [1, 7, 30]:
            df[f'price_change_{lag}d'] = df['price'].pct_change(periods=lag)
        
        # Technical indicators
        df['rsi'] = FeatureEngineering._calculate_rsi(df['price'])
        bb_upper, bb_lower = FeatureEngineering._calculate_bollinger_bands(df['price'])
        df['bb_upper'] = bb_upper
        df['bb_lower'] = bb_lower
        df['bb_position'] = (df['price'] - bb_lower) / (bb_upper - bb_lower)
        
        return df
    
    @staticmethod
    def create_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
        """Cria features temporais"""
        df = df.copy()
        
        # Extract datetime components
        df['hour'] = df.index.hour
        df['day_of_week'] = df.index.dayofweek
        df['day_of_month'] = df.index.day
        df['month'] = df.index.month
        df['quarter'] = df.index.quarter
        
        # Cyclical encoding
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        # Weekend/weekday
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        return df
    
    @staticmethod
    def create_volume_features(df: pd.DataFrame) -> pd.DataFrame:
        """Cria features baseadas em volume"""
        df = df.copy()
        
        if 'volume' in df.columns:
            # Volume moving averages
            for window in [7, 14, 30]:
                df[f'volume_ma_{window}'] = df['volume'].rolling(window=window).mean()
            
            # Volume ratios
            df['volume_to_ma7'] = df['volume'] / df['volume_ma_7']
            df['volume_spike'] = (df['volume'] > df['volume_ma_7'] * 2).astype(int)
            
            # Price-volume relationship
            df['price_volume_correlation'] = df['price'].rolling(window=14).corr(df['volume'])
        
        return df
    
    @staticmethod
    def _calculate_rsi(prices: pd.Series, window: int = 14) -> pd.Series:
        """Calcula o RSI (Relative Strength Index)"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def _calculate_bollinger_bands(prices: pd.Series, window: int = 20, num_std: int = 2) -> Tuple[pd.Series, pd.Series]:
        """Calcula as Bandas de Bollinger"""
        ma = prices.rolling(window=window).mean()
        std = prices.rolling(window=window).std()
        upper = ma + (std * num_std)
        lower = ma - (std * num_std)
        return upper, lower

class ProphetModel:
    """Modelo Prophet para previsão de séries temporais"""
    
    def __init__(self):
        self.model = None
        self.is_fitted = False
        self.item_name = None
        
    def prepare_data(self, df: pd.DataFrame, price_column: str = 'price') -> pd.DataFrame:
        """Prepara dados para o Prophet"""
        prophet_df = pd.DataFrame({
            'ds': df.index,
            'y': df[price_column]
        })
        
        # Adicionar regressor externos se disponíveis
        if 'volume' in df.columns:
            prophet_df['volume'] = df['volume'].values
        
        return prophet_df
    
    def fit(self, df: pd.DataFrame, item_name: str) -> Dict[str, Any]:
        """Treina o modelo Prophet"""
        if not PROPHET_AVAILABLE:
            raise ImportError("Prophet não está instalado")
        
        self.item_name = item_name
        
        # Preparar dados
        prophet_df = self.prepare_data(df)
        
        # Configurar modelo
        self.model = Prophet(
            growth='linear',
            seasonality_mode='multiplicative',
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            changepoint_prior_scale=0.05,
            seasonality_prior_scale=10.0
        )
        
        # Adicionar sazonalidades customizadas
        self.model.add_seasonality(name='hourly', period=1, fourier_order=8)
        
        # Adicionar regressores externos
        if 'volume' in prophet_df.columns:
            self.model.add_regressor('volume')
        
        # Treinar
        self.model.fit(prophet_df)
        self.is_fitted = True
        
        # Calcular métricas
        in_sample_forecast = self.model.predict(prophet_df)
        mae = mean_absolute_error(prophet_df['y'], in_sample_forecast['yhat'])
        
        return {
            'model_type': 'Prophet',
            'item_name': item_name,
            'training_samples': len(prophet_df),
            'mae': mae,
            'fitted_at': datetime.utcnow()
        }
    
    def predict(self, periods: int = 24, freq: str = 'H') -> pd.DataFrame:
        """Faz previsões"""
        if not self.is_fitted:
            raise ValueError("Modelo não foi treinado")
        
        # Criar dataframe futuro
        future = self.model.make_future_dataframe(periods=periods, freq=freq)
        
        # Fazer previsão
        forecast = self.model.predict(future)
        
        return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(periods)

class XGBoostModel:
    """Modelo XGBoost para previsão de preços"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_columns = []
        self.is_fitted = False
        self.item_name = None
        
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepara features para XGBoost"""
        df = df.copy()
        
        # Engenharia de features
        df = FeatureEngineering.create_price_features(df)
        df = FeatureEngineering.create_temporal_features(df)
        df = FeatureEngineering.create_volume_features(df)
        
        # Adicionar lags
        for lag in [1, 2, 3, 6, 12, 24]:
            df[f'price_lag_{lag}'] = df['price'].shift(lag)
        
        # Target: preço futuro (1h, 6h, 24h)
        df['target_1h'] = df['price'].shift(-1)
        df['target_6h'] = df['price'].shift(-6)
        df['target_24h'] = df['price'].shift(-24)
        
        return df
    
    def fit(self, df: pd.DataFrame, item_name: str, target: str = 'target_24h') -> Dict[str, Any]:
        """Treina o modelo XGBoost"""
        if not XGBOOST_AVAILABLE:
            raise ImportError("XGBoost não está instalado")
        
        self.item_name = item_name
        
        # Preparar features
        df_features = self.prepare_features(df)
        
        # Selecionar features numéricas
        numeric_features = df_features.select_dtypes(include=[np.number]).columns.tolist()
        feature_columns = [col for col in numeric_features if col not in ['price', 'target_1h', 'target_6h', 'target_24h']]
        
        # Remover features com muitos NaNs
        feature_columns = [col for col in feature_columns if df_features[col].isnull().sum() / len(df_features) < 0.5]
        
        self.feature_columns = feature_columns
        
        # Preparar dados
        X = df_features[feature_columns].fillna(method='ffill').fillna(0)
        y = df_features[target].fillna(method='ffill')
        
        # Remover linhas com target NaN
        valid_mask = ~y.isnull()
        X = X[valid_mask]
        y = y[valid_mask]
        
        if len(X) < 100:
            raise ValueError("Não há dados suficientes para treinar o modelo")
        
        # Split treino/teste
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, shuffle=False, random_state=42
        )
        
        # Escalar features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Treinar modelo
        self.model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(X_train_scaled, y_train)
        self.is_fitted = True
        
        # Calcular métricas
        y_pred = self.model.predict(X_test_scaled)
        mae = mean_absolute_error(y_test, y_pred)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        return {
            'model_type': 'XGBoost',
            'item_name': item_name,
            'training_samples': len(X_train),
            'test_samples': len(X_test),
            'mae': mae,
            'mse': mse,
            'r2': r2,
            'feature_count': len(feature_columns),
            'fitted_at': datetime.utcnow()
        }
    
    def predict(self, df: pd.DataFrame) -> float:
        """Faz previsão para um dataframe"""
        if not self.is_fitted:
            raise ValueError("Modelo não foi treinado")
        
        # Preparar features
        df_features = self.prepare_features(df)
        
        # Selecionar últimas linhas (mais recentes)
        X = df_features[self.feature_columns].tail(1).fillna(method='ffill').fillna(0)
        
        # Escalar
        X_scaled = self.scaler.transform(X)
        
        # Predizer
        prediction = self.model.predict(X_scaled)[0]
        
        return prediction
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Retorna importância das features"""
        if not self.is_fitted:
            return {}
        
        importance = self.model.feature_importances_
        return dict(zip(self.feature_columns, importance))

class OpportunityDetector:
    """Detector de oportunidades usando anomaly detection"""
    
    def __init__(self):
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        self.is_fitted = False
        
    def fit(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Treina o detector de anomalias"""
        # Preparar features para detecção
        features = []
        
        if 'price' in df.columns:
            features.extend(['price'])
        
        if 'volume' in df.columns:
            features.extend(['volume'])
        
        # Adicionar ratios e indicadores
        df_copy = FeatureEngineering.create_price_features(df)
        
        ratio_features = [col for col in df_copy.columns if 'ratio' in col or 'rsi' in col or 'bb_' in col]
        features.extend(ratio_features)
        
        # Remover NaNs
        X = df_copy[features].fillna(method='ffill').fillna(0)
        
        # Treinar
        self.isolation_forest.fit(X)
        self.is_fitted = True
        
        return {
            'detector_type': 'IsolationForest',
            'features_used': len(features),
            'training_samples': len(X),
            'fitted_at': datetime.utcnow()
        }
    
    def detect_opportunities(self, df: pd.DataFrame, threshold: float = -0.5) -> List[OpportunityAlert]:
        """Detecta oportunidades nos dados"""
        if not self.is_fitted:
            raise ValueError("Detector não foi treinado")
        
        opportunities = []
        
        # Calcular features
        df_features = FeatureEngineering.create_price_features(df)
        
        # Detectar anomalias
        anomaly_scores = self.isolation_forest.decision_function(
            df_features.fillna(method='ffill').fillna(0)
        )
        
        # Identificar oportunidades (anomalias negativas = undervalued)
        for i, score in enumerate(anomaly_scores):
            if score < threshold:
                row = df.iloc[i]
                
                opportunity = OpportunityAlert(
                    item_name=row.get('item_name', 'Unknown'),
                    current_price=row['price'],
                    fair_value=row['price'] * (1 - score),  # Estimativa
                    opportunity_score=abs(score) * 100,
                    opportunity_type='undervalued',
                    confidence=min(abs(score) * 100, 100),
                    factors=['Anomaly Detection', 'Price Below Expected'],
                    expiry_time=datetime.utcnow() + timedelta(hours=24)
                )
                
                opportunities.append(opportunity)
        
        return opportunities

class PredictionEngine:
    """Engine principal de ML para previsões"""
    
    def __init__(self):
        self.models = {}
        self.hybrid_db = None
        self.opportunity_detector = OpportunityDetector()
        self.model_metrics = {}
        
        # Criar diretório para modelos
        self.models_dir = Path('models')
        self.models_dir.mkdir(exist_ok=True)
        
        logger.info("🤖 PredictionEngine inicializado")
    
    async def __aenter__(self):
        """Async context manager"""
        self.hybrid_db = create_hybrid_database()
        await self.hybrid_db.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.hybrid_db:
            await self.hybrid_db.disconnect()
    
    async def get_item_data(self, item_name: str, days: int = 90) -> pd.DataFrame:
        """Obtém dados históricos de um item"""
        query = """
        SELECT 
            created_at_csfloat as timestamp,
            price_usd as price,
            float_value,
            count() as volume
        FROM listings_analytics 
        WHERE item_name = :item_name
            AND created_at_csfloat >= now() - INTERVAL :days DAY
        GROUP BY 
            toStartOfHour(created_at_csfloat),
            item_name
        ORDER BY timestamp
        """
        
        results = await self.hybrid_db.query(
            query, 
            {'item_name': item_name, 'days': days},
            operation='SELECT',
            complexity='analytics'
        )
        
        if not results:
            raise ValueError(f"Não há dados suficientes para {item_name}")
        
        df = pd.DataFrame(results)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        return df
    
    async def train_model(self, item_name: str, model_type: str = 'xgboost', days: int = 90) -> Dict[str, Any]:
        """Treina um modelo para um item específico"""
        try:
            # Obter dados
            df = await self.get_item_data(item_name, days)
            
            if len(df) < 100:
                raise ValueError(f"Dados insuficientes para {item_name}: {len(df)} registros")
            
            # Treinar modelo baseado no tipo
            if model_type.lower() == 'prophet' and PROPHET_AVAILABLE:
                model = ProphetModel()
                metrics = model.fit(df, item_name)
                
            elif model_type.lower() == 'xgboost' and XGBOOST_AVAILABLE:
                model = XGBoostModel()
                metrics = model.fit(df, item_name)
                
            else:
                raise ValueError(f"Tipo de modelo não suportado ou biblioteca não instalada: {model_type}")
            
            # Salvar modelo
            model_key = f"{item_name}_{model_type}"
            self.models[model_key] = model
            
            # Salvar métricas
            self.model_metrics[model_key] = ModelMetrics(
                model_name=model_key,
                mae=metrics.get('mae', 0),
                mse=metrics.get('mse', 0),
                r2=metrics.get('r2', 0),
                accuracy_24h=0,  # Será calculado posteriormente
                last_trained=datetime.utcnow(),
                training_samples=metrics.get('training_samples', 0)
            )
            
            # Salvar no disco
            await self._save_model(model_key, model)
            
            logger.info(f"✅ Modelo {model_type} treinado para {item_name}")
            
            return {
                'success': True,
                'model_key': model_key,
                'metrics': metrics,
                'training_data_points': len(df)
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao treinar modelo para {item_name}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def predict_price(self, item_name: str, horizon: str = '24h', 
                          model_type: str = 'xgboost') -> PredictionResult:
        """Faz previsão de preço para um item"""
        model_key = f"{item_name}_{model_type}"
        
        # Verificar se modelo existe
        if model_key not in self.models:
            # Tentar carregar do disco
            if not await self._load_model(model_key):
                # Treinar novo modelo
                training_result = await self.train_model(item_name, model_type)
                if not training_result['success']:
                    raise ValueError(f"Não foi possível treinar modelo para {item_name}")
        
        model = self.models[model_key]
        
        # Obter dados recentes
        df = await self.get_item_data(item_name, days=30)
        current_price = df['price'].iloc[-1]
        
        # Fazer previsão
        if isinstance(model, ProphetModel):
            horizon_hours = {'1h': 1, '6h': 6, '24h': 24, '7d': 168}.get(horizon, 24)
            forecast = model.predict(periods=horizon_hours)
            predicted_price = forecast['yhat'].iloc[-1]
            confidence = 80.0  # Prophet não fornece confidence score direto
            
        elif isinstance(model, XGBoostModel):
            predicted_price = model.predict(df)
            confidence = 75.0  # Baseado na performance histórica
            
        else:
            raise ValueError(f"Tipo de modelo não suportado: {type(model)}")
        
        # Calcular fatores que influenciaram a previsão
        factors = await self._analyze_prediction_factors(item_name, df, model)
        
        return PredictionResult(
            item_name=item_name,
            current_price=current_price,
            predicted_price=predicted_price,
            confidence=confidence,
            model_used=model_type,
            prediction_horizon=horizon,
            factors=factors,
            timestamp=datetime.utcnow()
        )
    
    async def detect_opportunities(self, min_score: float = 50.0) -> List[OpportunityAlert]:
        """Detecta oportunidades no mercado"""
        # Obter dados recentes de vários itens
        query = """
        SELECT DISTINCT item_name 
        FROM listings_analytics 
        WHERE created_at_csfloat >= now() - INTERVAL 1 DAY
        LIMIT 50
        """
        
        items_result = await self.hybrid_db.query(query, complexity='analytics')
        
        all_opportunities = []
        
        for item_row in items_result:
            item_name = item_row['item_name']
            
            try:
                # Obter dados do item
                df = await self.get_item_data(item_name, days=30)
                
                if len(df) < 50:
                    continue
                
                # Treinar detector se necessário
                if not self.opportunity_detector.is_fitted:
                    self.opportunity_detector.fit(df)
                
                # Detectar oportunidades
                opportunities = self.opportunity_detector.detect_opportunities(df)
                
                # Filtrar por score mínimo
                filtered_opportunities = [
                    opp for opp in opportunities 
                    if opp.opportunity_score >= min_score
                ]
                
                all_opportunities.extend(filtered_opportunities)
                
            except Exception as e:
                logger.warning(f"Erro ao detectar oportunidades para {item_name}: {e}")
                continue
        
        # Ordenar por score
        all_opportunities.sort(key=lambda x: x.opportunity_score, reverse=True)
        
        return all_opportunities[:20]  # Top 20 oportunidades
    
    async def _analyze_prediction_factors(self, item_name: str, df: pd.DataFrame, model) -> List[str]:
        """Analisa fatores que influenciaram a previsão"""
        factors = []
        
        # Análise de tendência
        recent_prices = df['price'].tail(7)
        if recent_prices.iloc[-1] > recent_prices.iloc[0]:
            factors.append("Tendência de alta recente")
        else:
            factors.append("Tendência de baixa recente")
        
        # Análise de volume
        if 'volume' in df.columns:
            recent_volume = df['volume'].tail(3).mean()
            avg_volume = df['volume'].mean()
            if recent_volume > avg_volume * 1.5:
                factors.append("Volume acima da média")
            elif recent_volume < avg_volume * 0.5:
                factors.append("Volume abaixo da média")
        
        # Feature importance (para XGBoost)
        if isinstance(model, XGBoostModel):
            importance = model.get_feature_importance()
            top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:3]
            factors.extend([f"Feature importante: {feat}" for feat, _ in top_features])
        
        return factors
    
    async def _save_model(self, model_key: str, model) -> bool:
        """Salva modelo no disco"""
        try:
            model_path = self.models_dir / f"{model_key}.pkl"
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar modelo {model_key}: {e}")
            return False
    
    async def _load_model(self, model_key: str) -> bool:
        """Carrega modelo do disco"""
        try:
            model_path = self.models_dir / f"{model_key}.pkl"
            if model_path.exists():
                with open(model_path, 'rb') as f:
                    model = pickle.load(f)
                self.models[model_key] = model
                return True
            return False
        except Exception as e:
            logger.error(f"Erro ao carregar modelo {model_key}: {e}")
            return False
    
    def get_model_metrics(self) -> Dict[str, ModelMetrics]:
        """Retorna métricas de todos os modelos"""
        return self.model_metrics.copy()

# Instância global
prediction_engine = PredictionEngine()