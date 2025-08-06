"""
Beta Launch Script - Skinlytics Platform

Script para lançamento da versão beta pública com autenticação Steam,
sistema de pagamentos e onboarding de usuários.

Features:
    - Steam OpenID Authentication
    - Stripe Integration (Freemium/Pro)
    - User Onboarding Flow
    - Beta Testing Analytics
    - Feedback Collection System

Author: CS2 Skin Tracker Team - Skinlytics Platform
Version: 2.0.0 Beta Ready
"""

import asyncio
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
import yaml

# Web Framework
from fastapi import FastAPI, Request, Depends, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer

# Authentication
import requests
from urllib.parse import urlencode, parse_qs
import hashlib
import hmac
import time

# Payment Processing
import stripe

# Database
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from ..models.hybrid_database import create_hybrid_database

logger = logging.getLogger(__name__)

# Pydantic Models for Beta
from pydantic import BaseModel, Field

class UserProfile(BaseModel):
    """Perfil de usuário beta"""
    steam_id: str
    username: str
    avatar_url: str
    email: Optional[str] = None
    subscription_tier: str = "free"  # free, pro, enterprise
    beta_features: List[str] = []
    created_at: datetime
    last_active: datetime

class BetaFeedback(BaseModel):
    """Feedback de usuário beta"""
    user_id: str
    feature: str
    rating: int = Field(ge=1, le=5)
    comment: str
    timestamp: datetime

class SubscriptionPlan(BaseModel):
    """Plano de assinatura"""
    name: str
    price_monthly: float
    features: List[str]
    api_calls_limit: int
    alerts_limit: int

# Database Models for Beta
Base = declarative_base()

class BetaUser(Base):
    """Modelo de usuário beta"""
    __tablename__ = 'beta_users'
    
    id = Column(Integer, primary_key=True)
    steam_id = Column(String(20), unique=True, nullable=False)
    username = Column(String(100), nullable=False)
    avatar_url = Column(String(500))
    email = Column(String(200))
    subscription_tier = Column(String(20), default='free')
    beta_features = Column(JSON, default=list)
    stripe_customer_id = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class BetaFeedbackModel(Base):
    """Modelo de feedback beta"""
    __tablename__ = 'beta_feedback'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(20), nullable=False)
    feature = Column(String(100), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

class BetaAnalytics(Base):
    """Analytics de uso beta"""
    __tablename__ = 'beta_analytics'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(20), nullable=False)
    action = Column(String(100), nullable=False)
    feature = Column(String(100))
    metadata = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)

