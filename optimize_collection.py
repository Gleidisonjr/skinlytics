"""
Otimizador do Sistema de Coleta Skinlytics

Melhora performance, reduz uso de CPU e otimiza coleta
Mantém máxima eficiência 24/7

Author: CS2 Skin Tracker Team - Skinlytics Platform  
Version: 1.0.0
"""

import sqlite3
import psutil
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

class CollectionOptimizer:
    """Otimiza sistema de coleta"""
    
    def __init__(self):
        self.db_path = "data/skins.db"
        self.logs_path = Path("logs")
        
    def optimize_database(self):
        """Otimiza banco de dados"""
        print("🗄️ Otimizando banco de dados...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Analisar tabelas
            cursor.execute("ANALYZE")
            
            # Vacuum para otimizar espaço
            cursor.execute("VACUUM")
            
            # Estatísticas
            cursor.execute("SELECT COUNT(*) FROM listings")
            total_listings = cursor.fetchone()[0]
            
            # Tamanho do arquivo
            db_size = Path(self.db_path).stat().st_size / (1024 * 1024)
            
            conn.close()
            
            print(f"   ✅ {total_listings:,} listings otimizados")
            print(f"   💾 Tamanho: {db_size:.2f} MB")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            return False
    
    def check_system_performance(self):
        """Verifica performance do sistema"""
        print("💻 Verificando performance do sistema...")
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memória
        memory = psutil.virtual_memory()
        
        # Processos Python
        python_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
            try:
                if 'python' in proc.info['name'].lower():
                    python_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'memory_mb': proc.info['memory_info'].rss / (1024 * 1024),
                        'cpu_percent': proc.info['cpu_percent']
                    })
            except:
                pass
        
        print(f"   🖥️ CPU: {cpu_percent:.1f}%")
        print(f"   🧠 Memory: {memory.percent:.1f}% ({memory.used/(1024**3):.1f}GB/{memory.total/(1024**3):.1f}GB)")
        print(f"   🐍 Python processes: {len(python_processes)}")
        
        # Alertas de performance
        if cpu_percent > 50:
            print("   ⚠️ CPU alto - considere otimizar")
        
        if memory.percent > 85:
            print("   ⚠️ Memória alta - considere reiniciar")
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "python_processes": len(python_processes)
        }
    
    def clean_old_logs(self, days_to_keep=7):
        """Limpa logs antigos"""
        print(f"🧹 Limpando logs com mais de {days_to_keep} dias...")
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cleaned = 0
            
            for log_file in self.logs_path.glob("*.log"):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
                    cleaned += 1
            
            print(f"   ✅ {cleaned} arquivos de log removidos")
            return cleaned
            
        except Exception as e:
            print(f"   ❌ Erro na limpeza: {e}")
            return 0
    
    def check_collection_status(self):
        """Verifica status da coleta"""
        print("📊 Verificando status da coleta...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Coletas recentes
            cursor.execute("""
                SELECT COUNT(*) FROM listings 
                WHERE collected_at >= datetime('now', '-1 hour')
            """)
            last_hour = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM listings 
                WHERE collected_at >= datetime('now', '-24 hours')
            """)
            last_24h = cursor.fetchone()[0]
            
            # Valor total
            cursor.execute("SELECT SUM(price_usd) FROM listings")
            total_value = cursor.fetchone()[0] or 0
            
            conn.close()
            
            print(f"   📈 Última hora: +{last_hour} listings")
            print(f"   📅 Últimas 24h: +{last_24h} listings")
            print(f"   💰 Valor total: ${total_value:,.2f}")
            
            # Status da coleta
            if last_hour > 0:
                print("   ✅ Coleta ativa")
            elif last_24h > 0:
                print("   ⚠️ Coleta lenta")
            else:
                print("   ❌ Coleta parada")
            
            return {
                "last_hour": last_hour,
                "last_24h": last_24h,
                "total_value": total_value
            }
            
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            return None
    
    def optimize_collection_settings(self):
        """Otimiza configurações de coleta"""
        print("⚙️ Otimizando configurações de coleta...")
        
        # Verificar performance atual
        perf = self.check_system_performance()
        
        recommendations = []
        
        if perf["cpu_percent"] > 30:
            recommendations.append("Aumentar intervalo de coleta para reduzir CPU")
        
        if perf["memory_percent"] > 80:
            recommendations.append("Reduzir concurrent workers")
        
        if perf["python_processes"] > 5:
            recommendations.append("Verificar processos duplicados")
        
        if recommendations:
            print("   📋 Recomendações:")
            for rec in recommendations:
                print(f"      • {rec}")
        else:
            print("   ✅ Configurações otimizadas!")
        
        return recommendations
    
    def generate_optimization_report(self):
        """Gera relatório de otimização"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "database": {},
            "system": {},
            "collection": {},
            "recommendations": []
        }
        
        print("\n" + "="*60)
        print("🚀 RELATÓRIO DE OTIMIZAÇÃO SKINLYTICS")
        print("="*60)
        
        # Otimizar banco
        if self.optimize_database():
            report["database"]["optimized"] = True
        
        # Verificar sistema
        report["system"] = self.check_system_performance()
        
        # Verificar coleta
        report["collection"] = self.check_collection_status()
        
        # Limpar logs
        cleaned_logs = self.clean_old_logs()
        report["logs_cleaned"] = cleaned_logs
        
        # Recomendações
        report["recommendations"] = self.optimize_collection_settings()
        
        # Salvar relatório
        report_file = f"logs/optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Relatório salvo: {report_file}")
        print("="*60)
        
        return report

def main():
    """Função principal"""
    optimizer = CollectionOptimizer()
    
    print("🔧 OTIMIZADOR SKINLYTICS - INICIANDO...")
    print()
    
    # Gerar relatório completo
    report = optimizer.generate_optimization_report()
    
    print("""
✅ OTIMIZAÇÃO CONCLUÍDA!

🎯 PRÓXIMAS AÇÕES RECOMENDADAS:
1. Execute este otimizador 1x por semana
2. Monitore logs/ para acompanhar performance  
3. Reinicie sistema se CPU/Memory altos
4. Mantenha apenas processos essenciais rodando

🔄 PARA EXECUTAR NOVAMENTE:
python optimize_collection.py
    """)

if __name__ == "__main__":
    main()