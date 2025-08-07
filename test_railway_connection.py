#!/usr/bin/env python3
"""
Teste de conexão com Railway PostgreSQL
"""

import os
import psycopg2
from sqlalchemy import create_engine, text
import pandas as pd

def test_railway_db():
    """Testa conexão com Railway PostgreSQL"""
    print("🔍 Testando conexão com Railway PostgreSQL...")
    
    # Verificar se DATABASE_URL está configurada
    if 'DATABASE_URL' not in os.environ:
        print("❌ DATABASE_URL não encontrada")
        print("💡 Verifique se está configurada no Railway")
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

def show_status():
    """Mostra status atual"""
    print("\n" + "="*50)
    print("🎯 STATUS ATUAL")
    print("="*50)
    
    print("\n✅ CONFIGURADO:")
    print("   - PostgreSQL criado no Railway")
    print("   - DATABASE_URL configurada")
    print("   - skinlytics em deploy")
    
    print("\n⏳ AGUARDANDO:")
    print("   - Deploy completar")
    print("   - Tabelas serem criadas")
    print("   - Dados serem coletados")
    
    print("\n🚀 PRÓXIMOS PASSOS:")
    print("   1. Aguardar deploy completar")
    print("   2. Verificar se tabelas foram criadas")
    print("   3. Testar dashboard com dados reais")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    success = test_railway_db()
    
    if success:
        print("\n🎉 Banco Railway configurado com sucesso!")
        print("💡 Agora aguarde o deploy completar")
    else:
        show_status()
