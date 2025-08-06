"""
Sistema de Monitoramento Skinlytics - Dashboard de Dados

Monitora em tempo real:
- Coleta de dados CSFloat
- Performance do banco de dados  
- Status dos sistemas
- Métricas de negócio
- Alertas automáticos

Author: CS2 Skin Tracker Team - Skinlytics Platform
Version: 2.0.0 Monitoring Ready
"""

import time
import os
import sqlite3
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List
import psutil
import logging
from pathlib import Path

class SkinlyticsMonitor:
    """Monitor completo do sistema Skinlytics"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.data_path = Path("data")
        self.logs_path = Path("logs")
        
        # Criar diretórios se não existirem
        self.data_path.mkdir(exist_ok=True)
        self.logs_path.mkdir(exist_ok=True)
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler('logs/monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("🔍 SkinlyticsMonitor inicializado")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do banco de dados"""
        try:
            # Conectar ao SQLite
            db_files = list(self.data_path.glob("*.db"))
            if not db_files:
                return {"error": "Nenhum banco encontrado"}
            
            db_path = db_files[0]  # Usar primeiro banco encontrado
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            stats = {
                "database_file": str(db_path),
                "file_size_mb": db_path.stat().st_size / (1024 * 1024),
                "tables": {}
            }
            
            # Obter tabelas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            for (table_name,) in tables:
                try:
                    # Contar registros
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    
                    # Obter tamanho estimado
                    cursor.execute(f"SELECT sql FROM sqlite_master WHERE name='{table_name}'")
                    schema = cursor.fetchone()
                    
                    stats["tables"][table_name] = {
                        "records": count,
                        "schema": schema[0] if schema else "N/A"
                    }
                except Exception as e:
                    stats["tables"][table_name] = {"error": str(e)}
            
            conn.close()
            return stats
            
        except Exception as e:
            return {"error": f"Erro ao acessar banco: {e}"}
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do sistema"""
        try:
            # CPU e Memória
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('.')
            
            # Processos Python
            python_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'create_time']):
                try:
                    if 'python' in proc.info['name'].lower():
                        python_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'memory_mb': proc.info['memory_info'].rss / (1024 * 1024),
                            'uptime_seconds': time.time() - proc.info['create_time']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            return {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total_gb": memory.total / (1024**3),
                    "used_gb": memory.used / (1024**3),
                    "percent": memory.percent
                },
                "disk": {
                    "total_gb": disk.total / (1024**3),
                    "used_gb": disk.used / (1024**3),
                    "percent": (disk.used / disk.total) * 100
                },
                "python_processes": python_processes,
                "system_uptime": time.time() - psutil.boot_time()
            }
            
        except Exception as e:
            return {"error": f"Erro ao obter stats do sistema: {e}"}
    
    def get_api_stats(self) -> Dict[str, Any]:
        """Testa conectividade com APIs"""
        stats = {
            "csfloat_api": {"status": "unknown", "response_time": None},
            "local_api": {"status": "unknown", "response_time": None}
        }
        
        # Testar CSFloat API
        try:
            start_time = time.time()
            response = requests.get("https://csfloat.com/api/v1/listings", timeout=10)
            response_time = time.time() - start_time
            
            stats["csfloat_api"] = {
                "status": "online" if response.status_code == 200 else "error",
                "status_code": response.status_code,
                "response_time": response_time,
                "rate_limit_remaining": response.headers.get("X-RateLimit-Remaining"),
                "rate_limit_reset": response.headers.get("X-RateLimit-Reset")
            }
        except Exception as e:
            stats["csfloat_api"] = {"status": "offline", "error": str(e)}
        
        # Testar API local (se estiver rodando)
        try:
            start_time = time.time()
            response = requests.get("http://localhost:8000/health", timeout=5)
            response_time = time.time() - start_time
            
            stats["local_api"] = {
                "status": "online" if response.status_code == 200 else "error",
                "status_code": response.status_code,
                "response_time": response_time
            }
        except Exception as e:
            stats["local_api"] = {"status": "offline", "error": str(e)}
        
        return stats
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas de coleta de dados"""
        try:
            # Verificar logs de coleta
            log_files = list(self.logs_path.glob("*.log"))
            
            stats = {
                "log_files": len(log_files),
                "last_collection": None,
                "collections_today": 0,
                "errors_today": 0,
                "total_collected": 0
            }
            
            # Analisar logs mais recentes
            today = datetime.now().date()
            
            for log_file in log_files:
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        
                    for line in lines[-100:]:  # Últimas 100 linhas
                        if str(today) in line:
                            if "Successfully collected" in line or "coletado" in line:
                                stats["collections_today"] += 1
                                # Extrair timestamp da última coleta
                                try:
                                    timestamp_str = line.split()[0] + " " + line.split()[1]
                                    stats["last_collection"] = timestamp_str
                                except:
                                    pass
                            
                            if "ERROR" in line or "erro" in line.lower():
                                stats["errors_today"] += 1
                                
                except Exception as e:
                    self.logger.warning(f"Erro ao ler log {log_file}: {e}")
            
            return stats
            
        except Exception as e:
            return {"error": f"Erro ao obter stats de coleta: {e}"}
    
    def get_business_metrics(self) -> Dict[str, Any]:
        """Calcula métricas de negócio baseadas nos dados coletados"""
        try:
            db_stats = self.get_database_stats()
            
            # Métricas simuladas baseadas nos dados reais
            total_listings = 0
            if "tables" in db_stats:
                for table, info in db_stats["tables"].items():
                    if isinstance(info, dict) and "records" in info:
                        total_listings += info["records"]
            
            # Calcular métricas de negócio
            estimated_market_value = total_listings * 85.50  # Preço médio estimado
            api_calls_potential = total_listings * 0.1  # 10% dos listings geram API calls
            
            return {
                "total_data_points": total_listings,
                "estimated_market_value": estimated_market_value,
                "data_coverage": min((total_listings / 100000) * 100, 100),  # % de cobertura do mercado
                "api_calls_potential": int(api_calls_potential),
                "data_quality_score": min((total_listings / 1000) * 100, 100),
                "platform_readiness": "Enterprise" if total_listings > 10000 else "Growing"
            }
            
        except Exception as e:
            return {"error": f"Erro ao calcular métricas: {e}"}
    
    def generate_report(self) -> Dict[str, Any]:
        """Gera relatório completo do sistema"""
        self.logger.info("📊 Gerando relatório completo do sistema...")
        
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "monitor_uptime": str(datetime.utcnow() - self.start_time),
            "database": self.get_database_stats(),
            "system": self.get_system_stats(),
            "apis": self.get_api_stats(),
            "collection": self.get_collection_stats(),
            "business": self.get_business_metrics()
        }
        
        # Salvar relatório
        report_file = f"logs/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.logger.info(f"📄 Relatório salvo: {report_file}")
        
        return report
    
    def print_dashboard(self, report: Dict[str, Any]):
        """Imprime dashboard no terminal"""
        print("\n" + "="*80)
        print("🚀 SKINLYTICS - DASHBOARD DE MONITORAMENTO")
        print("="*80)
        print(f"⏰ Timestamp: {report['timestamp']}")
        print(f"🔄 Monitor Uptime: {report['monitor_uptime']}")
        print()
        
        # Banco de Dados
        print("🗄️ DATABASE STATUS:")
        db = report.get("database", {})
        if "error" not in db:
            print(f"   📁 File: {db.get('database_file', 'N/A')}")
            print(f"   💾 Size: {db.get('file_size_mb', 0):.2f} MB")
            if "tables" in db:
                total_records = sum(
                    info.get("records", 0) for info in db["tables"].values() 
                    if isinstance(info, dict)
                )
                print(f"   📊 Total Records: {total_records:,}")
                print(f"   🗂️ Tables: {len(db['tables'])}")
        else:
            print(f"   ❌ Error: {db['error']}")
        print()
        
        # Sistema
        print("💻 SYSTEM STATUS:")
        sys = report.get("system", {})
        if "error" not in sys:
            print(f"   🖥️ CPU: {sys.get('cpu_percent', 0):.1f}%")
            mem = sys.get("memory", {})
            print(f"   🧠 Memory: {mem.get('percent', 0):.1f}% ({mem.get('used_gb', 0):.1f}GB/{mem.get('total_gb', 0):.1f}GB)")
            disk = sys.get("disk", {})
            print(f"   💿 Disk: {disk.get('percent', 0):.1f}% ({disk.get('used_gb', 0):.1f}GB/{disk.get('total_gb', 0):.1f}GB)")
            print(f"   🐍 Python Processes: {len(sys.get('python_processes', []))}")
        else:
            print(f"   ❌ Error: {sys['error']}")
        print()
        
        # APIs
        print("🌐 API STATUS:")
        apis = report.get("apis", {})
        csfloat = apis.get("csfloat_api", {})
        print(f"   🎯 CSFloat API: {csfloat.get('status', 'unknown').upper()}")
        if csfloat.get("response_time"):
            print(f"      ⚡ Response Time: {csfloat['response_time']:.3f}s")
        if csfloat.get("rate_limit_remaining"):
            print(f"      🚥 Rate Limit: {csfloat['rate_limit_remaining']} remaining")
        
        local = apis.get("local_api", {})
        print(f"   🏠 Local API: {local.get('status', 'unknown').upper()}")
        print()
        
        # Coleta
        print("📈 COLLECTION STATUS:")
        collection = report.get("collection", {})
        if "error" not in collection:
            print(f"   📅 Collections Today: {collection.get('collections_today', 0)}")
            print(f"   ❌ Errors Today: {collection.get('errors_today', 0)}")
            if collection.get("last_collection"):
                print(f"   🕐 Last Collection: {collection['last_collection']}")
        else:
            print(f"   ❌ Error: {collection['error']}")
        print()
        
        # Negócio
        print("💰 BUSINESS METRICS:")
        business = report.get("business", {})
        if "error" not in business:
            print(f"   📊 Data Points: {business.get('total_data_points', 0):,}")
            print(f"   💎 Est. Market Value: ${business.get('estimated_market_value', 0):,.2f}")
            print(f"   📊 Data Coverage: {business.get('data_coverage', 0):.1f}%")
            print(f"   🎯 Platform Status: {business.get('platform_readiness', 'Unknown')}")
        else:
            print(f"   ❌ Error: {business['error']}")
        
        print("="*80)
    
    def run_continuous_monitoring(self, interval_seconds: int = 30):
        """Executa monitoramento contínuo"""
        self.logger.info(f"🔄 Iniciando monitoramento contínuo (intervalo: {interval_seconds}s)")
        
        try:
            while True:
                # Gerar relatório
                report = self.generate_report()
                
                # Mostrar dashboard
                self.print_dashboard(report)
                
                # Verificar alertas
                self.check_alerts(report)
                
                # Aguardar próximo ciclo
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Monitoramento interrompido pelo usuário")
        except Exception as e:
            self.logger.error(f"❌ Erro no monitoramento: {e}")
    
    def check_alerts(self, report: Dict[str, Any]):
        """Verifica condições de alerta"""
        alerts = []
        
        # Verificar CPU alto
        sys_stats = report.get("system", {})
        if sys_stats.get("cpu_percent", 0) > 80:
            alerts.append("🚨 CPU usage alto: {:.1f}%".format(sys_stats["cpu_percent"]))
        
        # Verificar memória alta
        memory = sys_stats.get("memory", {})
        if memory.get("percent", 0) > 85:
            alerts.append("🚨 Memory usage alto: {:.1f}%".format(memory["percent"]))
        
        # Verificar erros de coleta
        collection = report.get("collection", {})
        if collection.get("errors_today", 0) > 10:
            alerts.append("🚨 Muitos erros de coleta hoje: {}".format(collection["errors_today"]))
        
        # Verificar API offline
        apis = report.get("apis", {})
        if apis.get("csfloat_api", {}).get("status") == "offline":
            alerts.append("🚨 CSFloat API offline!")
        
        # Mostrar alertas
        if alerts:
            print("\n⚠️ ALERTAS:")
            for alert in alerts:
                print(f"   {alert}")
                self.logger.warning(alert)
            print()

def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor do Sistema Skinlytics")
    parser.add_argument("--interval", type=int, default=30, help="Intervalo entre verificações (segundos)")
    parser.add_argument("--single", action="store_true", help="Executar apenas uma verificação")
    
    args = parser.parse_args()
    
    monitor = SkinlyticsMonitor()
    
    if args.single:
        # Execução única
        report = monitor.generate_report()
        monitor.print_dashboard(report)
        monitor.check_alerts(report)
    else:
        # Monitoramento contínuo
        monitor.run_continuous_monitoring(args.interval)

if __name__ == "__main__":
    main()