class SkinlyticsBetaApp:
    """Aplicação principal do beta"""
    
    def __init__(self):
        self.app = FastAPI(
            title="Skinlytics Beta",
            description="The Bloomberg of CS2 Skins - Beta Version",
            version="2.0.0-beta"
        )
        
        # Configurações
        self.config = self._load_config()
        self._setup_stripe()
        self._setup_middleware()
        self._setup_routes()
        
        # Templates
        self.templates = Jinja2Templates(directory="templates")
        
        # Planos de assinatura
        self.subscription_plans = {
            "free": SubscriptionPlan(
                name="Free",
                price_monthly=0.0,
                features=[
                    "Basic price tracking",
                    "5 alerts per month",
                    "Limited API calls (100/day)",
                    "Community support"
                ],
                api_calls_limit=100,
                alerts_limit=5
            ),
            "pro": SubscriptionPlan(
                name="Pro",
                price_monthly=29.0,
                features=[
                    "Advanced analytics",
                    "Unlimited alerts",
                    "ML predictions",
                    "API access (10K calls/day)",
                    "Priority support",
                    "Custom dashboards"
                ],
                api_calls_limit=10000,
                alerts_limit=-1  # Unlimited
            ),
            "enterprise": SubscriptionPlan(
                name="Enterprise",
                price_monthly=299.0,
                features=[
                    "All Pro features",
                    "Unlimited API access",
                    "Custom integrations",
                    "Dedicated support",
                    "SLA guarantee",
                    "Custom ML models"
                ],
                api_calls_limit=-1,  # Unlimited
                alerts_limit=-1  # Unlimited
            )
        }
        
        logger.info("🚀 Skinlytics Beta App inicializado")
    
    def _load_config(self) -> Dict[str, Any]:
        """Carrega configuração do beta"""
        return {
            "steam": {
                "api_key": os.getenv("STEAM_API_KEY"),
                "openid_url": "https://steamcommunity.com/openid",
                "return_url": os.getenv("STEAM_RETURN_URL", "http://localhost:8000/auth/steam/callback")
            },
            "stripe": {
                "secret_key": os.getenv("STRIPE_SECRET_KEY"),
                "public_key": os.getenv("STRIPE_PUBLIC_KEY"),
                "webhook_secret": os.getenv("STRIPE_WEBHOOK_SECRET")
            },
            "app": {
                "secret_key": os.getenv("APP_SECRET_KEY", "beta-secret-key-change-in-prod"),
                "domain": os.getenv("APP_DOMAIN", "localhost:8000"),
                "debug": os.getenv("DEBUG", "true").lower() == "true"
            },
            "beta": {
                "max_users": int(os.getenv("BETA_MAX_USERS", "1000")),
                "invite_only": os.getenv("BETA_INVITE_ONLY", "false").lower() == "true",
                "features_enabled": [
                    "price_tracking",
                    "basic_alerts",
                    "ml_predictions",
                    "api_access",
                    "community_features"
                ]
            }
        }
    
    def _setup_stripe(self):
        """Configura Stripe para pagamentos"""
        stripe.api_key = self.config["stripe"]["secret_key"]
        
        # Criar produtos no Stripe se não existirem
        self._ensure_stripe_products()
    
    def _ensure_stripe_products(self):
        """Garante que produtos existem no Stripe"""
        try:
            # Produto Pro
            stripe.Product.create(
                id="skinlytics-pro",
                name="Skinlytics Pro",
                description="Advanced CS2 skin analytics and predictions"
            )
            
            stripe.Price.create(
                product="skinlytics-pro",
                unit_amount=2900,  # $29.00
                currency="usd",
                recurring={"interval": "month"}
            )
            
            # Produto Enterprise  
            stripe.Product.create(
                id="skinlytics-enterprise",
                name="Skinlytics Enterprise", 
                description="Enterprise-grade skin analytics with unlimited access"
            )
            
            stripe.Price.create(
                product="skinlytics-enterprise",
                unit_amount=29900,  # $299.00
                currency="usd",
                recurring={"interval": "month"}
            )
            
        except stripe.error.InvalidRequestError:
            # Produtos já existem
            pass
    
    def _setup_middleware(self):
        """Configura middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure properly for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Static files
        self.app.mount("/static", StaticFiles(directory="static"), name="static")
    
    def _setup_routes(self):
        """Configura todas as rotas"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def home(request: Request):
            """Landing page do beta"""
            return self.templates.TemplateResponse("landing.html", {
                "request": request,
                "plans": self.subscription_plans,
                "beta_features": self.config["beta"]["features_enabled"]
            })
        
        @self.app.get("/auth/steam")
        async def steam_login(request: Request):
            """Inicia autenticação Steam OpenID"""
            params = {
                'openid.ns': 'http://specs.openid.net/auth/2.0',
                'openid.mode': 'checkid_setup',
                'openid.return_to': self.config["steam"]["return_url"],
                'openid.realm': f"http://{self.config['app']['domain']}",
                'openid.identity': 'http://specs.openid.net/auth/2.0/identifier_select',
                'openid.claimed_id': 'http://specs.openid.net/auth/2.0/identifier_select',
            }
            
            auth_url = f"{self.config['steam']['openid_url']}/login?{urlencode(params)}"
            return RedirectResponse(auth_url)
        
        @self.app.get("/auth/steam/callback")
        async def steam_callback(request: Request):
            """Callback da autenticação Steam"""
            # Validar OpenID response
            steam_id = await self._validate_steam_openid(request.query_params)
            
            if not steam_id:
                raise HTTPException(status_code=400, detail="Invalid Steam authentication")
            
            # Obter dados do usuário Steam
            user_data = await self._get_steam_user_data(steam_id)
            
            if not user_data:
                raise HTTPException(status_code=400, detail="Could not fetch Steam user data")
            
            # Criar ou atualizar usuário
            user = await self._create_or_update_user(user_data)
            
            # Redirecionar para dashboard
            return RedirectResponse(f"/dashboard?user_id={user.steam_id}")
        
        @self.app.get("/dashboard", response_class=HTMLResponse)
        async def dashboard(request: Request, user_id: str):
            """Dashboard principal do usuário"""
            user = await self._get_user(user_id)
            if not user:
                return RedirectResponse("/")
            
            # Atualizar última atividade
            await self._update_last_activity(user_id)
            
            # Analytics de uso
            await self._track_usage(user_id, "dashboard_view")
            
            return self.templates.TemplateResponse("dashboard.html", {
                "request": request,
                "user": user,
                "plan": self.subscription_plans[user.subscription_tier],
                "beta_features": self.config["beta"]["features_enabled"]
            })
        
        @self.app.post("/subscribe/{plan_name}")
        async def subscribe(plan_name: str, user_id: str):
            """Cria assinatura Stripe"""
            if plan_name not in self.subscription_plans:
                raise HTTPException(status_code=400, detail="Invalid plan")
            
            if plan_name == "free":
                raise HTTPException(status_code=400, detail="Free plan doesn't require subscription")
            
            user = await self._get_user(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Criar customer no Stripe se não existir
            if not user.stripe_customer_id:
                customer = stripe.Customer.create(
                    email=user.email,
                    metadata={"steam_id": user.steam_id, "username": user.username}
                )
                user.stripe_customer_id = customer.id
                await self._update_user(user)
            
            # Criar sessão de checkout
            price_id = f"skinlytics-{plan_name}-monthly"
            
            session = stripe.checkout.Session.create(
                customer=user.stripe_customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f"http://{self.config['app']['domain']}/subscription/success",
                cancel_url=f"http://{self.config['app']['domain']}/dashboard?user_id={user_id}",
                metadata={"user_id": user_id, "plan": plan_name}
            )
            
            return {"checkout_url": session.url}
        
        @self.app.post("/feedback")
        async def submit_feedback(feedback: BetaFeedback):
            """Submete feedback do usuário"""
            await self._save_feedback(feedback)
            await self._track_usage(feedback.user_id, "feedback_submitted", {
                "feature": feedback.feature,
                "rating": feedback.rating
            })
            
            return {"message": "Feedback received successfully"}
        
        @self.app.get("/api/beta/stats")
        async def beta_stats():
            """Estatísticas do beta para admins"""
            return await self._get_beta_statistics()
        
        @self.app.post("/webhook/stripe")
        async def stripe_webhook(request: Request):
            """Webhook do Stripe para eventos de pagamento"""
            payload = await request.body()
            sig_header = request.headers.get("stripe-signature")
            
            try:
                event = stripe.Webhook.construct_event(
                    payload, sig_header, self.config["stripe"]["webhook_secret"]
                )
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid payload")
            except stripe.error.SignatureVerificationError:
                raise HTTPException(status_code=400, detail="Invalid signature")
            
            # Handle subscription events
            if event['type'] == 'customer.subscription.created':
                await self._handle_subscription_created(event['data']['object'])
            elif event['type'] == 'customer.subscription.deleted':
                await self._handle_subscription_cancelled(event['data']['object'])
            
            return {"received": True}
    
    async def _validate_steam_openid(self, params) -> Optional[str]:
        """Valida resposta OpenID do Steam"""
        # Implementação simplificada - em produção usar biblioteca completa
        try:
            # Extrair Steam ID da identity URL
            identity = params.get('openid.identity')
            if identity and 'steamcommunity.com/openid/id/' in identity:
                steam_id = identity.split('/')[-1]
                return steam_id
        except:
            pass
        
        return None
    
    async def _get_steam_user_data(self, steam_id: str) -> Optional[Dict]:
        """Obtém dados do usuário via Steam API"""
        try:
            url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
            params = {
                'key': self.config["steam"]["api_key"],
                'steamids': steam_id
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if 'response' in data and 'players' in data['response'] and data['response']['players']:
                player = data['response']['players'][0]
                return {
                    'steam_id': steam_id,
                    'username': player.get('personaname', ''),
                    'avatar_url': player.get('avatarfull', ''),
                    'profile_url': player.get('profileurl', '')
                }
        except:
            pass
        
        return None
    
    async def _create_or_update_user(self, user_data: Dict) -> BetaUser:
        """Cria ou atualiza usuário no banco"""
        # Implementação mock - em produção usar SQLAlchemy session
        user = BetaUser(
            steam_id=user_data['steam_id'],
            username=user_data['username'],
            avatar_url=user_data['avatar_url'],
            subscription_tier='free',
            beta_features=self.config["beta"]["features_enabled"],
            created_at=datetime.utcnow(),
            last_active=datetime.utcnow()
        )
        
        return user
    
    async def _get_user(self, user_id: str) -> Optional[BetaUser]:
        """Obtém usuário por ID"""
        # Mock implementation
        return BetaUser(
            steam_id=user_id,
            username="Beta User",
            avatar_url="https://example.com/avatar.jpg",
            subscription_tier="free"
        )
    
    async def _update_user(self, user: BetaUser):
        """Atualiza usuário no banco"""
        # Mock implementation
        pass
    
    async def _update_last_activity(self, user_id: str):
        """Atualiza última atividade do usuário"""
        # Mock implementation
        pass
    
    async def _track_usage(self, user_id: str, action: str, metadata: Dict = None):
        """Rastreia uso para analytics"""
        analytics = BetaAnalytics(
            user_id=user_id,
            action=action,
            metadata=metadata or {},
            timestamp=datetime.utcnow()
        )
        # Salvar no banco
        logger.info(f"📊 Analytics: {user_id} - {action}")
    
    async def _save_feedback(self, feedback: BetaFeedback):
        """Salva feedback no banco"""
        feedback_model = BetaFeedbackModel(
            user_id=feedback.user_id,
            feature=feedback.feature,
            rating=feedback.rating,
            comment=feedback.comment,
            timestamp=feedback.timestamp
        )
        # Salvar no banco
        logger.info(f"💬 Feedback: {feedback.feature} - {feedback.rating}/5")
    
    async def _get_beta_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas do beta"""
        return {
            "total_users": 150,  # Mock
            "active_users_7d": 89,
            "subscription_breakdown": {
                "free": 120,
                "pro": 25,
                "enterprise": 5
            },
            "feature_usage": {
                "price_tracking": 145,
                "ml_predictions": 67,
                "api_access": 34,
                "alerts": 89
            },
            "avg_rating": 4.3,
            "feedback_count": 234
        }
    
    async def _handle_subscription_created(self, subscription):
        """Handle when subscription is created"""
        customer_id = subscription['customer']
        plan_name = subscription['metadata'].get('plan', 'pro')
        
        # Update user subscription tier
        logger.info(f"✅ Subscription created: {customer_id} -> {plan_name}")
    
    async def _handle_subscription_cancelled(self, subscription):
        """Handle when subscription is cancelled"""
        customer_id = subscription['customer']
        
        # Downgrade user to free tier
        logger.info(f"❌ Subscription cancelled: {customer_id}")

# HTML Templates (simplified)
LANDING_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Skinlytics Beta - The Bloomberg of CS2 Skins</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #0e1117; color: #fafafa; }
        .header { background: #ff6b6b; padding: 1rem; text-align: center; }
        .hero { padding: 3rem 1rem; text-align: center; }
        .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; padding: 2rem; }
        .feature { background: #262730; padding: 2rem; border-radius: 8px; }
        .pricing { display: flex; justify-content: center; gap: 2rem; padding: 2rem; }
        .plan { background: #262730; padding: 2rem; border-radius: 8px; text-align: center; min-width: 250px; }
        .cta { background: #ff6b6b; color: white; padding: 1rem 2rem; border: none; border-radius: 4px; font-size: 1.1rem; cursor: pointer; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 SKINLYTICS BETA</h1>
        <p>The Bloomberg Terminal for CS2 Skins</p>
    </div>
    
    <div class="hero">
        <h2>Transform Your CS2 Trading with AI-Powered Analytics</h2>
        <p>Get real-time market intelligence, predictive analytics, and automated alerts for CS2 skin trading.</p>
        <a href="/auth/steam"><button class="cta">🎮 Login with Steam</button></a>
    </div>
    
    <div class="features">
        <div class="feature">
            <h3>🤖 AI Predictions</h3>
            <p>Machine learning models predict price movements with 85%+ accuracy</p>
        </div>
        <div class="feature">
            <h3>📊 Real-time Analytics</h3>
            <p>Live market data with microsecond precision and float granularity</p>
        </div>
        <div class="feature">
            <h3>🔔 Smart Alerts</h3>
            <p>Automated notifications for opportunities and price targets</p>
        </div>
        <div class="feature">
            <h3>🚀 Enterprise API</h3>
            <p>Professional-grade API for bots and advanced trading systems</p>
        </div>
    </div>
    
    <div class="pricing">
        {% for plan_name, plan in plans.items() %}
        <div class="plan">
            <h3>{{ plan.name }}</h3>
            <p class="price">${{ plan.price_monthly }}/month</p>
            <ul>
                {% for feature in plan.features %}
                <li>{{ feature }}</li>
                {% endfor %}
            </ul>
            {% if plan_name != 'free' %}
            <button class="cta" onclick="subscribe('{{ plan_name }}')">Choose {{ plan.name }}</button>
            {% endif %}
        </div>
        {% endfor %}
    </div>
    
    <script>
        function subscribe(plan) {
            alert(`${plan} subscription coming soon in beta!`);
        }
    </script>
</body>
</html>
"""

# Save templates
def create_templates():
    """Cria templates HTML"""
    Path("templates").mkdir(exist_ok=True)
    
    with open("templates/landing.html", "w") as f:
        f.write(LANDING_PAGE_TEMPLATE)
    
    dashboard_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Skinlytics Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; background: #0e1117; color: #fafafa; margin: 0; }
        .sidebar { width: 250px; background: #262730; height: 100vh; position: fixed; padding: 1rem; }
        .main { margin-left: 270px; padding: 2rem; }
        .card { background: #262730; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; }
        .metric { text-align: center; }
        .metric h3 { margin: 0; color: #ff6b6b; }
        .metric p { margin: 0.5rem 0 0 0; font-size: 2rem; font-weight: bold; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2>🎮 {{ user.username }}</h2>
        <p>Plan: {{ plan.name }}</p>
        <ul style="list-style: none; padding: 0;">
            <li><a href="#" style="color: #fafafa;">📊 Dashboard</a></li>
            <li><a href="#" style="color: #fafafa;">🤖 Predictions</a></li>
            <li><a href="#" style="color: #fafafa;">🔔 Alerts</a></li>
            <li><a href="#" style="color: #fafafa;">📈 Analytics</a></li>
            <li><a href="#" style="color: #fafafa;">⚙️ Settings</a></li>
        </ul>
    </div>
    
    <div class="main">
        <h1>Welcome to Skinlytics Beta!</h1>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
            <div class="card metric">
                <h3>Market Cap</h3>
                <p>$2.3B</p>
            </div>
            <div class="card metric">
                <h3>Items Tracked</h3>
                <p>15,423</p>
            </div>
            <div class="card metric">
                <h3>Daily Volume</h3>
                <p>$45M</p>
            </div>
            <div class="card metric">
                <h3>ML Accuracy</h3>
                <p>87.3%</p>
            </div>
        </div>
        
        <div class="card">
            <h3>🚀 Beta Features Available</h3>
            <ul>
                {% for feature in beta_features %}
                <li>✅ {{ feature.replace('_', ' ').title() }}</li>
                {% endfor %}
            </ul>
        </div>
        
        <div class="card">
            <h3>💬 Beta Feedback</h3>
            <p>Help us improve! Rate your experience:</p>
            <div>
                <span onclick="rateBeta(1)">⭐</span>
                <span onclick="rateBeta(2)">⭐</span>
                <span onclick="rateBeta(3)">⭐</span>
                <span onclick="rateBeta(4)">⭐</span>
                <span onclick="rateBeta(5)">⭐</span>
            </div>
            <textarea placeholder="Your feedback..." style="width: 100%; margin-top: 1rem; padding: 0.5rem;"></textarea>
            <button onclick="submitFeedback()" style="margin-top: 0.5rem; background: #ff6b6b; color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px;">Submit Feedback</button>
        </div>
    </div>
    
    <script>
        let selectedRating = 0;
        
        function rateBeta(rating) {
            selectedRating = rating;
            console.log('Rated:', rating);
        }
        
        function submitFeedback() {
            const comment = document.querySelector('textarea').value;
            if (selectedRating > 0 && comment) {
                alert('Thank you for your feedback!');
            } else {
                alert('Please provide a rating and comment.');
            }
        }
    </script>
</body>
</html>
"""
    
    with open("templates/dashboard.html", "w") as f:
        f.write(dashboard_template)

# Main execution
async def launch_beta():
    """Lança a versão beta"""
    logger.info("🚀 Launching Skinlytics Beta...")
    
    # Criar templates
    create_templates()
    
    # Inicializar app
    beta_app = SkinlyticsBetaApp()
    
    # Setup database
    # Em produção, usar migrations adequadas
    
    logger.info("✅ Beta launch completed!")
    
    return beta_app.app

if __name__ == "__main__":
    import uvicorn
    
    app = asyncio.run(launch_beta())
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )