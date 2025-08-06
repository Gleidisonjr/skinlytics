"""
Advanced Notification Service - Telegram, Discord, Email

Sistema avançado de notificações para alertas de oportunidades,
previsões de mercado e atualizações importantes da plataforma.

Features:
    - Telegram Bot para alertas instantâneos
    - Discord Webhooks para comunidades
    - Email para relatórios periódicos
    - SMS para alertas críticos (Twilio)
    - Push notifications (Firebase)
    - Template system com personalização

Author: CS2 Skin Tracker Team - Skinlytics Platform
Version: 2.0.0
"""

import asyncio
import aiohttp
import smtplib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import json
import os
import re
from jinja2 import Template
import redis.asyncio as redis

logger = logging.getLogger(__name__)

@dataclass
class NotificationTemplate:
    """Template para diferentes tipos de notificação"""
    name: str
    subject: str
    html_template: str
    text_template: str
    telegram_template: str
    discord_template: str
    priority: str = "normal"  # low, normal, high, critical
    
@dataclass
class NotificationChannel:
    """Canal de notificação configurado"""
    type: str  # telegram, discord, email, sms
    config: Dict[str, Any]
    enabled: bool = True
    filters: List[str] = None

@dataclass
class NotificationEvent:
    """Evento de notificação"""
    event_type: str
    data: Dict[str, Any]
    user_id: Optional[str] = None
    priority: str = "normal"
    channels: List[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

class NotificationService:
    """Serviço central de notificações"""
    
    def __init__(self):
        # Configurações
        self.redis_client = None
        self.session = None
        
        # Templates pré-definidos
        self.templates = self._load_templates()
        
        # Canais configurados
        self.channels = self._load_channels()
        
        # Estatísticas
        self.stats = {
            'sent': 0,
            'failed': 0,
            'telegram': 0,
            'discord': 0,
            'email': 0,
            'sms': 0
        }
        
        logger.info("🔔 NotificationService inicializado")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        self.redis_client = redis.from_url(
            os.getenv('REDIS_URL', 'redis://localhost:6379')
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
        if self.redis_client:
            await self.redis_client.close()
    
    def _load_templates(self) -> Dict[str, NotificationTemplate]:
        """Carrega templates de notificação"""
        templates = {
            'price_alert': NotificationTemplate(
                name='Price Alert',
                subject='🚨 Alerta de Preço - {{item_name}}',
                html_template='''
                <h2>🚨 Alerta de Preço</h2>
                <p><strong>Item:</strong> {{item_name}}</p>
                <p><strong>Preço Atual:</strong> ${{current_price}}</p>
                <p><strong>Preço Alvo:</strong> ${{target_price}}</p>
                <p><strong>Variação:</strong> {{price_change}}%</p>
                <p><strong>Float:</strong> {{float_value}}</p>
                <a href="{{listing_url}}">Ver Listing</a>
                ''',
                text_template='🚨 {{item_name}} - ${{current_price}} ({{price_change}}%)',
                telegram_template='🚨 *{{item_name}}*\n💰 Preço: ${{current_price}}\n📈 Variação: {{price_change}}%\n🎯 Float: {{float_value}}\n[Ver Listing]({{listing_url}})',
                discord_template='🚨 **{{item_name}}** - ${{current_price}} ({{price_change}}%)',
                priority='high'
            ),
            
            'best_deal': NotificationTemplate(
                name='Best Deal',
                subject='💎 Oportunidade Encontrada - {{item_name}}',
                html_template='''
                <h2>💎 Excelente Oportunidade!</h2>
                <p><strong>Item:</strong> {{item_name}}</p>
                <p><strong>Preço:</strong> ${{price}}</p>
                <p><strong>Preço de Mercado:</strong> ${{market_price}}</p>
                <p><strong>Desconto:</strong> {{discount}}%</p>
                <p><strong>Economia:</strong> ${{savings}}</p>
                <p><strong>Vendedor:</strong> {{seller_name}} ({{seller_rating}}% confiança)</p>
                <a href="{{listing_url}}">COMPRAR AGORA</a>
                ''',
                text_template='💎 {{item_name}} - ${{price}} ({{discount}}% OFF)',
                telegram_template='💎 *OPORTUNIDADE*\n🎯 {{item_name}}\n💰 ${{price}} ({{discount}}% OFF)\n💵 Economia: ${{savings}}\n👤 {{seller_name}} ({{seller_rating}}%)\n[COMPRAR]({{listing_url}})',
                discord_template='💎 **DEAL!** {{item_name}} - ${{price}} ({{discount}}% OFF)',
                priority='high'
            ),
            
            'market_trend': NotificationTemplate(
                name='Market Trend',
                subject='📈 Análise de Tendência - {{period}}',
                html_template='''
                <h2>📈 Relatório de Tendências</h2>
                <p><strong>Período:</strong> {{period}}</p>
                <p><strong>Itens Analisados:</strong> {{items_count}}</p>
                <p><strong>Top Gainers:</strong></p>
                <ul>
                {% for item in top_gainers %}
                    <li>{{item.name}} (+{{item.change}}%)</li>
                {% endfor %}
                </ul>
                <p><strong>Top Losers:</strong></p>
                <ul>
                {% for item in top_losers %}
                    <li>{{item.name}} ({{item.change}}%)</li>
                {% endfor %}
                </ul>
                ''',
                text_template='📈 Relatório {{period}}: {{summary}}',
                telegram_template='📈 *Relatório {{period}}*\n\n🚀 Top Gainers:\n{{top_gainers_text}}\n\n📉 Top Losers:\n{{top_losers_text}}',
                discord_template='📈 **Relatório {{period}}** - {{summary}}',
                priority='normal'
            ),
            
            'ml_prediction': NotificationTemplate(
                name='ML Prediction',
                subject='🤖 Previsão IA - {{item_name}}',
                html_template='''
                <h2>🤖 Previsão de Inteligência Artificial</h2>
                <p><strong>Item:</strong> {{item_name}}</p>
                <p><strong>Preço Atual:</strong> ${{current_price}}</p>
                <p><strong>Previsão 24h:</strong> ${{predicted_price_24h}}</p>
                <p><strong>Confiança:</strong> {{confidence}}%</p>
                <p><strong>Recomendação:</strong> {{recommendation}}</p>
                <p><strong>Fatores:</strong> {{factors}}</p>
                ''',
                text_template='🤖 {{item_name}}: {{recommendation}} ({{confidence}}%)',
                telegram_template='🤖 *Previsão IA*\n🎯 {{item_name}}\n💰 Atual: ${{current_price}}\n🔮 24h: ${{predicted_price_24h}}\n📊 Confiança: {{confidence}}%\n💡 {{recommendation}}',
                discord_template='🤖 **{{item_name}}** - {{recommendation}} ({{confidence}}%)',
                priority='normal'
            ),
            
            'system_alert': NotificationTemplate(
                name='System Alert',
                subject='⚠️ Sistema - {{alert_type}}',
                html_template='''
                <h2>⚠️ Alerta do Sistema</h2>
                <p><strong>Tipo:</strong> {{alert_type}}</p>
                <p><strong>Mensagem:</strong> {{message}}</p>
                <p><strong>Timestamp:</strong> {{timestamp}}</p>
                <p><strong>Ação Requerida:</strong> {{action_required}}</p>
                ''',
                text_template='⚠️ {{alert_type}}: {{message}}',
                telegram_template='⚠️ *Sistema*\n🔴 {{alert_type}}\n📝 {{message}}\n⏰ {{timestamp}}',
                discord_template='⚠️ **Sistema** - {{alert_type}}: {{message}}',
                priority='critical'
            )
        }
        
        return templates
    
    def _load_channels(self) -> Dict[str, NotificationChannel]:
        """Carrega configuração dos canais"""
        channels = {}
        
        # Telegram
        if os.getenv('TELEGRAM_BOT_TOKEN'):
            channels['telegram'] = NotificationChannel(
                type='telegram',
                config={
                    'bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
                    'default_chat_id': os.getenv('TELEGRAM_DEFAULT_CHAT_ID')
                }
            )
        
        # Discord
        if os.getenv('DISCORD_WEBHOOK_URL'):
            channels['discord'] = NotificationChannel(
                type='discord',
                config={
                    'webhook_url': os.getenv('DISCORD_WEBHOOK_URL'),
                    'username': 'Skinlytics Bot',
                    'avatar_url': 'https://example.com/bot-avatar.png'
                }
            )
        
        # Email
        if os.getenv('SMTP_HOST'):
            channels['email'] = NotificationChannel(
                type='email',
                config={
                    'smtp_host': os.getenv('SMTP_HOST'),
                    'smtp_port': int(os.getenv('SMTP_PORT', 587)),
                    'smtp_user': os.getenv('SMTP_USER'),
                    'smtp_password': os.getenv('SMTP_PASSWORD'),
                    'from_email': os.getenv('FROM_EMAIL'),
                    'from_name': 'Skinlytics Platform'
                }
            )
        
        return channels
    
    async def send_notification(self, event: NotificationEvent) -> Dict[str, Any]:
        """Envia notificação para todos os canais apropriados"""
        results = {
            'success': True,
            'channels': {},
            'total_sent': 0,
            'total_failed': 0
        }
        
        # Determinar canais a usar
        target_channels = event.channels or list(self.channels.keys())
        
        # Obter template
        template = self.templates.get(event.event_type)
        if not template:
            logger.error(f"Template não encontrado: {event.event_type}")
            return {'success': False, 'error': 'Template não encontrado'}
        
        # Verificar se deve enviar baseado na prioridade
        if not await self._should_send(event):
            return {'success': True, 'skipped': True, 'reason': 'Rate limited or filtered'}
        
        # Enviar para cada canal
        for channel_name in target_channels:
            if channel_name not in self.channels:
                continue
                
            channel = self.channels[channel_name]
            if not channel.enabled:
                continue
            
            try:
                if channel.type == 'telegram':
                    result = await self._send_telegram(event, template, channel)
                elif channel.type == 'discord':
                    result = await self._send_discord(event, template, channel)
                elif channel.type == 'email':
                    result = await self._send_email(event, template, channel)
                else:
                    result = {'success': False, 'error': 'Canal não suportado'}
                
                results['channels'][channel_name] = result
                
                if result.get('success'):
                    results['total_sent'] += 1
                    self.stats['sent'] += 1
                    self.stats[channel.type] += 1
                else:
                    results['total_failed'] += 1
                    self.stats['failed'] += 1
                    
            except Exception as e:
                logger.error(f"Erro ao enviar para {channel_name}: {e}")
                results['channels'][channel_name] = {'success': False, 'error': str(e)}
                results['total_failed'] += 1
                self.stats['failed'] += 1
        
        # Cache da notificação
        await self._cache_notification(event, results)
        
        return results
    
    async def _send_telegram(self, event: NotificationEvent, template: NotificationTemplate, channel: NotificationChannel) -> Dict[str, Any]:
        """Envia notificação via Telegram"""
        bot_token = channel.config['bot_token']
        chat_id = event.data.get('telegram_chat_id') or channel.config['default_chat_id']
        
        if not chat_id:
            return {'success': False, 'error': 'Chat ID não configurado'}
        
        # Renderizar mensagem
        message = Template(template.telegram_template).render(**event.data)
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': True
        }
        
        async with self.session.post(url, json=payload) as response:
            if response.status == 200:
                return {'success': True, 'message_id': (await response.json()).get('result', {}).get('message_id')}
            else:
                error_text = await response.text()
                return {'success': False, 'error': f'Telegram API error: {error_text}'}
    
    async def _send_discord(self, event: NotificationEvent, template: NotificationTemplate, channel: NotificationChannel) -> Dict[str, Any]:
        """Envia notificação via Discord Webhook"""
        webhook_url = channel.config['webhook_url']
        
        # Renderizar mensagem
        message = Template(template.discord_template).render(**event.data)
        
        # Cores baseadas na prioridade
        color_map = {
            'low': 0x95a5a6,      # Cinza
            'normal': 0x3498db,   # Azul
            'high': 0xf39c12,     # Laranja
            'critical': 0xe74c3c  # Vermelho
        }
        
        embed = {
            'title': f"{template.name}",
            'description': message,
            'color': color_map.get(template.priority, 0x3498db),
            'timestamp': event.created_at.isoformat(),
            'footer': {
                'text': 'Skinlytics Platform',
                'icon_url': channel.config.get('avatar_url')
            }
        }
        
        # Adicionar campos específicos baseado no tipo
        if event.event_type == 'price_alert':
            embed['fields'] = [
                {'name': 'Preço', 'value': f"${event.data.get('current_price')}", 'inline': True},
                {'name': 'Variação', 'value': f"{event.data.get('price_change')}%", 'inline': True},
                {'name': 'Float', 'value': f"{event.data.get('float_value')}", 'inline': True}
            ]
        
        payload = {
            'username': channel.config.get('username', 'Skinlytics Bot'),
            'avatar_url': channel.config.get('avatar_url'),
            'embeds': [embed]
        }
        
        async with self.session.post(webhook_url, json=payload) as response:
            if response.status in [200, 204]:
                return {'success': True}
            else:
                error_text = await response.text()
                return {'success': False, 'error': f'Discord webhook error: {error_text}'}
    
    async def _send_email(self, event: NotificationEvent, template: NotificationTemplate, channel: NotificationChannel) -> Dict[str, Any]:
        """Envia notificação via Email"""
        try:
            config = channel.config
            
            # Renderizar conteúdo
            subject = Template(template.subject).render(**event.data)
            html_content = Template(template.html_template).render(**event.data)
            text_content = Template(template.text_template).render(**event.data)
            
            # Criar mensagem
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{config['from_name']} <{config['from_email']}>"
            msg['To'] = event.data.get('email') or config.get('default_email')
            
            # Adicionar conteúdo
            msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Enviar
            with smtplib.SMTP(config['smtp_host'], config['smtp_port']) as server:
                server.starttls()
                server.login(config['smtp_user'], config['smtp_password'])
                server.send_message(msg)
            
            return {'success': True}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _should_send(self, event: NotificationEvent) -> bool:
        """Verifica se deve enviar a notificação (rate limiting, filtros)"""
        # Rate limiting por tipo de evento
        rate_limit_key = f"notification_rate:{event.event_type}:{event.user_id or 'global'}"
        
        # Limites por prioridade
        limits = {
            'low': 10,      # 10 por hora
            'normal': 20,   # 20 por hora
            'high': 50,     # 50 por hora
            'critical': 100 # 100 por hora
        }
        
        limit = limits.get(event.priority, 20)
        
        # Verificar rate limit no Redis
        current_count = await self.redis_client.get(rate_limit_key)
        if current_count and int(current_count) >= limit:
            return False
        
        # Incrementar contador
        await self.redis_client.incr(rate_limit_key)
        await self.redis_client.expire(rate_limit_key, 3600)  # 1 hora
        
        return True
    
    async def _cache_notification(self, event: NotificationEvent, results: Dict[str, Any]):
        """Cacheia a notificação para histórico"""
        cache_key = f"notification_history:{event.user_id or 'global'}"
        
        notification_record = {
            'event_type': event.event_type,
            'data': event.data,
            'results': results,
            'timestamp': event.created_at.isoformat()
        }
        
        # Adicionar ao histórico (últimas 100)
        await self.redis_client.lpush(cache_key, json.dumps(notification_record))
        await self.redis_client.ltrim(cache_key, 0, 99)
        await self.redis_client.expire(cache_key, 86400 * 7)  # 7 dias
    
    # Métodos de conveniência para diferentes tipos de notificação
    async def send_price_alert(self, item_name: str, current_price: float, target_price: float, 
                             float_value: float, listing_url: str, user_id: str = None,
                             telegram_chat_id: str = None, email: str = None) -> Dict[str, Any]:
        """Envia alerta de preço"""
        price_change = ((current_price - target_price) / target_price) * 100
        
        event = NotificationEvent(
            event_type='price_alert',
            data={
                'item_name': item_name,
                'current_price': current_price,
                'target_price': target_price,
                'price_change': round(price_change, 2),
                'float_value': float_value,
                'listing_url': listing_url,
                'telegram_chat_id': telegram_chat_id,
                'email': email
            },
            user_id=user_id,
            priority='high'
        )
        
        return await self.send_notification(event)
    
    async def send_best_deal(self, item_name: str, price: float, market_price: float,
                           seller_name: str, seller_rating: float, listing_url: str,
                           user_id: str = None) -> Dict[str, Any]:
        """Envia notificação de oportunidade"""
        discount = ((market_price - price) / market_price) * 100
        savings = market_price - price
        
        event = NotificationEvent(
            event_type='best_deal',
            data={
                'item_name': item_name,
                'price': price,
                'market_price': market_price,
                'discount': round(discount, 1),
                'savings': round(savings, 2),
                'seller_name': seller_name,
                'seller_rating': round(seller_rating, 1),
                'listing_url': listing_url
            },
            user_id=user_id,
            priority='high'
        )
        
        return await self.send_notification(event)
    
    async def send_ml_prediction(self, item_name: str, current_price: float,
                               predicted_price_24h: float, confidence: float,
                               recommendation: str, factors: str,
                               user_id: str = None) -> Dict[str, Any]:
        """Envia previsão de ML"""
        event = NotificationEvent(
            event_type='ml_prediction',
            data={
                'item_name': item_name,
                'current_price': current_price,
                'predicted_price_24h': predicted_price_24h,
                'confidence': round(confidence, 1),
                'recommendation': recommendation,
                'factors': factors
            },
            user_id=user_id,
            priority='normal'
        )
        
        return await self.send_notification(event)
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do serviço"""
        return self.stats.copy()

# Instância global
notification_service = NotificationService()