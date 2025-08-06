"""
Configurador Automático de Email Matinal Skinlytics

Configura o envio automático de relatórios às 8:00 AM
para: gleidisonjunior187@gmail.com

Author: CS2 Skin Tracker Team - Skinlytics Platform
Version: 1.0.0
"""

import os
import schedule
import time
from datetime import datetime
import subprocess
from pathlib import Path

def setup_email_config():
    """Configura credenciais de email"""
    print("""
🔧 CONFIGURAÇÃO DE EMAIL MATINAL

Para enviar relatórios automáticos para gleidisonjunior187@gmail.com:

1. Você precisa configurar um email remetente (Gmail recomendado)
2. Gerar senha de app Gmail (não a senha normal)
3. Editar as credenciais no arquivo daily_morning_report.py

📧 OPÇÕES:
A) Usar seu próprio Gmail
B) Criar email específico para o projeto  
C) Usar apenas relatórios locais (salvos em logs/)

Qual opção você prefere? (A/B/C)
    """)

def test_morning_report():
    """Testa geração de relatório matinal"""
    try:
        result = subprocess.run([
            "python", "daily_morning_report.py", "--test"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Relatório matinal testado com sucesso!")
            return True
        else:
            print(f"❌ Erro no teste: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Erro ao testar: {e}")
        return False

def setup_startup_task():
    """Configura tarefa de inicialização"""
    try:
        # Copiar script para pasta de inicialização
        startup_folder = Path.home() / "AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup"
        source_script = Path("start_morning_reports.bat")
        
        if source_script.exists() and startup_folder.exists():
            dest_script = startup_folder / "skinlytics_morning_reports.bat"
            
            # Copiar arquivo
            import shutil
            shutil.copy2(source_script, dest_script)
            
            print(f"✅ Script copiado para: {dest_script}")
            print("📅 Relatórios matinais configurados para iniciar com Windows!")
            return True
        else:
            print("⚠️ Pasta de inicialização não encontrada")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao configurar inicialização: {e}")
        return False

def main():
    """Configuração principal"""
    print("🌅 CONFIGURANDO RELATÓRIOS MATINAIS SKINLYTICS")
    print("="*60)
    
    # Testar relatório
    print("1. 🧪 Testando geração de relatório...")
    if test_morning_report():
        print("   ✅ Teste passou!")
    else:
        print("   ❌ Teste falhou - verifique logs")
    
    print("\n2. 📧 Configuração de email:")
    setup_email_config()
    
    print("\n3. 🚀 Configurar inicialização automática:")
    if setup_startup_task():
        print("   ✅ Configurado!")
    else:
        print("   ⚠️ Configure manualmente")
    
    print(f"""
✅ CONFIGURAÇÃO CONCLUÍDA!

📧 Destinatário: gleidisonjunior187@gmail.com
⏰ Horário: 8:00 AM (todos os dias)
📁 Backups: logs/morning_report_*.txt

🔧 PRÓXIMOS PASSOS:
1. Configure email remetente (se quiser envio automático)
2. Mantenha PC ligado para relatórios funcionarem
3. Verifique logs/ para acompanhar relatórios

🎯 PARA TESTAR AGORA:
python daily_morning_report.py --test
    """)

if __name__ == "__main__":
    main()