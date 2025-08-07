#!/usr/bin/env python3
"""
📊 MONITOR DE COLETA EM TEMPO REAL
- Monitora logs do collector
- Mostra estatísticas do banco
- Atualização automática
"""

import os
import time
import psutil
import sqlite3
from sqlalchemy import create_engine, text
from datetime import datetime
import json

def get_database_stats():
    """Obtém estatísticas do banco"""
    try:
        if 'DATABASE_URL' in os.environ:
            engine = create_engine(os.environ['DATABASE_URL'])
        else:
            engine = create_engine('sqlite:///data/skins_saas.db')
            
        with engine.connect() as conn:
            # Contar skins
            result = conn.execute(text("SELECT COUNT(*) FROM skins_optimized"))
            skins_count = result.fetchone()[0]
            
            # Contar listings
            result = conn.execute(text("SELECT COUNT(*) FROM listings_optimized"))
            listings_count = result.fetchone()[0]
            
            # Valor total
            result = conn.execute(text("SELECT SUM(price) FROM listings_optimized WHERE price > 0"))
            total_value = result.fetchone()[0] or 0
            
            # Última atualização
            result = conn.execute(text("""
                SELECT MAX(collected_at) FROM listings_optimized
            """))
            last_update = result.fetchone()[0]
            
            return {
                'skins': skins_count,
                'listings': listings_count,
                'total_value': total_value / 100,  # Converter para USD
                'last_update': last_update
            }
            
    except Exception as e:
        return {
            'skins': 0,
            'listings': 0,
            'total_value': 0,
            'last_update': None,
            'error': str(e)
        }

def get_collector_status():
    """Verifica status do collector"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if proc.info['name'] == 'python.exe':
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'optimized_collector.py' in cmdline:
                    return {
                        'running': True,
                        'pid': proc.info['pid'],
                        'cpu_percent': proc.cpu_percent(),
                        'memory_mb': proc.memory_info().rss / 1024 / 1024
                    }
        return {'running': False}
    except Exception as e:
        return {'running': False, 'error': str(e)}

def monitor_logs():
    """Monitora logs do collector"""
    log_file = 'collector.log'
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return lines[-10:] if lines else []
        except Exception as e:
            return [f"Erro ao ler log: {e}"]
    return ["Log file não encontrado"]

def clear_screen():
    """Limpa a tela"""
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    """Função principal do monitor"""
    print("📊 MONITOR DE COLETA EM TEMPO REAL")
    print("=" * 50)
    
    iteration = 0
    while True:
        iteration += 1
        current_time = datetime.now().strftime("%H:%M:%S")
        
        clear_screen()
        print(f"🕐 [{current_time}] Monitor - Iteração {iteration}")
        print("=" * 50)
        
        # Status do collector
        collector_status = get_collector_status()
        print("🔍 STATUS DO COLLECTOR:")
        if collector_status['running']:
            print(f"   ✅ Rodando (PID: {collector_status['pid']})")
            print(f"   CPU: {collector_status['cpu_percent']:.1f}%")
            print(f"   RAM: {collector_status['memory_mb']:.1f} MB")
        else:
            print("   ❌ Parado")
            
        # Estatísticas do banco
        db_stats = get_database_stats()
        print("\n🗄️ ESTATÍSTICAS DO BANCO:")
        print(f"   🎨 Skins: {db_stats['skins']:,}")
        print(f"   📦 Listings: {db_stats['listings']:,}")
        print(f"   💰 Valor Total: ${db_stats['total_value']:,.2f}")
        
        if db_stats['last_update']:
            print(f"   🕐 Última atualização: {db_stats['last_update']}")
        else:
            print("   ⏳ Aguardando dados...")
            
        # Logs recentes
        logs = monitor_logs()
        print(f"\n📝 LOGS RECENTES ({len(logs)} linhas):")
        for log in logs[-5:]:  # Últimas 5 linhas
            print(f"   {log.strip()}")
            
        # Progresso
        if db_stats['listings'] > 0:
            print(f"\n📈 PROGRESSO:")
            print(f"   🎯 Listings coletados: {db_stats['listings']:,}")
            print(f"   🎨 Skins únicas: {db_stats['skins']:,}")
            print(f"   💰 Valor médio: ${db_stats['total_value']/max(db_stats['listings'], 1):.2f}")
            
        print(f"\n⏳ Atualizando em 10s... (Ctrl+C para sair)")
        
        try:
            time.sleep(10)
        except KeyboardInterrupt:
            print("\n👋 Monitor finalizado!")
            break

if __name__ == "__main__":
    main()
