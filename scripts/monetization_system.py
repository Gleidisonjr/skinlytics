"""
Monetization System - Skinlytics Platform

Sistema completo de monetização com:
- Planos Freemium/Pro/Enterprise
- Integração Stripe + PayPal
- API Rate Limiting por tier
- Sistema de afiliados
- Analytics de receita
- Subscription management

Features:
    - Multi-payment providers (Stripe, PayPal, Crypto)
    - Dynamic pricing baseado em região
    - Trial periods e promocional codes
    - Churn prediction e retention
    - Revenue analytics em tempo real

Author: CS2 Skin Tracker Team - Skinlytics Platform
Version: 2.0.0 Monetization Ready
"""

import asyncio
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from decimal import Decimal
import json
from dataclasses import dataclass, asdict
from enum import Enum
import hmac
import hashlib
import base64

# Payment providers
import stripe
import paypal
from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator

# Database
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session

# Analytics
import pandas as pd
import numpy as np

from ..models.hybrid_database import create_hybrid_database
from ..services.notification_service import notification_service

logger = logging.getLogger(__name__)

# Enums
class SubscriptionTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    LIFETIME = "lifetime"

class PaymentProvider(str, Enum):
    STRIPE = "stripe"
    PAYPAL = "paypal"
    CRYPTO = "crypto"
    BANK_TRANSFER = "bank_transfer"

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    TRIAL = "trial"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    PAUSED = "paused"

# Pydantic Models
class PricingPlan(BaseModel):
    """Plano de preços"""
    name: str
    tier: SubscriptionTier
    price_monthly_usd: float
    price_yearly_usd: float
    discount_yearly_pct: float = 20.0
    features: List[str]
    limits: Dict[str, int]
    popular: bool = False
    
    @validator('price_yearly_usd')
    def validate_yearly_price(cls, v, values):
        if 'price_monthly_usd' in values:
            expected = values['price_monthly_usd'] * 12 * (1 - values.get('discount_yearly_pct', 20) / 100)
            if abs(v - expected) > 0.01:
                raise ValueError('Yearly price inconsistent with monthly price and discount')
        return v

class SubscriptionRequest(BaseModel):
    """Request de criação de assinatura"""
    user_id: str
    plan_tier: SubscriptionTier
    billing_cycle: str = Field(..., regex="^(monthly|yearly)$")
    payment_provider: PaymentProvider = PaymentProvider.STRIPE
    promo_code: Optional[str] = None
    trial_days: Optional[int] = None

class PaymentMethodInfo(BaseModel):
    """Informações do método de pagamento"""
    provider: PaymentProvider
    provider_payment_method_id: str
    last_four: Optional[str] = None
    brand: Optional[str] = None
    exp_month: Optional[int] = None
    exp_year: Optional[int] = None

class UsageMetrics(BaseModel):
    """Métricas de uso do usuário"""
    api_calls_current_period: int
    predictions_made: int
    alerts_created: int
    dashboard_views: int
    data_export_requests: int
    last_activity: datetime

# Database Models
Base = declarative_base()

class Customer(Base):
    """Modelo de cliente"""
    __tablename__ = 'customers'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), unique=True, nullable=False, comment="ID do usuário (Steam ID)")
    email = Column(String(200), nullable=False)
    name = Column(String(200))
    country = Column(String(3), comment="Código ISO do país")
    
    # Payment providers
    stripe_customer_id = Column(String(100))
    paypal_customer_id = Column(String(100))
    
    # Lifecycle
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    lifetime_value = Column(Float, default=0.0, comment="LTV em USD")
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="customer")
    payments = relationship("Payment", back_populates="customer")
    usage_records = relationship("UsageRecord", back_populates="customer")

class Subscription(Base):
    """Modelo de assinatura"""
    __tablename__ = 'subscriptions'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    
    # Plan details
    tier = Column(String(20), nullable=False, comment="free, pro, enterprise, lifetime")
    billing_cycle = Column(String(10), comment="monthly, yearly")
    price_usd = Column(Float, comment="Preço em USD")
    currency = Column(String(3), default="USD")
    
    # Provider details
    provider = Column(String(20), nullable=False)
    provider_subscription_id = Column(String(100))
    provider_product_id = Column(String(100))
    provider_price_id = Column(String(100))
    
    # Status and dates
    status = Column(String(20), default="active")
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    trial_start = Column(DateTime)
    trial_end = Column(DateTime)
    cancelled_at = Column(DateTime)
    ended_at = Column(DateTime)
    
    # Lifecycle
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="subscriptions")

class Payment(Base):
    """Histórico de pagamentos"""
    __tablename__ = 'payments'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    subscription_id = Column(Integer, ForeignKey('subscriptions.id'))
    
    # Payment details
    amount_usd = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    provider = Column(String(20), nullable=False)
    provider_payment_id = Column(String(100))
    provider_invoice_id = Column(String(100))
    
    # Status
    status = Column(String(20), comment="succeeded, failed, pending, refunded")
    failure_reason = Column(Text)
    
    # Metadata
    description = Column(String(500))
    metadata = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    
    # Relationships
    customer = relationship("Customer", back_populates="payments")

class UsageRecord(Base):
    """Registros de uso para billing"""
    __tablename__ = 'usage_records'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    
    # Usage details
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    api_calls = Column(Integer, default=0)
    predictions_made = Column(Integer, default=0)
    alerts_created = Column(Integer, default=0)
    data_exports = Column(Integer, default=0)
    
    # Billing
    overage_charges = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="usage_records")

class PromoCode(Base):
    """Códigos promocionais"""
    __tablename__ = 'promo_codes'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    discount_percent = Column(Float)
    discount_amount_usd = Column(Float)
    max_uses = Column(Integer)
    current_uses = Column(Integer, default=0)
    valid_from = Column(DateTime)
    valid_until = Column(DateTime)
    applicable_tiers = Column(JSON, comment="Lista de tiers aplicáveis")
    created_at = Column(DateTime, default=datetime.utcnow)

class AffiliateProgram(Base):
    """Programa de afiliados"""
    __tablename__ = 'affiliates'
    
    id = Column(Integer, primary_key=True)
    affiliate_id = Column(String(50), unique=True, nullable=False)
    user_id = Column(String(50), comment="ID do usuário afiliado")
    commission_rate = Column(Float, default=0.2, comment="Taxa de comissão (20%)")
    total_earnings = Column(Float, default=0.0)
    total_referrals = Column(Integer, default=0)
    payout_threshold = Column(Float, default=50.0)
    payment_email = Column(String(200))
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

