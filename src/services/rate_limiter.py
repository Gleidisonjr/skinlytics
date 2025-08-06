"""
Advanced Rate Limiter for CSFloat API

Sistema avançado de rate limiting que se adapta automaticamente aos
limites da API CSFloat, respeitando headers de resposta e implementando
backoff inteligente.

Features:
    - Detecção automática de rate limits via headers
    - Backoff exponencial adaptativo
    - Queue de requisições com prioridade
    - Métricas em tempo real
    - Recuperação automática de throttling

Author: CS2 Skin Tracker Team
Version: 2.0.0
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from collections import deque
import aiohttp

logger = logging.getLogger(__name__)

@dataclass
class RateLimitInfo:
    """Informações de rate limit extraídas dos headers"""
    limit: Optional[int] = None
    remaining: Optional[int] = None
    reset_time: Optional[datetime] = None
    retry_after: Optional[int] = None

class AdaptiveRateLimiter:
    """
    Rate limiter adaptativo para CSFloat API.
    
    Este rate limiter monitora automaticamente os headers de resposta
    da API para ajustar dinamicamente os limites de requisição.
    """
    
    def __init__(self, 
                 initial_delay: float = 1.0,
                 max_delay: float = 60.0,
                 backoff_factor: float = 1.5,
                 max_queue_size: int = 1000):
        """
        Inicializa o rate limiter adaptativo.
        
        Args:
            initial_delay: Delay inicial entre requisições (segundos)
            max_delay: Delay máximo permitido (segundos)
            backoff_factor: Fator de crescimento do backoff
            max_queue_size: Tamanho máximo da fila de requisições
        """
        self.initial_delay = initial_delay
        self.current_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.max_queue_size = max_queue_size
        
        # Estado interno
        self.last_request_time = 0.0
        self.consecutive_errors = 0
        self.rate_limit_info = RateLimitInfo()
        self.is_throttled = False
        self.throttle_until = None
        
        # Fila de requisições
        self.request_queue = deque()
        self.queue_lock = asyncio.Lock()
        
        # Métricas
        self.total_requests = 0
        self.successful_requests = 0
        self.throttled_requests = 0
        self.total_wait_time = 0.0
        
        logger.info(f"Rate limiter inicializado: {initial_delay}s delay inicial")
    
    async def acquire(self) -> None:
        """
        Adquire permissão para fazer uma requisição.
        
        Este método bloqueia até que seja seguro fazer a próxima requisição,
        considerando rate limits, throttling e backoff.
        """
        start_time = time.time()
        
        # Verificar se estamos sendo throttled
        if self.is_throttled and self.throttle_until:
            if datetime.now() < self.throttle_until:
                wait_time = (self.throttle_until - datetime.now()).total_seconds()
                logger.warning(f"Throttled - aguardando {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
                self.throttled_requests += 1
            else:
                self.is_throttled = False
                self.throttle_until = None
                logger.info("Throttling expirou - retomando requisições")
        
        # Calcular delay necessário
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.current_delay:
            wait_time = self.current_delay - time_since_last
            logger.debug(f"Rate limiting - aguardando {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
            self.total_wait_time += wait_time
        
        # Atualizar timestamp
        self.last_request_time = time.time()
        self.total_requests += 1
        
        # Log de métricas periodicamente
        if self.total_requests % 100 == 0:
            self._log_metrics()
    
    def process_response_headers(self, headers: Dict[str, str]) -> None:
        """
        Processa headers de resposta para extrair informações de rate limit.
        
        Args:
            headers: Headers da resposta HTTP
        """
        # Headers comuns de rate limiting
        rate_limit_headers = {
            'x-ratelimit-limit': 'limit',
            'x-ratelimit-remaining': 'remaining',
            'x-ratelimit-reset': 'reset_time',
            'retry-after': 'retry_after',
            'ratelimit-limit': 'limit',
            'ratelimit-remaining': 'remaining',
            'ratelimit-reset': 'reset_time'
        }
        
        updated = False
        
        for header_name, attr_name in rate_limit_headers.items():
            header_value = headers.get(header_name) or headers.get(header_name.upper())
            
            if header_value:
                try:
                    if attr_name in ['limit', 'remaining', 'retry_after']:
                        value = int(header_value)
                        setattr(self.rate_limit_info, attr_name, value)
                        updated = True
                    elif attr_name == 'reset_time':
                        # Pode ser timestamp Unix ou segundos até reset
                        try:
                            timestamp = int(header_value)
                            if timestamp > 1000000000:  # Timestamp Unix
                                reset_time = datetime.fromtimestamp(timestamp)
                            else:  # Segundos até reset
                                reset_time = datetime.now() + timedelta(seconds=timestamp)
                            self.rate_limit_info.reset_time = reset_time
                            updated = True
                        except ValueError:
                            pass
                except ValueError:
                    logger.debug(f"Erro ao processar header {header_name}: {header_value}")
        
        if updated:
            self._adjust_rate_limit()
    
    def _adjust_rate_limit(self) -> None:
        """Ajusta o rate limit baseado nas informações da API"""
        info = self.rate_limit_info
        
        if info.remaining is not None and info.limit is not None:
            # Calcular utilização atual
            usage_ratio = (info.limit - info.remaining) / info.limit
            
            if usage_ratio > 0.8:  # 80% do limite usado
                # Aumentar delay preventivamente
                new_delay = min(self.current_delay * 1.2, self.max_delay)
                if new_delay != self.current_delay:
                    logger.info(f"Rate limit alto ({usage_ratio:.1%}) - "
                              f"aumentando delay para {new_delay:.2f}s")
                    self.current_delay = new_delay
            
            elif usage_ratio < 0.3 and self.current_delay > self.initial_delay:
                # Diminuir delay se uso está baixo
                new_delay = max(self.current_delay * 0.9, self.initial_delay)
                if new_delay != self.current_delay:
                    logger.info(f"Rate limit baixo ({usage_ratio:.1%}) - "
                              f"diminuindo delay para {new_delay:.2f}s")
                    self.current_delay = new_delay
        
        # Verificar se precisamos pausar por throttling
        if info.retry_after:
            self.is_throttled = True
            self.throttle_until = datetime.now() + timedelta(seconds=info.retry_after)
            logger.warning(f"API solicitou retry após {info.retry_after}s")
        
        elif info.remaining == 0 and info.reset_time:
            self.is_throttled = True
            self.throttle_until = info.reset_time
            logger.warning(f"Rate limit esgotado - pausando até {info.reset_time}")
    
    def handle_success(self) -> None:
        """Registra uma requisição bem-sucedida"""
        self.successful_requests += 1
        self.consecutive_errors = 0
        
        # Diminuir delay gradualmente após sucessos
        if self.consecutive_errors == 0 and self.current_delay > self.initial_delay:
            self.current_delay = max(
                self.current_delay * 0.95, 
                self.initial_delay
            )
    
    def handle_error(self, status_code: int = None) -> None:
        """
        Registra um erro e ajusta o rate limiting.
        
        Args:
            status_code: Código de status HTTP do erro
        """
        self.consecutive_errors += 1
        
        # Aplicar backoff exponencial para erros
        if status_code in [429, 503, 502, 504]:  # Rate limit ou server errors
            self.current_delay = min(
                self.current_delay * self.backoff_factor,
                self.max_delay
            )
            logger.warning(f"Erro {status_code} - aumentando delay para {self.current_delay:.2f}s")
            
            # Para 429 (Too Many Requests), aplicar throttling
            if status_code == 429:
                self.is_throttled = True
                self.throttle_until = datetime.now() + timedelta(seconds=self.current_delay)
    
    def _log_metrics(self) -> None:
        """Log das métricas do rate limiter"""
        if self.total_requests > 0:
            success_rate = (self.successful_requests / self.total_requests) * 100
            avg_wait = self.total_wait_time / self.total_requests
            
            logger.info(f"📊 Rate Limiter - "
                       f"Total: {self.total_requests}, "
                       f"Sucesso: {success_rate:.1f}%, "
                       f"Throttled: {self.throttled_requests}, "
                       f"Delay atual: {self.current_delay:.2f}s, "
                       f"Wait médio: {avg_wait:.2f}s")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do rate limiter"""
        return {
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'throttled_requests': self.throttled_requests,
            'success_rate': (self.successful_requests / max(self.total_requests, 1)) * 100,
            'current_delay': self.current_delay,
            'is_throttled': self.is_throttled,
            'avg_wait_time': self.total_wait_time / max(self.total_requests, 1),
            'rate_limit_info': {
                'limit': self.rate_limit_info.limit,
                'remaining': self.rate_limit_info.remaining,
                'reset_time': self.rate_limit_info.reset_time.isoformat() if self.rate_limit_info.reset_time else None
            }
        }

