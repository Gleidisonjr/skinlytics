#!/usr/bin/env python3
"""
🔍 SKINLYTICS DATABASE EXPLORER
Script interativo para explorar e consultar o banco de dados
"""
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os

class DatabaseExplorer:
    def __init__(self, db_path='data/skins.db'):
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """Conecta ao banco de dados"""
        if not os.path.exists(self.db_path):
            print(f"❌ Banco de dados não encontrado: {self.db_path}")
            return False
        
        self.conn = sqlite3.connect(self.db_path)
        print(f"✅ Conectado ao banco: {self.db_path}")
        return True
    
    def get_stats(self):
        """Mostra estatísticas gerais do banco"""
        if not self.conn:
            return
        
        print("\n" + "="*60)
        print("📊 ESTATÍSTICAS GERAIS")
        print("="*60)
        
        cursor = self.conn.cursor()
        
        # Total de skins
        cursor.execute("SELECT COUNT(*) FROM skins")
        total_skins = cursor.fetchone()[0]
        print(f"🎯 Total de Skins: {total_skins:,}")
        
        # Total de listings
        cursor.execute("SELECT COUNT(*) FROM listings")
        total_listings = cursor.fetchone()[0]
        print(f"📦 Total de Listings: {total_listings:,}")
        
        # Valor total (assumindo que o preço está em centavos USD)
        cursor.execute("SELECT SUM(price_usd) FROM listings WHERE price_usd IS NOT NULL")
        total_value = cursor.fetchone()[0]
        if total_value:
            print(f"💰 Valor Total: ${total_value:,.2f}")
        
        # Média de preços
        cursor.execute("SELECT AVG(price_usd) FROM listings WHERE price_usd IS NOT NULL")
        avg_price = cursor.fetchone()[0]
        if avg_price:
            print(f"💵 Preço Médio: ${avg_price:,.2f}")
        
        # Última coleta
        cursor.execute("SELECT MAX(collected_at) FROM listings")
        last_collect = cursor.fetchone()[0]
        if last_collect:
            print(f"🕐 Última Coleta: {last_collect}")
        
        # Top 5 skins mais caras
        print(f"\n🏆 TOP 5 SKINS MAIS CARAS:")
        cursor.execute("""
            SELECT l.item_name, l.price_usd, l.wear_name, l.float_value
            FROM listings l
            WHERE l.price_usd IS NOT NULL
            ORDER BY l.price_usd DESC
            LIMIT 5
        """)
        
        for i, (item, price, wear, float_val) in enumerate(cursor.fetchall(), 1):
            print(f"  {i}. {item} ({wear}) - ${price:,.2f} (Float: {float_val:.4f})")
    
    def search_skins(self, search_term):
        """Busca skins por nome"""
        if not self.conn:
            return
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT l.item_name, l.price_usd, l.wear_name, l.float_value, l.collected_at
            FROM listings l
            WHERE l.item_name LIKE ? 
            ORDER BY l.price_usd DESC
            LIMIT 20
        """, (f"%{search_term}%",))
        
        results = cursor.fetchall()
        if results:
            print(f"\n🔍 RESULTADOS PARA '{search_term}' ({len(results)} encontrados):")
            print("-" * 80)
            for item, price, wear, float_val, collected in results:
                print(f"💎 {item} ({wear}) - ${price:,.2f} | Float: {float_val:.4f} | {collected}")
        else:
            print(f"❌ Nenhuma skin encontrada com '{search_term}'")
    
    def get_collection_growth(self):
        """Mostra crescimento da coleta nas últimas horas"""
        if not self.conn:
            return
        
        cursor = self.conn.cursor()
        
        # Últimas 24 horas
        cursor.execute("""
            SELECT 
                DATE(collected_at) as date,
                COUNT(*) as count
            FROM listings 
            WHERE collected_at >= datetime('now', '-7 days')
            GROUP BY DATE(collected_at)
            ORDER BY date DESC
        """)
        
        print(f"\n📈 CRESCIMENTO DOS DADOS (ÚLTIMOS 7 DIAS):")
        print("-" * 40)
        for date, count in cursor.fetchall():
            print(f"📅 {date}: +{count:,} listings")
    
    def custom_query(self, query):
        """Executa uma query personalizada"""
        if not self.conn:
            return
        
        try:
            df = pd.read_sql_query(query, self.conn)
            print("\n📊 RESULTADO DA QUERY:")
            print(df.to_string(index=False))
            return df
        except Exception as e:
            print(f"❌ Erro na query: {e}")
    
    def show_tables(self):
        """Mostra estrutura das tabelas"""
        if not self.conn:
            return
        
        cursor = self.conn.cursor()
        
        # Listar tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"\n🗄️ TABELAS NO BANCO:")
        for table in tables:
            table_name = table[0]
            print(f"\n📋 {table_name.upper()}:")
            
            # Mostrar colunas
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            for col in columns:
                col_name, col_type, not_null, default, pk = col[1], col[2], col[3], col[4], col[5]
                pk_marker = " (PK)" if pk else ""
                print(f"  • {col_name}: {col_type}{pk_marker}")
    
    def close(self):
        """Fecha conexão"""
        if self.conn:
            self.conn.close()
            print("🔌 Conexão fechada")

def main():
    """Menu interativo"""
    explorer = DatabaseExplorer()
    
    if not explorer.connect():
        return
    
    print("\n🚀 SKINLYTICS DATABASE EXPLORER")
    print("Digite 'help' para ver comandos disponíveis")
    
    while True:
        try:
            command = input("\n> ").strip().lower()
            
            if command in ['exit', 'quit', 'q']:
                break
            elif command == 'help':
                print("""
📋 COMANDOS DISPONÍVEIS:
  stats     - Estatísticas gerais
  tables    - Mostrar estrutura das tabelas  
  growth    - Crescimento da coleta
  search    - Buscar skins (ex: search ak-47)
  query     - Query personalizada (ex: query SELECT * FROM skins LIMIT 5)
  help      - Esta ajuda
  exit      - Sair
                """)
            elif command == 'stats':
                explorer.get_stats()
            elif command == 'tables':
                explorer.show_tables()
            elif command == 'growth':
                explorer.get_collection_growth()
            elif command.startswith('search '):
                search_term = command[7:]
                explorer.search_skins(search_term)
            elif command.startswith('query '):
                query = command[6:]
                explorer.custom_query(query)
            else:
                print("❌ Comando não reconhecido. Digite 'help' para ajuda.")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    explorer.close()
    print("👋 Até logo!")

if __name__ == "__main__":
    main()