#!/usr/bin/env python3
"""
📊 MONITOR DE PROGRESSO - Acompanha crescimento dos dados em tempo real
"""
import sqlite3
import time
import os
from datetime import datetime, timedelta
import json

class ProgressMonitor:
    def __init__(self, db_path='data/skins.db'):
        self.db_path = db_path
        self.last_stats = {}
        
    def get_current_stats(self):
        """Obtém estatísticas atuais do banco"""
        if not os.path.exists(self.db_path):
            return None
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        try:
            # Total de listings
            cursor.execute("SELECT COUNT(*) FROM listings")
            stats['total_listings'] = cursor.fetchone()[0]
            
            # Total de skins únicas
            cursor.execute("SELECT COUNT(DISTINCT item_name) FROM listings WHERE item_name IS NOT NULL")
            stats['unique_skins'] = cursor.fetchone()[0]
            
            # Valor total
            cursor.execute("SELECT SUM(price_usd) FROM listings WHERE price_usd IS NOT NULL")
            total_value = cursor.fetchone()[0]
            stats['total_value'] = total_value if total_value else 0
            
            # Última coleta
            cursor.execute("SELECT MAX(collected_at) FROM listings")
            stats['last_collection'] = cursor.fetchone()[0]
            
            # Coletas das últimas 24h
            cursor.execute("""
                SELECT COUNT(*) FROM listings 
                WHERE collected_at >= datetime('now', '-1 day')
            """)
            stats['last_24h'] = cursor.fetchone()[0]
            
            # Coletas da última hora
            cursor.execute("""
                SELECT COUNT(*) FROM listings 
                WHERE collected_at >= datetime('now', '-1 hour')
            """)
            stats['last_hour'] = cursor.fetchone()[0]
            
            # Top 5 skins mais caras
            cursor.execute("""
                SELECT item_name, price_usd, wear_name 
                FROM listings 
                WHERE price_usd IS NOT NULL 
                ORDER BY price_usd DESC 
                LIMIT 5
            """)
            stats['top_skins'] = cursor.fetchall()
            
            # Crescimento por hora (últimas 6 horas)
            cursor.execute("""
                SELECT 
                    strftime('%H', collected_at) as hour,
                    COUNT(*) as count
                FROM listings 
                WHERE collected_at >= datetime('now', '-6 hours')
                GROUP BY strftime('%H', collected_at)
                ORDER BY hour DESC
            """)
            stats['hourly_growth'] = cursor.fetchall()
            
            stats['timestamp'] = datetime.now()
            
        except Exception as e:
            print(f"❌ Erro ao obter estatísticas: {e}")
            return None
        finally:
            conn.close()
        
        return stats
    
    def calculate_growth_rate(self, current_stats):
        """Calcula taxa de crescimento"""
        if not self.last_stats:
            return None
        
        time_diff = (current_stats['timestamp'] - self.last_stats['timestamp']).total_seconds()
        if time_diff == 0:
            return None
        
        listings_diff = current_stats['total_listings'] - self.last_stats['total_listings']
        growth_rate = (listings_diff / time_diff) * 3600  # Por hora
        
        return {
            'listings_per_hour': growth_rate,
            'new_listings': listings_diff,
            'time_elapsed': time_diff / 60  # Em minutos
        }
    
    def print_dashboard(self, stats):
        """Imprime dashboard com estatísticas"""
        os.system('cls' if os.name == 'nt' else 'clear')  # Limpa tela
        
        print("🚀 SKINLYTICS - MONITOR DE PROGRESSO")
        print("=" * 70)
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if not stats:
            print("❌ Não foi possível obter estatísticas")
            return
        
        print(f"\n📊 DADOS GERAIS:")
        print(f"  📦 Total de Listings: {stats['total_listings']:,}")
        print(f"  🎯 Skins Únicas: {stats['unique_skins']:,}")
        print(f"  💰 Valor Total: ${stats['total_value']:,.2f}")
        print(f"  🕐 Última Coleta: {stats['last_collection'] or 'N/A'}")
        
        print(f"\n📈 CRESCIMENTO:")
        print(f"  📅 Últimas 24h: +{stats['last_24h']:,} listings")
        print(f"  ⏱️  Última hora: +{stats['last_hour']:,} listings")
        
        # Taxa de crescimento
        growth = self.calculate_growth_rate(stats)
        if growth:
            print(f"  🚀 Taxa atual: {growth['listings_per_hour']:.1f} listings/hora")
            print(f"  ⚡ Últimos {growth['time_elapsed']:.1f}min: +{growth['new_listings']} listings")
        
        print(f"\n🏆 TOP 5 SKINS MAIS CARAS:")
        for i, (name, price, wear) in enumerate(stats['top_skins'], 1):
            print(f"  {i}. {name} ({wear}) - ${price:,.2f}")
        
        print(f"\n📊 CRESCIMENTO POR HORA (ÚLTIMAS 6H):")
        for hour, count in stats['hourly_growth']:
            print(f"  {hour}:00 - {count:,} listings")
        
        print("=" * 70)
        print("💡 Pressione Ctrl+C para parar o monitoramento")
    
    def run_monitor(self, interval=30):
        """Executa monitoramento contínuo"""
        print("🚀 Iniciando monitor de progresso...")
        print(f"📊 Atualizando a cada {interval} segundos")
        
        try:
            while True:
                current_stats = self.get_current_stats()
                self.print_dashboard(current_stats)
                
                # Salvar estatísticas para próxima comparação
                if current_stats:
                    self.last_stats = current_stats
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n👋 Monitor interrompido pelo usuário")
        except Exception as e:
            print(f"\n❌ Erro no monitor: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor de Progresso Skinlytics')
    parser.add_argument('--interval', type=int, default=30, 
                      help='Intervalo de atualização em segundos (padrão: 30)')
    args = parser.parse_args()
    
    monitor = ProgressMonitor()
    monitor.run_monitor(interval=args.interval)

if __name__ == "__main__":
    main()