#!/usr/bin/env python3
"""
🔍 INVESTIGAÇÃO PRICEMPIRE API
Descobre por que está retornando 403 Forbidden
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def investigate_pricempire():
    """Investiga diferentes abordagens para Pricempire API"""
    
    print("🔍 INVESTIGANDO PRICEMPIRE API")
    print("=" * 50)
    
    # Teste 1: Headers básicos
    print("\n1️⃣ Teste com headers básicos...")
    async with aiohttp.ClientSession() as session:
        url = "https://api.pricempire.com/v2/getItems"
        params = {'game': 'cs2', 'limit': 1}
        
        async with session.get(url, params=params) as response:
            print(f"   Status: {response.status}")
            print(f"   Headers: {dict(response.headers)}")
            if response.status != 200:
                text = await response.text()
                print(f"   Response: {text[:300]}")
    
    # Teste 2: Com User-Agent específico
    print("\n2️⃣ Teste com User-Agent específico...")
    async with aiohttp.ClientSession() as session:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        async with session.get(url, params=params, headers=headers) as response:
            print(f"   Status: {response.status}")
            if response.status != 200:
                text = await response.text()
                print(f"   Response: {text[:300]}")
    
    # Teste 3: Com referer
    print("\n3️⃣ Teste com referer...")
    async with aiohttp.ClientSession() as session:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://pricempire.com/'
        }
        
        async with session.get(url, params=params, headers=headers) as response:
            print(f"   Status: {response.status}")
            if response.status != 200:
                text = await response.text()
                print(f"   Response: {text[:300]}")
    
    # Teste 4: Endpoint diferente
    print("\n4️⃣ Teste endpoint diferente...")
    async with aiohttp.ClientSession() as session:
        test_url = "https://api.pricempire.com/v2/getPrice"
        test_params = {'item': 'AK-47 | Redline (Field-Tested)', 'currency': 'USD'}
        
        async with session.get(test_url, params=test_params, headers=headers) as response:
            print(f"   Status: {response.status}")
            if response.status != 200:
                text = await response.text()
                print(f"   Response: {text[:300]}")
    
    # Teste 5: Verificar documentação
    print("\n5️⃣ Verificando documentação...")
    async with aiohttp.ClientSession() as session:
        doc_url = "https://pricempire.com/api"
        
        async with session.get(doc_url) as response:
            print(f"   Status: {response.status}")
            if response.status == 200:
                content = await response.text()
                if "rate limit" in content.lower():
                    print("   ✅ Documentação encontrada")
                else:
                    print("   ⚠️ Documentação não encontrada")

async def test_alternative_approach():
    """Testa abordagem alternativa"""
    print("\n🔄 TESTANDO ABORDAGEM ALTERNATIVA")
    print("=" * 50)
    
    # Simular navegador real
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    
    async with aiohttp.ClientSession() as session:
        # Primeiro acessar a página principal
        print("   📄 Acessando página principal...")
        main_page = await session.get("https://pricempire.com/", headers=headers)
        print(f"      Status: {main_page.status}")
        
        # Depois tentar a API
        print("   🔌 Tentando API...")
        api_response = await session.get(
            "https://api.pricempire.com/v2/getItems?game=cs2&limit=1",
            headers=headers
        )
        print(f"      Status: {api_response.status}")
        
        if api_response.status == 200:
            data = await api_response.json()
            print(f"      ✅ Sucesso! Dados: {data}")
        else:
            text = await api_response.text()
            print(f"      ❌ Falha: {text[:200]}")

async def main():
    """Função principal"""
    print("🚀 INICIANDO INVESTIGAÇÃO COMPLETA")
    print("=" * 60)
    
    await investigate_pricempire()
    await test_alternative_approach()
    
    print("\n🎯 RECOMENDAÇÕES:")
    print("1. Verificar se precisa de API key")
    print("2. Verificar rate limiting")
    print("3. Verificar se precisa de autenticação")
    print("4. Considerar usar web scraping como fallback")

if __name__ == "__main__":
    asyncio.run(main())