class CSFloatRateLimiter(AdaptiveRateLimiter):
    """Rate limiter específico para CSFloat API com configurações otimizadas"""
    
    def __init__(self):
        # Configurações específicas para CSFloat
        super().__init__(
            initial_delay=1.0,      # CSFloat recomenda 1 req/sec
            max_delay=30.0,         # Máximo 30s de delay
            backoff_factor=1.5,     # Crescimento moderado
            max_queue_size=500      # Fila menor para responsividade
        )
        
        logger.info("CSFloat Rate Limiter inicializado com configurações otimizadas")
    
    async def make_request(self, 
                          session: aiohttp.ClientSession,
                          method: str,
                          url: str,
                          **kwargs) -> aiohttp.ClientResponse:
        """
        Faz uma requisição HTTP com rate limiting automático.
        
        Args:
            session: Sessão aiohttp
            method: Método HTTP (GET, POST, etc.)
            url: URL da requisição
            **kwargs: Argumentos adicionais para a requisição
            
        Returns:
            Response da requisição
            
        Raises:
            aiohttp.ClientError: Em caso de erro na requisição
        """
        await self.acquire()
        
        try:
            async with session.request(method, url, **kwargs) as response:
                # Processar headers de rate limiting
                self.process_response_headers(dict(response.headers))
                
                if response.status == 200:
                    self.handle_success()
                else:
                    self.handle_error(response.status)
                
                return response
                
        except aiohttp.ClientError as e:
            self.handle_error()
            raise e

# Singleton global para uso em todo o projeto
csfloat_rate_limiter = CSFloatRateLimiter()