#!/usr/bin/env python3
"""
Script para verificar status atual do projeto após reinicialização
"""
import sqlite3
import os
from datetime import datetime

def check_database_status():
    """Verifica status do banco de dados"""
    print("=" * 60)
    print("🔍 VERIFICAÇÃO DO BANCO DE DADOS")
    print("=" * 60)
    
    db_path = 'data/skins.db'
    if not os.path.exists(db_path):
        print("❌ Banco de dados não encontrado!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar tabelas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"📋 TABELAS: {[t[0] for t in tables]}")
    
    # Verificar dados nas principais tabelas
    for table in ['skins', 'listings']:
        if (table,) in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"📊 {table.upper()}: {count:,} registros")
            
            # Últimos registros
            cursor.execute(f"SELECT * FROM {table} LIMIT 1")
            sample = cursor.fetchone()
            if sample:
                print(f"✅ Dados presentes em {table}")
    
    # Verificar colunas da tabela listings
    if ('listings',) in tables:
        cursor.execute("PRAGMA table_info(listings)")
        cols = cursor.fetchall()
        print(f"🗂️ COLUNAS LISTINGS: {[c[1] for c in cols]}")
    
    conn.close()

def check_logs():
    """Verifica logs recentes"""
    print("\n" + "=" * 60)
    print("📋 VERIFICAÇÃO DE LOGS")
    print("=" * 60)
    
    log_dir = 'logs'
    if os.path.exists(log_dir):
        log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
        for log_file in log_files[-5:]:  # Últimos 5 logs
            size = os.path.getsize(os.path.join(log_dir, log_file))
            print(f"📄 {log_file}: {size} bytes")

def check_project_files():
    """Verifica arquivos importantes do projeto"""
    print("\n" + "=" * 60)
    print("📁 VERIFICAÇÃO DE ARQUIVOS")
    print("=" * 60)
    
    important_files = [
        'scale_collection.py',
        'src/services/csfloat_service.py',
        'src/models/database.py',
        'src/collectors/realtime_collector.py',
        'daily_morning_report.py'
    ]
    
    for file in important_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"✅ {file}: {size} bytes")
        else:
            print(f"❌ {file}: NÃO ENCONTRADO")

if __name__ == "__main__":
    print("🚀 SKINLYTICS - VERIFICAÇÃO DE STATUS")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    check_database_status()
    check_logs()
    check_project_files()
    
    print("\n" + "=" * 60)
    print("✅ VERIFICAÇÃO CONCLUÍDA!")
    print("=" * 60)