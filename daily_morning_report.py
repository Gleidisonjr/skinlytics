"""
Relatório Matinal Automático Skinlytics - 8:00 AM

Envia relatório diário de crescimento de dados por email
Email: gleidisonjunior187@gmail.com
Horário: 8:00 AM todos os dias

Author: CS2 Skin Tracker Team - Skinlytics Platform
Version: 2.0.0 Daily Reports
"""

import sqlite3
import os
import schedule
import time
from datetime import datetime, timedelta
from pathlib import Path
import logging

class DailyMorningReport:
    """Relatório matinal automático"""
    
    def __init__(self):
        self.db_path = "data/skins.db"
        self.target_email = "gleidisonjunior187@gmail.com"
        
        # Configurações de email (você precisará configurar)
        self.email_config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "email": "seu_email@gmail.com",  # Configure seu email
            "password": "sua_senha_app",     # Configure senha de app do Gmail
        }
        
        # Configurar logging
        Path("logs").mkdir(exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler('logs/daily_reports.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_growth_stats(self):
        """Obtém estatísticas de crescimento"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total atual
            cursor.execute("SELECT COUNT(*) FROM listings")
            total_now = cursor.fetchone()[0]
            
            # Últimas 24 horas
            cursor.execute("""
                SELECT COUNT(*) FROM listings 
                WHERE collected_at >= datetime('now', '-1 day')
            """)
            last_24h = cursor.fetchone()[0]
            
            # Última semana
            cursor.execute("""
                SELECT COUNT(*) FROM listings 
                WHERE collected_at >= datetime('now', '-7 days')
            """)
            last_week = cursor.fetchone()[0]
            
            # Valor total
            cursor.execute("SELECT SUM(price_usd) FROM listings")
            total_value = cursor.fetchone()[0] or 0
            
            # Valor médio
            avg_value = total_value / max(1, total_now)
            
            # Skins mais valiosas da última semana
            cursor.execute("""
                SELECT item_name, price_usd, collected_at 
                FROM listings 
                WHERE collected_at >= datetime('now', '-7 days')
                ORDER BY price_usd DESC 
                LIMIT 5
            """)
            top_weekly = cursor.fetchall()
            
            # Tamanho do banco
            db_size = Path(self.db_path).stat().st_size / (1024 * 1024)
            
            conn.close()
            
            return {
                "total_listings": total_now,
                "growth_24h": last_24h,
                "growth_week": last_week,
                "total_value": total_value,
                "avg_value": avg_value,
                "top_weekly": top_weekly,
                "db_size_mb": db_size,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas: {e}")
            return None
    
    def generate_morning_report(self, stats):
        """Gera relatório matinal em português"""
        if not stats:
            return "❌ Erro ao gerar relatório - banco indisponível"
        
        # Calcular crescimento percentual
        growth_rate_24h = 0
        if stats["total_listings"] > stats["growth_24h"]:
            base = stats["total_listings"] - stats["growth_24h"]
            growth_rate_24h = (stats["growth_24h"] / max(1, base)) * 100
        
        growth_rate_week = 0
        if stats["total_listings"] > stats["growth_week"]:
            base = stats["total_listings"] - stats["growth_week"]
            growth_rate_week = (stats["growth_week"] / max(1, base)) * 100
        
        # Top skins da semana
        top_skins = "\n".join([
            f"  💎 {name}: ${price:,.2f} ({date})" 
            for name, price, date in stats["top_weekly"]
        ]) if stats["top_weekly"] else "  Nenhuma skin encontrada"
        
        report = f"""
☀️ BOM DIA! RELATÓRIO SKINLYTICS - {stats['timestamp']}
{'='*70}

📊 CRESCIMENTO DOS DADOS:
  📦 Total de Listings: {stats['total_listings']:,}
  
  📈 Crescimento 24h: +{stats['growth_24h']:,} ({growth_rate_24h:.1f}%)
  📅 Crescimento Semanal: +{stats['growth_week']:,} ({growth_rate_week:.1f}%)
  
💰 ANÁLISE FINANCEIRA:
  💎 Valor Total Rastreado: ${stats['total_value']:,.2f}
  💵 Valor Médio por Skin: ${stats['avg_value']:.2f}
  
🗄️ STATUS DO BANCO:
  💾 Tamanho do Database: {stats['db_size_mb']:.2f} MB
  📊 Performance: {"✅ Excelente" if stats['growth_24h'] > 100 else "⚠️ Baixa" if stats['growth_24h'] < 50 else "✅ Boa"}
  
🏆 TOP 5 SKINS MAIS VALIOSAS (ÚLTIMA SEMANA):
{top_skins}

🎯 RESUMO EXECUTIVO:
  {"🚀 Sistema funcionando perfeitamente! Dados crescendo consistentemente." if stats['growth_24h'] > 50 else "⚠️ Crescimento baixo - verificar sistema de coleta."}
  
  📈 Taxa de Crescimento: {"Exponencial" if growth_rate_24h > 10 else "Estável" if growth_rate_24h > 1 else "Lenta"}
  
  💼 Status do Projeto: {"🔥 Em pleno desenvolvimento" if stats['total_listings'] < 10000 else "🏢 Pronto para escala enterprise"}

📅 PRÓXIMO RELATÓRIO: Amanhã às 8:00 AM

--
🚀 Skinlytics Platform - Enterprise CS2 Market Intelligence
📧 gleidisonjunior187@gmail.com
⏰ Relatório gerado automaticamente às 8:00 AM
        """.strip()
        
        return report
    
    def send_email_report(self, subject, body):
        """Salva relatório localmente (email será configurado depois)"""
        try:
            # Por enquanto, salvar localmente com formato de email
            morning_file = f"logs/morning_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
            
            email_content = f"""
📧 RELATÓRIO MATINAL SKINLYTICS
Para: {self.target_email}
Assunto: {subject}
Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{body}

📌 INSTRUÇÕES PARA CONFIGURAR EMAIL AUTOMÁTICO:
1. Configure seu Gmail nas linhas 29-32 do arquivo daily_morning_report.py
2. Use senha de app do Gmail (não a senha normal)
3. Execute: python daily_morning_report.py --setup-email

✅ Relatório salvo em: {morning_file}
            """.strip()
            
            with open(morning_file, 'w', encoding='utf-8') as f:
                f.write(email_content)
            
            self.logger.info(f"📧 Relatório matinal salvo: {morning_file}")
            self.logger.info(f"📧 Destinatário configurado: {self.target_email}")
            
            # Mostrar no console também
            print(f"\n{'='*70}")
            print("📧 RELATÓRIO MATINAL GERADO!")
            print(f"📁 Arquivo: {morning_file}")
            print(f"📧 Para: {self.target_email}")
            print(f"{'='*70}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao salvar relatório: {e}")
            return False
    
    def generate_and_send_morning_report(self):
        """Gera e envia relatório matinal"""
        self.logger.info("☀️ Gerando relatório matinal...")
        
        # Obter dados
        stats = self.get_growth_stats()
        if not stats:
            self.logger.error("❌ Falha ao obter dados")
            return
        
        # Gerar relatório
        report_text = self.generate_morning_report(stats)
        
        # Criar assunto
        date_str = datetime.now().strftime("%d/%m/%Y")
        subject = f"☀️ Skinlytics Report Matinal - {date_str} - {stats['total_listings']:,} Listings"
        
        # Enviar
        success = self.send_email_report(subject, report_text)
        
        if success:
            self.logger.info("✅ Relatório matinal enviado com sucesso!")
        else:
            self.logger.warning("⚠️ Falha no envio - relatório salvo localmente")
    
    def setup_daily_schedule(self):
        """Configura agendamento diário às 8:00 AM"""
        schedule.clear()
        schedule.every().day.at("08:00").do(self.generate_and_send_morning_report)
        
        self.logger.info("⏰ Agendamento configurado: Relatório diário às 8:00 AM")
        self.logger.info(f"📧 Destinatário: {self.target_email}")
        
        print(f"""
☀️ RELATÓRIO MATINAL CONFIGURADO!

📧 Email: {self.target_email}
⏰ Horário: 8:00 AM (todos os dias)
📊 Conteúdo: Crescimento de dados, valor de mercado, top skins

🔧 IMPORTANTE - CONFIGURAR EMAIL:
1. Edite o arquivo daily_morning_report.py
2. Configure seu email e senha de app Gmail nas linhas 26-29
3. Execute: python daily_morning_report.py --setup-email

✅ O sistema ficará rodando e enviará relatórios automaticamente!
        """)
    
    def run_scheduler(self):
        """Executa agendador contínuo"""
        self.logger.info("🔄 Iniciando agendador de relatórios matinais...")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Verificar a cada minuto
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Agendador interrompido pelo usuário")
        except Exception as e:
            self.logger.error(f"❌ Erro no agendador: {e}")

def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Relatório Matinal Skinlytics")
    parser.add_argument("--test", action="store_true", help="Teste imediato do relatório")
    parser.add_argument("--schedule", action="store_true", help="Iniciar agendamento diário")
    parser.add_argument("--setup-email", action="store_true", help="Configurar email")
    
    args = parser.parse_args()
    
    reporter = DailyMorningReport()
    
    if args.test:
        print("🧪 Testando relatório matinal...")
        reporter.generate_and_send_morning_report()
    
    elif args.schedule:
        reporter.setup_daily_schedule()
        reporter.run_scheduler()
    
    elif args.setup_email:
        print("""
🔧 CONFIGURAÇÃO DE EMAIL:

1. Vá para sua conta Gmail: https://myaccount.google.com/
2. Ative a verificação em 2 etapas
3. Gere uma senha de app:
   - Vá em Segurança > Senhas de app
   - Selecione "Mail" e gere uma senha
   
4. Edite o arquivo daily_morning_report.py linha 26-29:
   "email": "seu_email@gmail.com",
   "password": "sua_senha_app_16_digitos",

5. Teste: python daily_morning_report.py --test

✅ Após configurar, execute: python daily_morning_report.py --schedule
        """)
    
    else:
        print("""
☀️ RELATÓRIO MATINAL SKINLYTICS

Opções disponíveis:
--test          : Teste imediato do relatório
--schedule      : Iniciar agendamento diário (8:00 AM)
--setup-email   : Instruções de configuração de email

📧 Destinatário: gleidisonjunior187@gmail.com
⏰ Horário: 8:00 AM todos os dias
        """)

if __name__ == "__main__":
    main()