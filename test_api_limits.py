#!/usr/bin/env python3
"""
CSFloat API Limits Tester

Script para testar e documentar os limites reais da API CSFloat,
incluindo rate limiting, throttling e capacidade de resposta.

Funcionalidades:
    - Teste de rate limits em diferentes endpoints
    - Monitoramento de headers de resposta
    - Análise de performance e latência
    - Geração de relatório detalhado

Usage:
    python test_api_limits.py --duration 60 --requests 100
"""

import asyncio
import aiohttp
import time
import json
import os
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class APITestResult:
    """Resultado de um teste de API"""
    endpoint: str
    method: str
    status_code: int
    response_time: float
    headers: Dict[str, str]
    rate_limit_info: Dict[str, Any]
    timestamp: datetime
    error: Optional[str] = None
    
class CSFloatAPITester:
    """Testador de limites da API CSFloat"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://csfloat.com/api/v1"
        self.results: List[APITestResult] = []
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        headers = {
            'User-Agent': 'CS2-Skin-Tracker-Tester/2.0',
            'Accept': 'application/json'
        }
        
        if self.api_key:
            headers['Authorization'] = self.api_key
        
        self.session = aiohttp.ClientSession(
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _extract_rate_limit_info(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """Extrai informações de rate limiting dos headers"""
        rate_info = {}
        
        # Headers de rate limiting comuns
        rate_headers = {
            'x-ratelimit-limit': 'limit',
            'x-ratelimit-remaining': 'remaining', 
            'x-ratelimit-reset': 'reset',
            'retry-after': 'retry_after',
            'ratelimit-limit': 'limit_alt',
            'ratelimit-remaining': 'remaining_alt',
            'ratelimit-reset': 'reset_alt'
        }
        
        for header, key in rate_headers.items():
            value = headers.get(header) or headers.get(header.upper())
            if value:
                try:
                    # Tentar converter para int
                    rate_info[key] = int(value)
                except ValueError:
                    rate_info[key] = value
        
        return rate_info
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> APITestResult:
        """Faz uma requisição e registra o resultado"""
        url = f"{self.base_url}/{endpoint}"
        start_time = time.time()
        
        try:
            async with self.session.get(url, params=params) as response:
                response_time = time.time() - start_time
                
                # Tentar ler resposta
                try:
                    await response.text()
                except Exception:
                    pass  # Não é crítico para o teste
                
                result = APITestResult(
                    endpoint=endpoint,
                    method="GET",
                    status_code=response.status,
                    response_time=response_time,
                    headers=dict(response.headers),
                    rate_limit_info=self._extract_rate_limit_info(dict(response.headers)),
                    timestamp=datetime.now()
                )
                
                return result
                
        except Exception as e:
            response_time = time.time() - start_time
            
            result = APITestResult(
                endpoint=endpoint,
                method="GET", 
                status_code=0,
                response_time=response_time,
                headers={},
                rate_limit_info={},
                timestamp=datetime.now(),
                error=str(e)
            )
            
            return result
    
    async def test_listings_endpoint(self, num_requests: int = 10, delay: float = 1.0) -> List[APITestResult]:
        """Testa o endpoint de listings"""
        logger.info(f"🧪 Testando endpoint listings - {num_requests} requisições com {delay}s delay")
        
        results = []
        
        for i in range(num_requests):
            if i > 0:
                await asyncio.sleep(delay)
            
            params = {
                'page': i,
                'limit': 10,  # Pequeno para não sobrecarregar
                'sort_by': 'most_recent'
            }
            
            result = await self._make_request('listings', params)
            results.append(result)
            self.results.append(result)
            
            # Log do progresso
            status_emoji = "✅" if result.status_code == 200 else "❌"
            rate_info = result.rate_limit_info
            remaining = rate_info.get('remaining', 'N/A')
            
            logger.info(f"{status_emoji} Req {i+1}/{num_requests}: "
                       f"{result.status_code} ({result.response_time:.2f}s) "
                       f"- Remaining: {remaining}")
            
            # Parar se hit rate limit
            if result.status_code == 429:
                logger.warning("⚠️ Rate limit atingido - parando teste")
                break
        
        return results
    
    async def test_burst_requests(self, num_requests: int = 5) -> List[APITestResult]:
        """Testa requisições em rajada (sem delay)"""
        logger.info(f"💥 Testando requisições em rajada - {num_requests} simultâneas")
        
        tasks = []
        
        for i in range(num_requests):
            params = {
                'page': 0,
                'limit': 5,
                'sort_by': 'most_recent'
            }
            task = self._make_request('listings', params)
            tasks.append(task)
        
        # Executar todas simultaneamente
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processar resultados
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, APITestResult):
                valid_results.append(result)
                self.results.append(result)
                
                status_emoji = "✅" if result.status_code == 200 else "❌"
                logger.info(f"{status_emoji} Burst {i+1}: "
                           f"{result.status_code} ({result.response_time:.2f}s)")
            else:
                logger.error(f"❌ Burst {i+1}: Exceção - {result}")
        
        return valid_results
    
    async def test_different_endpoints(self) -> List[APITestResult]:
        """Testa diferentes endpoints disponíveis"""
        logger.info("🔍 Testando diferentes endpoints")
        
        # Endpoints para testar (alguns podem não existir)
        test_endpoints = [
            ('listings', {'limit': 5}),
            ('market/search', {'query': 'AK-47'}),
            ('items/float', {'inspect_url': 'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20S76561198084749846A35418888340D16085414346054800717'}),
        ]
        
        results = []
        
        for endpoint, params in test_endpoints:
            result = await self._make_request(endpoint, params)
            results.append(result)
            self.results.append(result)
            
            status_emoji = "✅" if result.status_code == 200 else "❌"
            logger.info(f"{status_emoji} {endpoint}: {result.status_code}")
            
            # Delay entre diferentes endpoints
            await asyncio.sleep(1.0)
        
        return results
    
    def generate_report(self) -> Dict[str, Any]:
        """Gera relatório detalhado dos testes"""
        if not self.results:
            return {"error": "Nenhum resultado para analisar"}
        
        # Estatísticas básicas
        total_requests = len(self.results)
        successful_requests = len([r for r in self.results if r.status_code == 200])
        failed_requests = total_requests - successful_requests
        
        # Análise de rate limiting
        rate_limited = len([r for r in self.results if r.status_code == 429])
        
        # Análise de timing
        response_times = [r.response_time for r in self.results if r.response_time > 0]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Rate limit info do último resultado com dados
        last_rate_info = {}
        for result in reversed(self.results):
            if result.rate_limit_info:
                last_rate_info = result.rate_limit_info
                break
        
        # Análise temporal
        if len(self.results) >= 2:
            start_time = self.results[0].timestamp
            end_time = self.results[-1].timestamp
            duration = (end_time - start_time).total_seconds()
            requests_per_second = total_requests / duration if duration > 0 else 0
        else:
            duration = 0
            requests_per_second = 0
        
        # Códigos de status
        status_codes = {}
        for result in self.results:
            status_codes[result.status_code] = status_codes.get(result.status_code, 0) + 1
        
        report = {
            "summary": {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "success_rate": (successful_requests / total_requests * 100) if total_requests > 0 else 0,
                "rate_limited_requests": rate_limited,
                "duration_seconds": duration,
                "requests_per_second": requests_per_second
            },
            "performance": {
                "avg_response_time": avg_response_time,
                "min_response_time": min(response_times) if response_times else 0,
                "max_response_time": max(response_times) if response_times else 0
            },
            "rate_limiting": {
                "last_known_limit": last_rate_info.get('limit'),
                "last_known_remaining": last_rate_info.get('remaining'),
                "detected_headers": list(set([
                    header for result in self.results 
                    for header in result.rate_limit_info.keys()
                ]))
            },
            "status_codes": status_codes,
            "recommendations": self._generate_recommendations(),
            "timestamp": datetime.now().isoformat()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Gera recomendações baseadas nos resultados"""
        recommendations = []
        
        if not self.results:
            return ["Nenhum teste executado"]
        
        # Análise de rate limiting
        rate_limited = len([r for r in self.results if r.status_code == 429])
        if rate_limited > 0:
            recommendations.append(f"⚠️ {rate_limited} requisições foram rate limited - reduza a frequência")
        
        # Análise de response time
        response_times = [r.response_time for r in self.results if r.response_time > 0]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            if avg_time > 2.0:
                recommendations.append(f"🐌 Tempo de resposta alto ({avg_time:.2f}s) - considere cache")
        
        # Análise de success rate
        total = len(self.results)
        successful = len([r for r in self.results if r.status_code == 200])
        success_rate = (successful / total * 100) if total > 0 else 0
        
        if success_rate < 90:
            recommendations.append(f"❌ Taxa de sucesso baixa ({success_rate:.1f}%) - verifique API key")
        elif success_rate > 95:
            recommendations.append("✅ Taxa de sucesso excelente - configuração otimizada")
        
        # Rate limit específico
        last_rate_info = {}
        for result in reversed(self.results):
            if result.rate_limit_info:
                last_rate_info = result.rate_limit_info
                break
        
        if last_rate_info.get('remaining'):
            remaining = last_rate_info['remaining']
            limit = last_rate_info.get('limit', 100)
            usage = ((limit - remaining) / limit * 100) if limit > 0 else 0
            
            if usage > 80:
                recommendations.append(f"⚠️ Rate limit alto ({usage:.1f}%) - implemente delay de {1.2}s")
            elif usage < 50:
                recommendations.append(f"✅ Rate limit OK ({usage:.1f}%) - pode aumentar frequência")
        
        return recommendations

