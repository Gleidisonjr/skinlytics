#!/usr/bin/env python3
"""
Script para testar conexão com banco Railway
"""

import os
import psycopg2
from sqlalchemy import create_engine, text
import pandas as pd

def test_railway_connection():
    """Testa conexão com Railway PostgreSQL"""
    print("🔍 Testando conexão com Railway PostgreSQL...")
    
    # Verificar se DATABASE_URL está configurada
    if 'DATABASE_URL' not in os.environ:
        print("❌ DATABASE_URL não encontrada")
        print("💡 Configure a variável DATABASE_URL no Railway")
        return False
    
    try:
        # Testar conexão
        engine = create_engine(os.environ['DATABASE_URL'])
        
        with engine.connect() as conn:
            print("✅ Conexão estabelecida com sucesso!")
            
            # Verificar se as tabelas existem
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            
            if tables:
                print(f"📊 Tabelas encontradas: {tables}")
                
                # Verificar dados em cada tabela
                for table in tables:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.fetchone()[0]
                    print(f"  - {table}: {count:,} registros")
            else:
                print("⚠️ Nenhuma tabela encontrada")
                print("💡 As tabelas serão criadas automaticamente no primeiro deploy")
            
            # Testar inserção simples
            try:
                result = conn.execute(text("SELECT 1 as test"))
                test_result = result.fetchone()
                print(f"✅ Teste de query: {test_result[0]}")
            except Exception as e:
                print(f"❌ Erro no teste de query: {e}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return False

def show_railway_instructions():
    """Mostra instruções para configurar Railway"""
    print("\n" + "="*50)
    print("🚀 INSTRUÇÕES PARA CONFIGURAR RAILWAY")
    print("="*50)
    
    print("\n1️⃣ ADICIONAR POSTGRESQL:")
    print("   - Vá para: https://railway.app/dashboard")
    print("   - Clique no projeto 'skinlytics'")
    print("   - Clique em 'New Service' → 'Database' → 'PostgreSQL'")
    print("   - Aguarde 'Deployed'")
    
    print("\n2️⃣ CONFIGURAR DATABASE_URL:")
    print("   - No serviço PostgreSQL, clique em 'Connect'")
    print("   - Copie a DATABASE_URL completa")
    print("   - No projeto principal, vá em 'Variables'")
    print("   - Adicione: Nome='DATABASE_URL', Valor=URL_copiada")
    
    print("\n3️⃣ VERIFICAR:")
    print("   - Execute: python test_railway_db.py")
    print("   - Confirme que a conexão funciona")
    
    print("\n4️⃣ DEPLOY:")
    print("   - O Railway fará deploy automático")
    print("   - As tabelas serão criadas automaticamente")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    success = test_railway_connection()
    
    if not success:
        show_railway_instructions()
    else:
        print("\n🎉 Banco configurado com sucesso!")
        print("💡 Agora você pode fazer o deploy no Railway")
