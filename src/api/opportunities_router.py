"""
Opportunities API Router

API endpoints para detecção de oportunidades, alertas de preço
e integração com sistema de notificações.

Features:
    - Detecção de oportunidades em tempo real
    - Configuração de alertas personalizados
    - Histórico de oportunidades
    - Análise de performance dos alertas
    - Integração com ML predictions

Author: CS2 Skin Tracker Team - Skinlytics Platform
Version: 2.0.0
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from ..ml.prediction_engine import prediction_engine, PredictionResult, OpportunityAlert
from ..services.notification_service import notification_service
from ..models.hybrid_database import create_hybrid_database

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer(auto_error=False)

router = APIRouter(
    prefix="/api/opportunities",
    tags=["opportunities"],
    responses={404: {"description": "Not found"}}
)

# Pydantic Models
class AlertRequest(BaseModel):
    """Request para criar alerta de preço"""
    item_name: str = Field(..., description="Nome do item")
    target_price: Optional[float] = Field(None, description="Preço alvo")
    min_price: Optional[float] = Field(None, description="Preço mínimo")
    max_price: Optional[float] = Field(None, description="Preço máximo")
    min_float: Optional[float] = Field(None, description="Float mínimo")
    max_float: Optional[float] = Field(None, description="Float máximo")
    notification_channels: List[str] = Field(default=["telegram"], description="Canais de notificação")
    user_id: Optional[str] = Field(None, description="ID do usuário")
    telegram_chat_id: Optional[str] = Field(None, description="Chat ID do Telegram")
    email: Optional[str] = Field(None, description="Email para notificações")

class PredictionRequest(BaseModel):
    """Request para previsão de preço"""
    item_name: str = Field(..., description="Nome do item")
    horizon: str = Field(default="24h", description="Horizonte de previsão")
    model_type: str = Field(default="xgboost", description="Tipo de modelo")

class OpportunityResponse(BaseModel):
    """Response de oportunidade detectada"""
    item_name: str
    current_price: float
    fair_value: float
    opportunity_score: float
    opportunity_type: str
    confidence: float
    factors: List[str]
    expiry_time: datetime
    listing_url: Optional[str] = None

class PredictionResponse(BaseModel):
    """Response de previsão"""
    item_name: str
    current_price: float
    predicted_price: float
    confidence: float
    model_used: str
    prediction_horizon: str
    factors: List[str]
    timestamp: datetime
    price_change_pct: float
    recommendation: str

class AlertResponse(BaseModel):
    """Response de alerta criado"""
    alert_id: str
    status: str
    message: str
    channels_configured: List[str]

# Dependency para autenticação
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verifica autenticação do usuário"""
    if not credentials:
        return None
    
    # Aqui você implementaria a verificação do token
    # Por enquanto, retornamos um usuário mock
    return {"user_id": "user_123", "email": "user@example.com"}