async def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Testador de limites da API CSFloat")
    parser.add_argument("--duration", type=int, default=60, help="Duração do teste em segundos")
    parser.add_argument("--requests", type=int, default=20, help="Número de requisições para teste")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay entre requisições")
    parser.add_argument("--output", type=str, default="api_test_report.json", help="Arquivo de saída")
    
    args = parser.parse_args()
    
    # Verificar API key
    api_key = os.getenv('CSFLOAT_API_KEY')
    if not api_key:
        logger.error("❌ CSFLOAT_API_KEY não encontrada nas variáveis de ambiente")
        return
    
    logger.info("🚀 Iniciando teste de limites da API CSFloat")
    logger.info(f"📊 Configuração: {args.requests} requisições, {args.delay}s delay")
    
    async with CSFloatAPITester(api_key) as tester:
        try:
            # Teste 1: Requisições sequenciais
            await tester.test_listings_endpoint(args.requests, args.delay)
            
            # Aguardar um pouco
            await asyncio.sleep(5)
            
            # Teste 2: Requisições em rajada
            await tester.test_burst_requests(5)
            
            # Aguardar um pouco
            await asyncio.sleep(5)
            
            # Teste 3: Diferentes endpoints
            await tester.test_different_endpoints()
            
        except KeyboardInterrupt:
            logger.info("⚠️ Teste interrompido pelo usuário")
        except Exception as e:
            logger.error(f"❌ Erro durante teste: {e}")
    
    # Gerar relatório
    logger.info("📊 Gerando relatório...")
    report = tester.generate_report()
    
    # Salvar relatório
    output_file = Path(args.output)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    
    # Mostrar resumo
    summary = report['summary']
    logger.info("=" * 60)
    logger.info("📊 RELATÓRIO DE TESTE DA API CSFLOAT")
    logger.info("=" * 60)
    logger.info(f"📡 Total de requisições: {summary['total_requests']}")
    logger.info(f"✅ Requisições bem-sucedidas: {summary['successful_requests']}")
    logger.info(f"❌ Requisições com falha: {summary['failed_requests']}")
    logger.info(f"📈 Taxa de sucesso: {summary['success_rate']:.1f}%")
    logger.info(f"⚠️ Rate limited: {summary['rate_limited_requests']}")
    logger.info(f"⏱️ Duração: {summary['duration_seconds']:.1f}s")
    logger.info(f"🚀 Req/s: {summary['requests_per_second']:.2f}")
    logger.info(f"📄 Relatório completo: {output_file}")
    
    # Mostrar recomendações
    if report['recommendations']:
        logger.info("\n💡 RECOMENDAÇÕES:")
        for rec in report['recommendations']:
            logger.info(f"   {rec}")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())