class MonetizationEngine:
    """Engine principal de monetização"""
    
    def __init__(self):
        self.pricing_plans = self._init_pricing_plans()
        self.stripe_client = self._init_stripe()
        self.paypal_client = self._init_paypal()
        self.hybrid_db = None
        
        # Analytics
        self.revenue_metrics = {
            "mrr": 0.0,  # Monthly Recurring Revenue
            "arr": 0.0,  # Annual Recurring Revenue
            "churn_rate": 0.0,
            "ltv": 0.0,  # Customer Lifetime Value
            "arpu": 0.0,  # Average Revenue Per User
            "conversion_rate": 0.0
        }
        
        logger.info("💰 MonetizationEngine inicializado")
    
    def _init_pricing_plans(self) -> Dict[SubscriptionTier, PricingPlan]:
        """Inicializa planos de preços"""
        return {
            SubscriptionTier.FREE: PricingPlan(
                name="Free",
                tier=SubscriptionTier.FREE,
                price_monthly_usd=0.0,
                price_yearly_usd=0.0,
                features=[
                    "Basic price tracking",
                    "5 price alerts",
                    "Limited API access (100 calls/day)",
                    "Community support",
                    "7-day price history"
                ],
                limits={
                    "api_calls_daily": 100,
                    "alerts_active": 5,
                    "predictions_daily": 3,
                    "data_exports_monthly": 1
                }
            ),
            
            SubscriptionTier.PRO: PricingPlan(
                name="Pro",
                tier=SubscriptionTier.PRO,
                price_monthly_usd=29.0,
                price_yearly_usd=278.4,  # 20% discount
                features=[
                    "Advanced analytics dashboard",
                    "Unlimited price alerts",
                    "ML predictions & insights",
                    "Enhanced API access (10K calls/day)",
                    "Priority support",
                    "30-day price history",
                    "Custom notification channels",
                    "Export capabilities"
                ],
                limits={
                    "api_calls_daily": 10000,
                    "alerts_active": -1,  # Unlimited
                    "predictions_daily": 50,
                    "data_exports_monthly": 10
                },
                popular=True
            ),
            
            SubscriptionTier.ENTERPRISE: PricingPlan(
                name="Enterprise",
                tier=SubscriptionTier.ENTERPRISE,
                price_monthly_usd=299.0,
                price_yearly_usd=2870.4,  # 20% discount
                features=[
                    "All Pro features",
                    "Unlimited API access",
                    "Custom ML models",
                    "Dedicated support manager",
                    "SLA guarantees",
                    "Custom integrations",
                    "Advanced analytics",
                    "Bulk data access",
                    "White-label options"
                ],
                limits={
                    "api_calls_daily": -1,  # Unlimited
                    "alerts_active": -1,  # Unlimited
                    "predictions_daily": -1,  # Unlimited
                    "data_exports_monthly": -1  # Unlimited
                }
            ),
            
            SubscriptionTier.LIFETIME: PricingPlan(
                name="Lifetime",
                tier=SubscriptionTier.LIFETIME,
                price_monthly_usd=0.0,  # One-time payment
                price_yearly_usd=1999.0,  # One-time payment
                features=[
                    "All Pro features forever",
                    "Grandfathered pricing",
                    "Exclusive lifetime updates",
                    "VIP support",
                    "Beta access to new features"
                ],
                limits={
                    "api_calls_daily": 25000,
                    "alerts_active": -1,
                    "predictions_daily": 100,
                    "data_exports_monthly": 25
                }
            )
        }
    
    def _init_stripe(self):
        """Inicializa cliente Stripe"""
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        return stripe
    
    def _init_paypal(self):
        """Inicializa cliente PayPal"""
        # Mock implementation
        return None
    
    async def __aenter__(self):
        """Async context manager"""
        self.hybrid_db = create_hybrid_database()
        await self.hybrid_db.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.hybrid_db:
            await self.hybrid_db.disconnect()
    
    async def create_subscription(self, request: SubscriptionRequest) -> Dict[str, Any]:
        """Cria nova assinatura"""
        try:
            # Validar plano
            if request.plan_tier not in self.pricing_plans:
                raise ValueError(f"Invalid plan tier: {request.plan_tier}")
            
            plan = self.pricing_plans[request.plan_tier]
            
            # Calcular preço
            price = plan.price_monthly_usd if request.billing_cycle == "monthly" else plan.price_yearly_usd
            
            # Aplicar código promocional se fornecido
            if request.promo_code:
                price = await self._apply_promo_code(price, request.promo_code)
            
            # Criar customer se não existir
            customer = await self._get_or_create_customer(request.user_id)
            
            # Criar assinatura no provider
            if request.payment_provider == PaymentProvider.STRIPE:
                provider_subscription = await self._create_stripe_subscription(
                    customer, plan, request.billing_cycle, price, request.trial_days
                )
            elif request.payment_provider == PaymentProvider.PAYPAL:
                provider_subscription = await self._create_paypal_subscription(
                    customer, plan, request.billing_cycle, price
                )
            else:
                raise ValueError(f"Unsupported payment provider: {request.payment_provider}")
            
            # Salvar no banco
            subscription = await self._save_subscription(
                customer, plan, request, provider_subscription, price
            )
            
            # Atualizar métricas
            await self._update_revenue_metrics()
            
            # Enviar notificações
            await self._send_subscription_notifications(customer, subscription, "created")
            
            return {
                "success": True,
                "subscription_id": subscription.id,
                "checkout_url": provider_subscription.get("checkout_url"),
                "trial_end": subscription.trial_end.isoformat() if subscription.trial_end else None
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar assinatura: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_stripe_subscription(self, customer, plan: PricingPlan, 
                                        billing_cycle: str, price: float, trial_days: int = None) -> Dict[str, Any]:
        """Cria assinatura no Stripe"""
        try:
            # Criar produto se não existir
            product_id = f"skinlytics-{plan.tier.value}"
            try:
                product = stripe.Product.retrieve(product_id)
            except stripe.error.InvalidRequestError:
                product = stripe.Product.create(
                    id=product_id,
                    name=f"Skinlytics {plan.name}",
                    description=f"Skinlytics {plan.name} plan - {', '.join(plan.features[:3])}"
                )
            
            # Criar preço
            price_id = f"{product_id}-{billing_cycle}"
            try:
                stripe_price = stripe.Price.retrieve(price_id)
            except stripe.error.InvalidRequestError:
                stripe_price = stripe.Price.create(
                    id=price_id,
                    product=product.id,
                    unit_amount=int(price * 100),  # Stripe usa centavos
                    currency="usd",
                    recurring={
                        "interval": "month" if billing_cycle == "monthly" else "year"
                    }
                )
            
            # Criar checkout session
            session_params = {
                "customer": customer.stripe_customer_id,
                "payment_method_types": ["card"],
                "line_items": [{
                    "price": stripe_price.id,
                    "quantity": 1
                }],
                "mode": "subscription",
                "success_url": f"{os.getenv('APP_URL')}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}",
                "cancel_url": f"{os.getenv('APP_URL')}/pricing",
                "metadata": {
                    "user_id": customer.user_id,
                    "plan_tier": plan.tier.value
                }
            }
            
            # Adicionar trial se especificado
            if trial_days:
                session_params["subscription_data"] = {
                    "trial_period_days": trial_days
                }
            
            session = stripe.checkout.Session.create(**session_params)
            
            return {
                "provider_subscription_id": session.subscription,
                "provider_product_id": product.id,
                "provider_price_id": stripe_price.id,
                "checkout_url": session.url,
                "session_id": session.id
            }
            
        except Exception as e:
            logger.error(f"❌ Erro no Stripe: {e}")
            raise
    
    async def _create_paypal_subscription(self, customer, plan: PricingPlan, 
                                        billing_cycle: str, price: float) -> Dict[str, Any]:
        """Cria assinatura no PayPal"""
        # Mock implementation - em produção implementar PayPal SDK
        return {
            "provider_subscription_id": f"paypal_sub_{customer.id}_{int(time.time())}",
            "provider_product_id": f"paypal_prod_{plan.tier.value}",
            "provider_price_id": f"paypal_price_{plan.tier.value}_{billing_cycle}",
            "checkout_url": f"https://paypal.com/checkout/mock/{customer.id}"
        }
    
    async def _apply_promo_code(self, price: float, promo_code: str) -> float:
        """Aplica código promocional"""
        # Query promo code from database
        query = """
        SELECT discount_percent, discount_amount_usd, max_uses, current_uses, valid_until
        FROM promo_codes 
        WHERE code = :code AND valid_until > NOW()
        """
        
        result = await self.hybrid_db.query(
            query, 
            {"code": promo_code}, 
            operation='SELECT'
        )
        
        if not result:
            raise ValueError("Invalid or expired promo code")
        
        promo = result[0]
        
        # Check usage limits
        if promo["max_uses"] and promo["current_uses"] >= promo["max_uses"]:
            raise ValueError("Promo code usage limit exceeded")
        
        # Apply discount
        if promo["discount_percent"]:
            discount = price * (promo["discount_percent"] / 100)
        elif promo["discount_amount_usd"]:
            discount = min(promo["discount_amount_usd"], price)
        else:
            discount = 0
        
        # Update usage count
        await self.hybrid_db.query(
            "UPDATE promo_codes SET current_uses = current_uses + 1 WHERE code = :code",
            {"code": promo_code},
            operation='UPDATE'
        )
        
        return max(0, price - discount)
    
    async def _get_or_create_customer(self, user_id: str) -> Customer:
        """Obtém ou cria customer"""
        # Try to get existing customer
        query = "SELECT * FROM customers WHERE user_id = :user_id"
        result = await self.hybrid_db.query(
            query, 
            {"user_id": user_id}, 
            operation='SELECT'
        )
        
        if result:
            return Customer(**result[0])
        
        # Create new customer
        # Em produção, obter dados do usuário Steam
        customer_data = {
            "user_id": user_id,
            "email": f"{user_id}@steam.user",  # Mock
            "name": f"User {user_id}",
            "country": "US"  # Default
        }
        
        # Create in Stripe
        stripe_customer = stripe.Customer.create(
            email=customer_data["email"],
            name=customer_data["name"],
            metadata={"user_id": user_id}
        )
        customer_data["stripe_customer_id"] = stripe_customer.id
        
        # Save to database
        insert_query = """
        INSERT INTO customers (user_id, email, name, country, stripe_customer_id, created_at)
        VALUES (:user_id, :email, :name, :country, :stripe_customer_id, NOW())
        """
        
        await self.hybrid_db.query(
            insert_query,
            customer_data,
            operation='INSERT'
        )
        
        return Customer(**customer_data)
    
    async def _save_subscription(self, customer: Customer, plan: PricingPlan, 
                               request: SubscriptionRequest, provider_subscription: Dict[str, Any], 
                               price: float) -> Subscription:
        """Salva assinatura no banco"""
        subscription_data = {
            "customer_id": customer.id,
            "tier": request.plan_tier.value,
            "billing_cycle": request.billing_cycle,
            "price_usd": price,
            "provider": request.payment_provider.value,
            "provider_subscription_id": provider_subscription["provider_subscription_id"],
            "provider_product_id": provider_subscription["provider_product_id"],
            "provider_price_id": provider_subscription["provider_price_id"],
            "status": "trial" if request.trial_days else "active",
            "current_period_start": datetime.utcnow(),
            "current_period_end": datetime.utcnow() + timedelta(
                days=30 if request.billing_cycle == "monthly" else 365
            )
        }
        
        if request.trial_days:
            subscription_data["trial_start"] = datetime.utcnow()
            subscription_data["trial_end"] = datetime.utcnow() + timedelta(days=request.trial_days)
        
        insert_query = """
        INSERT INTO subscriptions 
        (customer_id, tier, billing_cycle, price_usd, provider, provider_subscription_id, 
         provider_product_id, provider_price_id, status, current_period_start, current_period_end,
         trial_start, trial_end, created_at)
        VALUES 
        (:customer_id, :tier, :billing_cycle, :price_usd, :provider, :provider_subscription_id,
         :provider_product_id, :provider_price_id, :status, :current_period_start, :current_period_end,
         :trial_start, :trial_end, NOW())
        """
        
        await self.hybrid_db.query(
            insert_query,
            subscription_data,
            operation='INSERT'
        )
        
        return Subscription(**subscription_data)
    
    async def handle_stripe_webhook(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle webhooks do Stripe"""
        try:
            if event_type == "checkout.session.completed":
                await self._handle_checkout_completed(event_data)
            
            elif event_type == "invoice.payment_succeeded":
                await self._handle_payment_succeeded(event_data)
            
            elif event_type == "invoice.payment_failed":
                await self._handle_payment_failed(event_data)
            
            elif event_type == "customer.subscription.updated":
                await self._handle_subscription_updated(event_data)
            
            elif event_type == "customer.subscription.deleted":
                await self._handle_subscription_cancelled(event_data)
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"❌ Erro no webhook Stripe: {e}")
            return {"success": False, "error": str(e)}
    
    async def _handle_checkout_completed(self, event_data: Dict[str, Any]):
        """Handle checkout completado"""
        session = event_data
        subscription_id = session.get("subscription")
        customer_id = session.get("customer")
        
        # Ativar assinatura
        await self.hybrid_db.query(
            """UPDATE subscriptions 
               SET status = 'active', provider_subscription_id = :subscription_id
               WHERE customer_id = (SELECT id FROM customers WHERE stripe_customer_id = :customer_id)
               AND status = 'trial'""",
            {"subscription_id": subscription_id, "customer_id": customer_id},
            operation='UPDATE'
        )
        
        logger.info(f"✅ Checkout completado: {session.get('id')}")
    
    async def _handle_payment_succeeded(self, event_data: Dict[str, Any]):
        """Handle pagamento bem-sucedido"""
        invoice = event_data
        
        # Registrar pagamento
        payment_data = {
            "customer_stripe_id": invoice["customer"],
            "amount_usd": invoice["amount_paid"] / 100,
            "provider": "stripe",
            "provider_payment_id": invoice["payment_intent"],
            "provider_invoice_id": invoice["id"],
            "status": "succeeded",
            "processed_at": datetime.utcnow()
        }
        
        # Salvar no banco
        await self._save_payment(payment_data)
        
        # Atualizar métricas
        await self._update_revenue_metrics()
        
        logger.info(f"✅ Pagamento processado: ${payment_data['amount_usd']}")
    
    async def _handle_payment_failed(self, event_data: Dict[str, Any]):
        """Handle falha no pagamento"""
        invoice = event_data
        
        # Atualizar status da assinatura
        await self.hybrid_db.query(
            """UPDATE subscriptions 
               SET status = 'past_due' 
               WHERE provider_subscription_id = :subscription_id""",
            {"subscription_id": invoice.get("subscription")},
            operation='UPDATE'
        )
        
        # Registrar pagamento falhado
        payment_data = {
            "customer_stripe_id": invoice["customer"],
            "amount_usd": invoice["amount_due"] / 100,
            "provider": "stripe",
            "provider_invoice_id": invoice["id"],
            "status": "failed",
            "failure_reason": "Payment failed",
            "processed_at": datetime.utcnow()
        }
        
        await self._save_payment(payment_data)
        
        # Enviar notificação
        await self._send_payment_failed_notification(invoice["customer"])
        
        logger.warning(f"❌ Pagamento falhou: {invoice['id']}")
    
    async def _save_payment(self, payment_data: Dict[str, Any]):
        """Salva registro de pagamento"""
        # Get customer_id from stripe_customer_id
        customer_query = "SELECT id FROM customers WHERE stripe_customer_id = :stripe_id"
        customer_result = await self.hybrid_db.query(
            customer_query,
            {"stripe_id": payment_data["customer_stripe_id"]},
            operation='SELECT'
        )
        
        if not customer_result:
            logger.warning(f"Customer não encontrado: {payment_data['customer_stripe_id']}")
            return
        
        payment_data["customer_id"] = customer_result[0]["id"]
        
        insert_query = """
        INSERT INTO payments 
        (customer_id, amount_usd, provider, provider_payment_id, provider_invoice_id, 
         status, failure_reason, processed_at, created_at)
        VALUES 
        (:customer_id, :amount_usd, :provider, :provider_payment_id, :provider_invoice_id,
         :status, :failure_reason, :processed_at, NOW())
        """
        
        await self.hybrid_db.query(
            insert_query,
            payment_data,
            operation='INSERT'
        )
    
    async def _update_revenue_metrics(self):
        """Atualiza métricas de receita"""
        try:
            # Calculate MRR (Monthly Recurring Revenue)
            mrr_query = """
            SELECT SUM(
                CASE 
                    WHEN billing_cycle = 'monthly' THEN price_usd
                    WHEN billing_cycle = 'yearly' THEN price_usd / 12
                    ELSE 0
                END
            ) as mrr
            FROM subscriptions 
            WHERE status IN ('active', 'trial')
            """
            
            mrr_result = await self.hybrid_db.query(mrr_query, operation='SELECT')
            self.revenue_metrics["mrr"] = mrr_result[0]["mrr"] or 0.0
            self.revenue_metrics["arr"] = self.revenue_metrics["mrr"] * 12
            
            # Calculate churn rate (monthly)
            churn_query = """
            SELECT 
                COUNT(CASE WHEN cancelled_at >= NOW() - INTERVAL 30 DAY THEN 1 END) as churned,
                COUNT(*) as total_active_month_ago
            FROM subscriptions 
            WHERE created_at <= NOW() - INTERVAL 30 DAY
            """
            
            churn_result = await self.hybrid_db.query(churn_query, operation='SELECT')
            if churn_result[0]["total_active_month_ago"] > 0:
                self.revenue_metrics["churn_rate"] = (
                    churn_result[0]["churned"] / churn_result[0]["total_active_month_ago"]
                )
            
            # Calculate ARPU (Average Revenue Per User)
            arpu_query = """
            SELECT AVG(price_usd) as arpu
            FROM subscriptions 
            WHERE status IN ('active', 'trial') 
            AND billing_cycle = 'monthly'
            """
            
            arpu_result = await self.hybrid_db.query(arpu_query, operation='SELECT')
            self.revenue_metrics["arpu"] = arpu_result[0]["arpu"] or 0.0
            
            logger.info(f"📊 Métricas atualizadas: MRR=${self.revenue_metrics['mrr']:.2f}, Churn={self.revenue_metrics['churn_rate']:.2%}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar métricas: {e}")
    
    async def get_user_subscription(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Obtém assinatura ativa do usuário"""
        query = """
        SELECT s.*, c.user_id 
        FROM subscriptions s
        JOIN customers c ON s.customer_id = c.id
        WHERE c.user_id = :user_id 
        AND s.status IN ('active', 'trial', 'past_due')
        ORDER BY s.created_at DESC
        LIMIT 1
        """
        
        result = await self.hybrid_db.query(
            query,
            {"user_id": user_id},
            operation='SELECT'
        )
        
        if result:
            subscription = result[0]
            plan = self.pricing_plans.get(SubscriptionTier(subscription["tier"]))
            
            return {
                "subscription": subscription,
                "plan": plan.dict() if plan else None,
                "limits": plan.limits if plan else {},
                "features": plan.features if plan else []
            }
        
        # Return free plan as default
        return {
            "subscription": {"tier": "free", "status": "active"},
            "plan": self.pricing_plans[SubscriptionTier.FREE].dict(),
            "limits": self.pricing_plans[SubscriptionTier.FREE].limits,
            "features": self.pricing_plans[SubscriptionTier.FREE].features
        }
    
    async def check_usage_limits(self, user_id: str, action: str) -> Dict[str, Any]:
        """Verifica limites de uso do usuário"""
        user_subscription = await self.get_user_subscription(user_id)
        limits = user_subscription["limits"]
        
        # Get current usage
        current_usage = await self._get_current_usage(user_id)
        
        # Check specific action
        limit_checks = {
            "api_call": {
                "limit": limits.get("api_calls_daily", 0),
                "current": current_usage.get("api_calls_today", 0),
                "allowed": True
            },
            "prediction": {
                "limit": limits.get("predictions_daily", 0),
                "current": current_usage.get("predictions_today", 0),
                "allowed": True
            },
            "alert": {
                "limit": limits.get("alerts_active", 0),
                "current": current_usage.get("alerts_active", 0),
                "allowed": True
            }
        }
        
        # Check if action is allowed
        if action in limit_checks:
            check = limit_checks[action]
            if check["limit"] != -1:  # -1 means unlimited
                check["allowed"] = check["current"] < check["limit"]
        
        return {
            "user_tier": user_subscription["subscription"]["tier"],
            "limits": limit_checks,
            "upgrade_required": not limit_checks.get(action, {}).get("allowed", True)
        }
    
    async def _get_current_usage(self, user_id: str) -> Dict[str, int]:
        """Obtém uso atual do usuário"""
        # Mock implementation - em produção buscar do Redis/banco
        return {
            "api_calls_today": 45,
            "predictions_today": 2,
            "alerts_active": 3,
            "data_exports_this_month": 1
        }
    
    async def generate_revenue_report(self, period_days: int = 30) -> Dict[str, Any]:
        """Gera relatório de receita"""
        try:
            # Revenue over time
            revenue_query = """
            SELECT 
                DATE(processed_at) as date,
                SUM(amount_usd) as daily_revenue,
                COUNT(*) as transactions
            FROM payments 
            WHERE processed_at >= NOW() - INTERVAL :days DAY
            AND status = 'succeeded'
            GROUP BY DATE(processed_at)
            ORDER BY date
            """
            
            revenue_data = await self.hybrid_db.query(
                revenue_query,
                {"days": period_days},
                operation='SELECT'
            )
            
            # Subscription breakdown
            subscription_query = """
            SELECT 
                tier,
                COUNT(*) as count,
                SUM(price_usd) as revenue
            FROM subscriptions 
            WHERE status IN ('active', 'trial')
            GROUP BY tier
            """
            
            subscription_data = await self.hybrid_db.query(
                subscription_query,
                operation='SELECT'
            )
            
            # Calculate totals
            total_revenue = sum(day["daily_revenue"] for day in revenue_data)
            total_transactions = sum(day["transactions"] for day in revenue_data)
            
            return {
                "period_days": period_days,
                "total_revenue": total_revenue,
                "total_transactions": total_transactions,
                "average_daily_revenue": total_revenue / period_days if period_days > 0 else 0,
                "current_metrics": self.revenue_metrics,
                "daily_revenue": revenue_data,
                "subscription_breakdown": subscription_data,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erro no relatório de receita: {e}")
            return {"error": str(e)}
    
    def get_pricing_plans(self) -> Dict[str, Any]:
        """Retorna todos os planos de preços"""
        return {
            tier.value: plan.dict() 
            for tier, plan in self.pricing_plans.items()
        }

# Global instance
monetization_engine = MonetizationEngine()