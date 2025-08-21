#!/usr/bin/env python3
"""
🌐 PRICEMPIRE SCRAPER - Coletor via Web Scraping
Contorna proteção Cloudflare e coleta dados diretamente do site
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
import re
from bs4 import BeautifulSoup

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pricempire_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PricempireScraper:
    def __init__(self):
        self.session = None
        self.base_url = "https://pricempire.com"
        
        # Headers para simular navegador real
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',  # Removido brotli
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
        self.delay = 2.0  # 2 segundos entre requests
        
    async def __aenter__(self):
        # Configurar timeout e cookies
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        
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
        
        if self.requests >= 30:  # 30 requests/min
            wait_time = 60 - (current_time - self.last_reset)
            if wait_time > 0:
                logger.info(f"Rate limit atingido. Aguardando {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
                self.requests = 0
                self.last_reset = current_time
        
        self.requests += 1
        await asyncio.sleep(self.delay)
    
    async def get_cs2_items_page(self, page: int = 1) -> Optional[str]:
        """Obtém página de itens CS2"""
        try:
            await self._respect_rate_limit()
            
            url = f"{self.base_url}/cs2"
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
    
    def parse_items_from_html(self, html_content: str) -> List[Dict]:
        """Extrai itens da página HTML"""
        items = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Procurar por cards de itens
            item_cards = soup.find_all('div', class_=re.compile(r'item-card|skin-card|price-card'))
            
            if not item_cards:
                # Tentar outras classes comuns
                item_cards = soup.find_all('div', class_=re.compile(r'card|item|skin'))
            
            logger.info(f"🔍 Encontrados {len(item_cards)} possíveis cards de itens")
            
            for card in item_cards[:20]:  # Limitar a 20 por página
                try:
                    item_data = self._extract_item_data(card)
                    if item_data:
                        items.append(item_data)
                except Exception as e:
                    logger.debug(f"Erro ao extrair item: {e}")
                    continue
            
            # Se não encontrou cards, tentar extrair de tabelas
            if not items:
                items = self._extract_from_tables(soup)
            
            # Se ainda não encontrou, tentar extrair de listas
            if not items:
                items = self._extract_from_lists(soup)
            
        except Exception as e:
            logger.error(f"❌ Erro ao fazer parse do HTML: {e}")
        
        return items
    
    def _extract_item_data(self, card) -> Optional[Dict]:
        """Extrai dados de um card de item"""
        try:
            # Nome do item
            name_elem = card.find(['h3', 'h4', 'h5', 'span', 'div'], 
                                class_=re.compile(r'title|name|item-name|skin-name'))
            if not name_elem:
                name_elem = card.find(['h3', 'h4', 'h5', 'span', 'div'])
            
            if not name_elem or not name_elem.get_text(strip=True):
                return None
            
            name = name_elem.get_text(strip=True)
            
            # Preço
            price_elem = card.find(['span', 'div'], 
                                 class_=re.compile(r'price|cost|value'))
            price = None
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                # Extrair número do preço
                price_match = re.search(r'[\d,]+\.?\d*', price_text)
                if price_match:
                    price = float(price_match.group().replace(',', ''))
            
            # Wear/Quality
            wear_elem = card.find(['span', 'div'], 
                                class_=re.compile(r'wear|quality|condition'))
            wear = None
            if wear_elem:
                wear = wear_elem.get_text(strip=True)
            
            # Imagem
            img_elem = card.find('img')
            image_url = None
            if img_elem and img_elem.get('src'):
                image_url = img_elem['src']
                if image_url.startswith('/'):
                    image_url = f"https://pricempire.com{image_url}"
            
            return {
                'name': name,
                'price': price,
                'wear': wear,
                'image_url': image_url,
                'source': 'pricempire_scraping'
            }
            
        except Exception as e:
            logger.debug(f"Erro ao extrair dados do card: {e}")
            return None
    
    def _extract_from_tables(self, soup) -> List[Dict]:
        """Extrai dados de tabelas"""
        items = []
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows[1:]:  # Pular header
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    name = cells[0].get_text(strip=True)
                    price_text = cells[1].get_text(strip=True)
                    
                    price_match = re.search(r'[\d,]+\.?\d*', price_text)
                    price = float(price_match.group().replace(',', '')) if price_match else None
                    
                    if name and price:
                        items.append({
                            'name': name,
                            'price': price,
                            'source': 'pricempire_table'
                        })
        
        return items
    
    def _extract_from_lists(self, soup) -> List[Dict]:
        """Extrai dados de listas"""
        items = []
        lists = soup.find_all(['ul', 'ol'])
        
        for list_elem in lists:
            list_items = list_elem.find_all('li')
            for li in list_items:
                text = li.get_text(strip=True)
                if text and len(text) > 10:  # Filtrar textos muito curtos
                    # Tentar extrair nome e preço
                    price_match = re.search(r'[\d,]+\.?\d*', text)
                    if price_match:
                        price = float(price_match.group().replace(',', ''))
                        name = text.replace(price_match.group(), '').strip()
                        
                        if name:
                            items.append({
                                'name': name,
                                'price': price,
                                'source': 'pricempire_list'
                            })
        
        return items
    
    async def collect_cs2_data(self, max_pages: int = 3) -> Dict:
        """Coleta dados de múltiplas páginas"""
        logger.info("🎯 Iniciando coleta via web scraping do Pricempire")
        
        all_items = []
        
        for page in range(1, max_pages + 1):
            logger.info(f"📖 Processando página {page}/{max_pages}")
            
            html_content = await self.get_cs2_items_page(page)
            if html_content:
                items = self.parse_items_from_html(html_content)
                all_items.extend(items)
                logger.info(f"✅ Página {page}: {len(items)} itens extraídos")
            else:
                logger.warning(f"⚠️ Falha ao carregar página {page}")
            
            # Aguardar entre páginas
            if page < max_pages:
                await asyncio.sleep(3)
        
        # Consolidar dados
        consolidated_data = {
            'metadata': {
                'total_items': len(all_items),
                'pages_scraped': max_pages,
                'collection_timestamp': datetime.now().isoformat(),
                'source': 'pricempire_web_scraping',
                'method': 'bypass_cloudflare'
            },
            'items': all_items
        }
        
        logger.info(f"🎯 Coleta concluída! {len(all_items)} itens coletados")
        return consolidated_data
    
    def save_data(self, data: Dict, filename: str = None) -> str:
        """Salva dados coletados"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pricempire_scraped_{timestamp}.json"
        
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
    logger.info("🚀 Iniciando Pricempire Scraper")
    
    async with PricempireScraper() as scraper:
        # Coletar dados
        data = await scraper.collect_cs2_data(max_pages=2)
        
        if data and data['items']:
            # Salvar dados
            filename = scraper.save_data(data)
            
            # Mostrar resumo
            logger.info("📊 RESUMO DA COLETA:")
            logger.info(f"   Total de itens: {data['metadata']['total_items']}")
            logger.info(f"   Páginas processadas: {data['metadata']['pages_scraped']}")
            logger.info(f"   Arquivo salvo: {filename}")
            
            # Mostrar alguns exemplos
            logger.info("\n💰 EXEMPLOS DE ITENS:")
            for i, item in enumerate(data['items'][:5]):
                price_str = f"${item['price']:.2f}" if item['price'] else 'N/A'
                logger.info(f"   {i+1}. {item['name']}: {price_str}")
        else:
            logger.error("❌ Falha na coleta de dados")

if __name__ == "__main__":
    asyncio.run(main())
