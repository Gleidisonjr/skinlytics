#!/usr/bin/env python3
"""
🔄 DAILY AGGREGATOR - SKINLYTICS
Executador automático de agregações diárias
Pode ser agendado para rodar automaticamente via cron/task scheduler
"""

import asyncio
import argparse
import logging
import schedule
import time
from datetime import datetime, timedelta
from src.services.aggregation_service import AggregationService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('data/daily_aggregator.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class DailyAggregator:
    """Gerenciador de agregações automáticas"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.running = False
        
    def run_aggregation(self):
        """Executa uma agregação completa"""
        try:
            self.logger.info("🚀 Iniciando agregação automática...")
            
            service = AggregationService()
            result = service.run_daily_aggregation()
            
            if result['success']:
                stats = result['stats']
                duration = result['duration']
                
                self.logger.info("✅ Agregação concluída com sucesso!")
                self.logger.info(f"📊 Histórico criado: {stats['price_history_created']} registros")
                self.logger.info(f"🧠 Insights atualizados: {stats['insights_updated']} skins")
                self.logger.info(f"⏱️ Tempo total: {duration:.2f}s")
                
                # Mostrar top oportunidades
                top_opportunities = service.get_top_opportunities(5)
                if top_opportunities:
                    self.logger.info("🎯 TOP 5 OPORTUNIDADES:")
                    for i, opp in enumerate(top_opportunities, 1):
                        self.logger.info(
                            f"  {i}. {opp['skin_name'][:50]} - "
                            f"${opp['current_price']:.2f} "
                            f"(Score: {opp['opportunity_score']:.0f})"
                        )
                
                return True
            else:
                self.logger.error(f"❌ Erro na agregação: {result['error']}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Erro crítico no agregador: {e}")
            return False
    
    def run_manual(self):
        """Executa agregação manual (uma vez)"""
        self.logger.info("🔧 Modo manual: executando agregação única")
        success = self.run_aggregation()
        
        if success:
            print("\n🎉 Agregação manual concluída com sucesso!")
        else:
            print("\n❌ Agregação manual falhou. Verifique os logs.")
        
        return success
    
    def run_scheduler(self, schedule_time: str = "06:00"):
        """Executa agregador com agendamento automático"""
        self.logger.info(f"⏰ Modo agendado: executando diariamente às {schedule_time}")
        
        # Agendar execução diária
        schedule.every().day.at(schedule_time).do(self.run_aggregation)
        
        # Primeira execução imediata se especificado
        if input("Executar agregação imediatamente? (s/N): ").lower() in ['s', 'sim', 'y', 'yes']:
            self.run_aggregation()
        
        self.running = True
        
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Agregador interrompido pelo usuário")
            self.running = False
    
    def run_continuous(self, interval_hours: int = 6):
        """Executa agregador continuamente com intervalo específico"""
        self.logger.info(f"🔄 Modo contínuo: executando a cada {interval_hours} horas")
        
        self.running = True
        
        # Primeira execução
        self.run_aggregation()
        
        try:
            while self.running:
                self.logger.info(f"⏳ Aguardando {interval_hours} horas até próxima agregação...")
                time.sleep(interval_hours * 3600)  # Convert to seconds
                
                if self.running:
                    self.run_aggregation()
                    
        except KeyboardInterrupt:
            self.logger.info("🛑 Agregador contínuo interrompido pelo usuário")
            self.running = False

def main():
    """Função principal com argumentos de linha de comando"""
    parser = argparse.ArgumentParser(description='Daily Aggregator - Skinlytics')
    
    parser.add_argument(
        '--mode', 
        choices=['manual', 'scheduled', 'continuous'],
        default='manual',
        help='Modo de execução (default: manual)'
    )
    
    parser.add_argument(
        '--schedule-time',
        default='06:00',
        help='Horário para execução agendada (formato HH:MM) (default: 06:00)'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=6,
        help='Intervalo em horas para modo contínuo (default: 6)'
    )
    
    parser.add_argument(
        '--show-opportunities',
        action='store_true',
        help='Mostrar top oportunidades após agregação'
    )
    
    args = parser.parse_args()
    
    aggregator = DailyAggregator()
    
    print("🔄 DAILY AGGREGATOR - SKINLYTICS")
    print("=" * 50)
    print(f"Modo: {args.mode}")
    
    if args.mode == 'manual':
        success = aggregator.run_manual()
        
        if success and args.show_opportunities:
            print("\n🎯 BUSCANDO TOP OPORTUNIDADES...")
            service = AggregationService()
            opportunities = service.get_top_opportunities(10)
            
            if opportunities:
                print("\n🏆 TOP 10 OPORTUNIDADES DE TRADING:")
                print("-" * 80)
                for i, opp in enumerate(opportunities, 1):
                    trend_icon = "📈" if opp['trend_7d'] > 0 else "📉" if opp['trend_7d'] < 0 else "➡️"
                    undervalued_icon = "💎" if opp['is_undervalued'] else ""
                    stattrak_icon = "🔥" if opp['is_stattrak'] else ""
                    
                    print(f"{i:2}. {opp['skin_name'][:45]:45} | "
                          f"${opp['current_price']:8.2f} | "
                          f"{trend_icon} {opp['trend_7d']:+5.1f}% | "
                          f"Score: {opp['opportunity_score']:3.0f} "
                          f"{undervalued_icon}{stattrak_icon}")
            else:
                print("❌ Nenhuma oportunidade encontrada")
    
    elif args.mode == 'scheduled':
        aggregator.run_scheduler(args.schedule_time)
    
    elif args.mode == 'continuous':
        aggregator.run_continuous(args.interval)

if __name__ == "__main__":
    main()