@router.get("/detect", response_model=List[OpportunityResponse])
async def detect_opportunities(
    min_score: float = Query(default=50.0, ge=0, le=100, description="Score mínimo da oportunidade"),
    limit: int = Query(default=20, ge=1, le=100, description="Número máximo de oportunidades"),
    category: Optional[str] = Query(default=None, description="Categoria de items (knife, rifle, etc.)"),
    max_price: Optional[float] = Query(default=None, description="Preço máximo"),
    current_user: dict = Depends(get_current_user)
):
    """
    🔍 Detecta oportunidades no mercado usando ML
    
    Analisa o mercado em tempo real para encontrar items:
    - Subvalorizados (preço abaixo do valor justo)
    - Com alta probabilidade de valorização
    - Com padrões anômalos de preço/volume
    """
    try:
        async with prediction_engine as engine:
            # Detectar oportunidades
            opportunities = await engine.detect_opportunities(min_score=min_score)
            
            # Filtrar por critérios
            if max_price:
                opportunities = [opp for opp in opportunities if opp.current_price <= max_price]
            
            if category:
                opportunities = [opp for opp in opportunities if category.lower() in opp.item_name.lower()]
            
            # Limitar resultados
            opportunities = opportunities[:limit]
            
            # Converter para response
            responses = []
            for opp in opportunities:
                # Gerar URL do listing (mock)
                listing_url = f"https://csfloat.com/search?name={opp.item_name.replace(' ', '%20')}"
                
                responses.append(OpportunityResponse(
                    item_name=opp.item_name,
                    current_price=opp.current_price,
                    fair_value=opp.fair_value,
                    opportunity_score=opp.opportunity_score,
                    opportunity_type=opp.opportunity_type,
                    confidence=opp.confidence,
                    factors=opp.factors,
                    expiry_time=opp.expiry_time,
                    listing_url=listing_url
                ))
            
            logger.info(f"🔍 Detectadas {len(responses)} oportunidades para usuário {current_user}")
            
            return responses
            
    except Exception as e:
        logger.error(f"❌ Erro ao detectar oportunidades: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.post("/predict", response_model=PredictionResponse)
async def predict_price(
    request: PredictionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    🤖 Faz previsão de preço usando modelos de ML
    
    Utiliza modelos treinados (Prophet, XGBoost, LSTM) para prever:
    - Preço em diferentes horizontes temporais
    - Confiança da previsão
    - Fatores que influenciam o preço
    - Recomendação (comprar/vender/aguardar)
    """
    try:
        async with prediction_engine as engine:
            # Fazer previsão
            prediction = await engine.predict_price(
                item_name=request.item_name,
                horizon=request.horizon,
                model_type=request.model_type
            )
            
            # Calcular variação percentual
            price_change_pct = ((prediction.predicted_price - prediction.current_price) / prediction.current_price) * 100
            
            # Gerar recomendação
            if price_change_pct > 10 and prediction.confidence > 70:
                recommendation = "🚀 COMPRAR - Alta probabilidade de valorização"
            elif price_change_pct < -10 and prediction.confidence > 70:
                recommendation = "📉 VENDER - Alta probabilidade de desvalorização"
            elif abs(price_change_pct) < 5:
                recommendation = "⏳ AGUARDAR - Preço estável previsto"
            else:
                recommendation = "🤔 ANALISAR - Sinal incerto, aguardar mais dados"
            
            response = PredictionResponse(
                item_name=prediction.item_name,
                current_price=prediction.current_price,
                predicted_price=prediction.predicted_price,
                confidence=prediction.confidence,
                model_used=prediction.model_used,
                prediction_horizon=prediction.prediction_horizon,
                factors=prediction.factors,
                timestamp=prediction.timestamp,
                price_change_pct=round(price_change_pct, 2),
                recommendation=recommendation
            )
            
            logger.info(f"🤖 Previsão realizada para {request.item_name}: {price_change_pct:.2f}%")
            
            return response
            
    except Exception as e:
        logger.error(f"❌ Erro na previsão de {request.item_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na previsão: {str(e)}")

@router.post("/alerts", response_model=AlertResponse)
async def create_alert(
    alert_request: AlertRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    🔔 Cria alerta personalizado de preço
    
    Configura monitoramento automático que notifica quando:
    - Preço atingir valor específico
    - Item entrar em faixa de preço
    - Float estiver dentro do range desejado
    - Oportunidade for detectada pelo ML
    """
    try:
        # Gerar ID único para o alerta
        alert_id = f"alert_{alert_request.item_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Salvar alerta no banco (seria implementado com uma tabela específica)
        # Por enquanto, apenas loggar
        logger.info(f"🔔 Alerta criado: {alert_id} para {alert_request.item_name}")
        
        # Configurar monitoramento em background
        background_tasks.add_task(
            monitor_alert,
            alert_id,
            alert_request,
            current_user
        )
        
        return AlertResponse(
            alert_id=alert_id,
            status="active",
            message=f"Alerta criado para {alert_request.item_name}",
            channels_configured=alert_request.notification_channels
        )
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar alerta: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao criar alerta: {str(e)}")

@router.get("/alerts/{alert_id}")
async def get_alert_status(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    📊 Consulta status de um alerta específico
    
    Retorna informações sobre:
    - Status atual do alerta
    - Número de notificações enviadas
    - Última verificação
    - Performance do alerta
    """
    # Implementação seria buscar no banco de dados
    return {
        "alert_id": alert_id,
        "status": "active",
        "created_at": "2024-01-01T00:00:00Z",
        "checks_performed": 1250,
        "notifications_sent": 3,
        "last_check": datetime.utcnow().isoformat(),
        "success_rate": 95.2
    }

@router.get("/history")
async def get_opportunities_history(
    days: int = Query(default=7, ge=1, le=30, description="Dias de histórico"),
    current_user: dict = Depends(get_current_user)
):
    """
    📈 Histórico de oportunidades detectadas
    
    Retorna:
    - Oportunidades dos últimos N dias
    - Performance das detecções
    - Estatísticas de acerto
    - Melhores categorias/items
    """
    try:
        hybrid_db = create_hybrid_database()
        async with hybrid_db:
            # Query para histórico (seria uma tabela específica)
            query = """
            SELECT 
                item_name,
                avg(price_usd) as avg_price,
                count() as listings_count,
                min(price_usd) as min_price,
                max(price_usd) as max_price
            FROM listings_analytics 
            WHERE created_at_csfloat >= now() - INTERVAL :days DAY
            GROUP BY item_name
            ORDER BY listings_count DESC
            LIMIT 50
            """
            
            results = await hybrid_db.query(
                query,
                {"days": days},
                operation='SELECT',
                complexity='analytics'
            )
            
            return {
                "period_days": days,
                "opportunities_found": len(results),
                "top_items": results[:10],
                "summary": {
                    "total_items_analyzed": len(results),
                    "avg_opportunities_per_day": len(results) / days,
                    "success_rate": 85.5  # Mock
                }
            }
            
    except Exception as e:
        logger.error(f"❌ Erro ao buscar histórico: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar histórico: {str(e)}")

@router.get("/stats")
async def get_ml_stats(current_user: dict = Depends(get_current_user)):
    """
    📊 Estatísticas dos modelos de ML
    
    Retorna:
    - Performance dos modelos
    - Acurácia das previsões
    - Modelos disponíveis
    - Últimos treinos realizados
    """
    try:
        async with prediction_engine as engine:
            metrics = engine.get_model_metrics()
            
            stats = {
                "models_count": len(metrics),
                "models": [],
                "overall_performance": {
                    "avg_accuracy": 0,
                    "total_predictions": 0,
                    "successful_alerts": 0
                }
            }
            
            total_accuracy = 0
            for model_key, metric in metrics.items():
                model_info = {
                    "model_name": metric.model_name,
                    "mae": round(metric.mae, 4),
                    "r2_score": round(metric.r2, 4),
                    "training_samples": metric.training_samples,
                    "last_trained": metric.last_trained.isoformat(),
                    "accuracy_24h": round(metric.accuracy_24h, 2)
                }
                stats["models"].append(model_info)
                total_accuracy += metric.accuracy_24h
            
            if len(metrics) > 0:
                stats["overall_performance"]["avg_accuracy"] = round(total_accuracy / len(metrics), 2)
            
            return stats
            
    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas ML: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")

# Background task para monitoramento de alertas
async def monitor_alert(alert_id: str, alert_request: AlertRequest, user: dict):
    """Monitora um alerta em background"""
    try:
        logger.info(f"🔄 Iniciando monitoramento do alerta {alert_id}")
        
        # Simular verificação de preço atual
        # Em implementação real, buscaria dados atuais do item
        
        # Se condições do alerta forem atendidas, enviar notificação
        async with notification_service as notif_service:
            await notif_service.send_price_alert(
                item_name=alert_request.item_name,
                current_price=100.0,  # Mock
                target_price=alert_request.target_price or 90.0,
                float_value=0.05,  # Mock
                listing_url="https://csfloat.com/item/123",
                user_id=user.get("user_id"),
                telegram_chat_id=alert_request.telegram_chat_id,
                email=alert_request.email
            )
        
        logger.info(f"✅ Alerta {alert_id} processado com sucesso")
        
    except Exception as e:
        logger.error(f"❌ Erro no monitoramento do alerta {alert_id}: {e}")

# Endpoints para testes e desenvolvimento
@router.get("/test/notification")
async def test_notification(
    channel: str = Query(default="telegram", description="Canal de teste"),
    current_user: dict = Depends(get_current_user)
):
    """🧪 Testa envio de notificação"""
    try:
        async with notification_service as notif_service:
            if channel == "telegram":
                result = await notif_service.send_best_deal(
                    item_name="AK-47 | Redline (Field-Tested)",
                    price=45.50,
                    market_price=52.00,
                    seller_name="ProTrader123",
                    seller_rating=98.5,
                    listing_url="https://csfloat.com/item/test",
                    user_id=current_user.get("user_id") if current_user else None
                )
            else:
                result = {"success": False, "error": "Canal não suportado para teste"}
        
        return {"test_result": result}
        
    except Exception as e:
        return {"error": str(e)}

@router.post("/test/train-model")
async def test_train_model(
    item_name: str = Query(..., description="Nome do item para treinar"),
    model_type: str = Query(default="xgboost", description="Tipo do modelo"),
    current_user: dict = Depends(get_current_user)
):
    """🧪 Testa treinamento de modelo ML"""
    try:
        async with prediction_engine as engine:
            result = await engine.train_model(item_name, model_type)
        
        return {"training_result": result}
        
    except Exception as e:
        return {"error": str(e)}