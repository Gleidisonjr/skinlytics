#!/usr/bin/env python3
"""
Monitor de deploy e banco de dados Railway
"""

import os
import time
import requests
import psycopg2
from sqlalchemy import create_engine, text
from datetime import datetime

def check_railway_status():
    """Verifica status do Railway"""
    try:
        # Tentar acessar o app
        response = requests.get("https://skinlytics-production.up.railway.app", timeout=10)
        if response.status_code == 200:
            return "✅ ONLINE"
        else:
            return f"⚠️ STATUS {response.status_code}"
    except Exception as e:
        return "❌ OFFLINE"

def check_database_connection():
    """Verifica conexão com banco"""
    try:
        if 'DATABASE_URL' not in os.environ:
            return "❌ DATABASE_URL não configurada"
        
        engine = create_engine(os.environ['DATABASE_URL'])
        with engine.connect() as conn:
            # Verificar tabelas
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            
            if tables:
                # Contar dados
                total_data = 0
                for table in tables:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.fetchone()[0]
                    total_data += count
                
                return f"✅ {len(tables)} tabelas, {total_data:,} registros"
            else:
                return "⚠️ Nenhuma tabela encontrada"
                
    except Exception as e:
        return f"❌ Erro: {str(e)[:50]}"

def check_collector_status():
    """Verifica se o collector está rodando"""
    try:
        # Verificar se há dados recentes no banco
        if 'DATABASE_URL' in os.environ:
            engine = create_engine(os.environ['DATABASE_URL'])
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT MAX(collected_at) as last_collection
                    FROM listings_optimized
                """))
                last_collection = result.fetchone()[0]
                
                if last_collection:
                    time_diff = datetime.now() - last_collection
                    if time_diff.total_seconds() < 3600:  # Menos de 1 hora
                        return f"✅ Última coleta: {time_diff.total_seconds()/60:.0f}min atrás"
                    else:
                        return f"⚠️ Última coleta: {time_diff.total_seconds()/3600:.1f}h atrás"
                else:
                    return "⚠️ Nenhuma coleta encontrada"
        else:
            return "❌ DATABASE_URL não configurada"
            
    except Exception as e:
        return f"❌ Erro: {str(e)[:50]}"

def monitor_loop():
    """Loop principal de monitoramento"""
    print("🚀 MONITOR DE DEPLOY RAILWAY")
    print("="*50)
    
    iteration = 0
    while True:
        iteration += 1
        current_time = datetime.now().strftime("%H:%M:%S")
        
        print(f"\n🕐 [{current_time}] Iteração {iteration}")
        print("-" * 30)
        
        # Verificar status do app
        app_status = check_railway_status()
        print(f"🌐 App Railway: {app_status}")
        
        # Verificar banco de dados
        db_status = check_database_connection()
        print(f"🗄️ Banco PostgreSQL: {db_status}")
        
        # Verificar collector
        collector_status = check_collector_status()
        print(f"📊 Collector: {collector_status}")
        
        # Status geral
        if "ONLINE" in app_status and "✅" in db_status:
            print("\n🎉 SISTEMA FUNCIONANDO!")
            print("💡 Acesse: https://skinlytics-production.up.railway.app")
            break
        elif iteration > 30:  # 5 minutos
            print("\n⏰ Timeout - Verifique manualmente")
            break
        else:
            print(f"\n⏳ Aguardando... ({iteration}/30)")
            time.sleep(10)  # 10 segundos

if __name__ == "__main__":
    try:
        monitor_loop()
    except KeyboardInterrupt:
        print("\n🛑 Monitoramento interrompido")
    except Exception as e:
        print(f"\n❌ Erro no monitoramento: {e}")
