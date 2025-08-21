#!/usr/bin/env python3
"""
🧪 TESTE DAS APIS CONFIÁVEIS
Verifica se Pricempire e Steam Market APIs estão funcionando
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

async def test_pricempire_api():
    """Testa Pricempire API"""
    print("💰 Testando Pricempire API...")
    
    url = "https://api.pricempire.com/v2/getItems"
    params = {
        'game': 'cs2',
        'limit': 5
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                print(f"   Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Sucesso! {len(data.get('data', []))} items retornados")
                    
                    # Mostrar primeiro item como exemplo
                    if data.get('data'):
                        first_item = data['data'][0]
                        print(f"   📝 Exemplo: {first_item.get('market_hash_name', 'N/A')}")
                        print(f"      Preço: ${first_item.get('price', 'N/A')}")
                    
                    return True
                else:
                    print(f"   ❌ Erro HTTP: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False

async def test_steam_market_api():
    """Testa Steam Market API"""
    print("🎮 Testando Steam Market API...")
    
    # Testar com uma skin popular
    test_skin = "AK-47 | Redline (Field-Tested)"
    
    url = "https://steamcommunity.com/market/priceoverview/"
    params = {
        'appid': '730',  # CS2
        'currency': '1',  # USD
        'market_hash_name': test_skin
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                print(f"   Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Sucesso! Dados retornados para {test_skin}")
                    
                    if data.get('success'):
                        print(f"   📝 Preço médio: {data.get('median_price', 'N/A')}")
                        print(f"      Volume: {data.get('volume', 'N/A')}")
                        print(f"      Status: {data.get('success')}")
                    else:
                        print(f"   ⚠️ API retornou success=False")
                    
                    return True
                else:
                    print(f"   ❌ Erro HTTP: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False

async def test_rate_limiting():
    """Testa rate limiting das APIs"""
    print("⏱️ Testando rate limiting...")
    
    # Testar Pricempire com múltiplas requests
    print("   Testando Pricempire (5 requests rápidos)...")
    
    start_time = time.time()
    success_count = 0
    
    for i in range(5):
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.pricempire.com/v2/getItems"
                params = {'game': 'cs2', 'limit': 1}
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        success_count += 1
                        print(f"      Request {i+1}: ✅")
                    else:
                        print(f"      Request {i+1}: ❌ HTTP {response.status}")
                
                # Pequeno delay entre requests
                await asyncio.sleep(0.1)
                
        except Exception as e:
            print(f"      Request {i+1}: ❌ Erro: {e}")
    
    elapsed_time = time.time() - start_time
    print(f"   ⏱️ Tempo total: {elapsed_time:.2f}s")
    print(f"   📊 Taxa de sucesso: {success_count}/5 ({success_count/5*100:.0f}%)")
    
    return success_count >= 4  # Pelo menos 80% de sucesso

async def main():
    """Função principal de teste"""
    print("🚀 INICIANDO TESTES DAS APIS CONFIÁVEIS")
    print("=" * 50)
    
    results = {}
    
    # Teste 1: Pricempire API
    results['pricempire'] = await test_pricempire_api()
    print()
    
    # Teste 2: Steam Market API
    results['steam_market'] = await test_steam_market_api()
    print()
    
    # Teste 3: Rate Limiting
    results['rate_limiting'] = await test_rate_limiting()
    print()
    
    # Resumo dos resultados
    print("📊 RESUMO DOS TESTES")
    print("=" * 50)
    
    for api, success in results.items():
        status = "✅ FUNCIONANDO" if success else "❌ FALHOU"
        print(f"   {api.replace('_', ' ').title()}: {status}")
    
    # Recomendação
    working_apis = sum(results.values())
    total_apis = len(results)
    
    print(f"\n🎯 RESULTADO: {working_apis}/{total_apis} APIs funcionando")
    
    if working_apis >= 2:
        print("✅ SISTEMA PRONTO PARA USO!")
        print("💡 Execute: python reliable_collector.py")
        print("💡 Dashboard: streamlit run dashboard_reliable.py")
    elif working_apis >= 1:
        print("⚠️ SISTEMA PARCIALMENTE FUNCIONAL")
        print("💡 Algumas APIs estão funcionando, mas verifique os problemas")
    else:
        print("❌ SISTEMA NÃO FUNCIONA")
        print("💡 Verifique sua conexão com a internet e tente novamente")

if __name__ == "__main__":
    asyncio.run(main())
