#!/usr/bin/env python3
"""
🇨🇳 BUFF163 COLLECTOR - Coletor da Maior Plataforma de Skins CS2
Buff163 é a maior plataforma chinesa com dados muito mais ricos
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
import re

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('buff163_collector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Buff163Collector:
    def __init__(self):
        self.session = None
        self.base_url = "https://buff.163.com"
        
        # Headers para simular navegador real
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        
        # Rate limiting
        self.requests = 0
        self.last_reset = time.time()
        self.delay = 3.0  # 3 segundos entre requests (mais conservador)
        
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        connector = aiohttp.TCPConnector(limit=5, limit_per_host=2)
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers=self.headers,
            cookie_jar=aiohttp.CookieJar()
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _respect_rate_limit(self):
        """Respeita rate limiting"""
        current_time = time.time()
        
        if current_time - self.last_reset >= 60:
            self.requests = 0
            self.last_reset = current_time
        
        if self.requests >= 20:  # 20 requests/min (conservador)
            wait_time = 60 - (current_time - self.last_reset)
            if wait_time > 0:
                logger.info(f"Rate limit atingido. Aguardando {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
                self.requests = 0
                self.last_reset = current_time
        
        self.requests += 1
        await asyncio.sleep(self.delay)
    
    async def get_cs2_market_page(self, page: int = 1) -> Optional[str]:
        """Obtém página do mercado CS2 do Buff163"""
        try:
            await self._respect_rate_limit()
            
            # URL do mercado CS2
            url = f"{self.base_url}/market/csgo"
            if page > 1:
                url += f"?page={page}"
            
            logger.info(f"📄 Acessando página {page}: {url}")
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    logger.info(f"✅ Página {page} carregada com sucesso")
                    return content
                else:
                    logger.warning(f"❌ HTTP {response.status} para página {page}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Erro ao acessar página {page}: {e}")
            return None
    
    async def get_item_details(self, item_id: str) -> Optional[Dict]:
        """Obtém detalhes de um item específico"""
        try:
            await self._respect_rate_limit()
            
            url = f"{self.base_url}/goods/{item_id}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    return self._parse_item_page(content)
                else:
                    logger.warning(f"❌ HTTP {response.status} para item {item_id}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Erro ao obter detalhes do item {item_id}: {e}")
            return None
    
    def _parse_item_page(self, html_content: str) -> Optional[Dict]:
        """Extrai dados da página de item"""
        try:
            # Procurar por dados JSON embutidos
            json_pattern = r'window\.__INITIAL_STATE__\s*=\s*({.*?});'
            json_match = re.search(json_pattern, html_content, re.DOTALL)
            
            if json_match:
                json_data = json.loads(json_match.group(1))
                return self._extract_from_json(json_data)
            
            # Fallback: extrair dados básicos do HTML
            return self._extract_from_html(html_content)
            
        except Exception as e:
            logger.error(f"❌ Erro ao fazer parse da página: {e}")
            return None
    
    def _extract_from_json(self, json_data: Dict) -> Optional[Dict]:
        """Extrai dados do JSON embutido"""
        try:
            # Navegar pela estrutura JSON para encontrar dados do item
            if 'goods' in json_data:
                goods_data = json_data['goods']
                if 'detail' in goods_data:
                    detail = goods_data['detail']
                    
                    return {
                        'name': detail.get('name', ''),
                        'price': detail.get('price', 0),
                        'steam_price': detail.get('steam_price', 0),
                        'buff_price': detail.get('buff_price', 0),
                        'rarity': detail.get('rarity', ''),
                        'exterior': detail.get('exterior', ''),
                        'source': 'buff163_json'
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair do JSON: {e}")
            return None
    
    def _extract_from_html(self, html_content: str) -> Optional[Dict]:
        """Extrai dados básicos do HTML"""
        try:
            # Procurar por nome do item
            name_pattern = r'<title>(.*?)</title>'
            name_match = re.search(name_pattern, html_content)
            name = name_match.group(1) if name_match else ''
            
            # Procurar por preço
            price_pattern = r'[\$¥€]?\s*([\d,]+\.?\d*)'
            price_matches = re.findall(price_pattern, html_content)
            price = float(price_matches[0].replace(',', '')) if price_matches else 0
            
            return {
                'name': name,
                'price': price,
                'source': 'buff163_html'
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair do HTML: {e}")
            return None
    
    async def collect_cs2_data(self, max_pages: int = 2) -> Dict:
        """Coleta dados de múltiplas páginas"""
        logger.info("🎯 Iniciando coleta do Buff163 CS2")
        
        all_items = []
        
        for page in range(1, max_pages + 1):
            logger.info(f"📖 Processando página {page}/{max_pages}")
            
            html_content = await self.get_cs2_market_page(page)
            if html_content:
                # Extrair IDs de itens da página
                item_ids = self._extract_item_ids(html_content)
                logger.info(f"🔍 Encontrados {len(item_ids)} IDs de itens na página {page}")
                
                # Coletar detalhes dos primeiros 5 itens (para não sobrecarregar)
                for i, item_id in enumerate(item_ids[:5]):
                    logger.info(f"   📋 Coletando item {i+1}/5: {item_id}")
                    item_details = await self.get_item_details(item_id)
                    if item_details:
                        all_items.append(item_details)
                    
                    # Aguardar entre itens
                    await asyncio.sleep(2)
            else:
                logger.warning(f"⚠️ Falha ao carregar página {page}")
            
            # Aguardar entre páginas
            if page < max_pages:
                await asyncio.sleep(5)
        
        # Consolidar dados
        consolidated_data = {
            'metadata': {
                'total_items': len(all_items),
                'pages_scraped': max_pages,
                'collection_timestamp': datetime.now().isoformat(),
                'source': 'buff163_web_scraping',
                'method': 'direct_access'
            },
            'items': all_items
        }
        
        logger.info(f"🎯 Coleta concluída! {len(all_items)} itens coletados")
        return consolidated_data
    
    def _extract_item_ids(self, html_content: str) -> List[str]:
        """Extrai IDs de itens da página"""
        try:
            # Procurar por padrões de URL de itens
            id_pattern = r'/goods/(\d+)'
            item_ids = re.findall(id_pattern, html_content)
            
            # Remover duplicatas
            unique_ids = list(set(item_ids))
            
            return unique_ids[:10]  # Limitar a 10 IDs por página
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair IDs: {e}")
            return []
    
    def save_data(self, data: Dict, filename: str = None) -> str:
        """Salva dados coletados"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"buff163_collection_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Dados salvos em {filename}")
            return filename
        except Exception as e:
            logger.error(f"❌ Erro ao salvar dados: {e}")
            return None

async def main():
    """Função principal para teste"""
    logger.info("🚀 Iniciando Buff163 Collector")
    
    async with Buff163Collector() as collector:
        # Coletar dados
        data = await collector.collect_cs2_data(max_pages=2)
        
        if data and data['items']:
            # Salvar dados
            filename = collector.save_data(data)
            
            # Mostrar resumo
            logger.info("📊 RESUMO DA COLETA:")
            logger.info(f"   Total de itens: {data['metadata']['total_items']}")
            logger.info(f"   Páginas processadas: {data['metadata']['pages_scraped']}")
            logger.info(f"   Arquivo salvo: {filename}")
            
            # Mostrar alguns exemplos
            logger.info("\n💰 EXEMPLOS DE ITENS:")
            for i, item in enumerate(data['items'][:5]):
                price_str = f"${item['price']:.2f}" if item.get('price') else 'N/A'
                logger.info(f"   {i+1}. {item.get('name', 'N/A')}: {price_str}")
        else:
            logger.error("❌ Falha na coleta de dados")

if __name__ == "__main__":
    asyncio.run(main())
