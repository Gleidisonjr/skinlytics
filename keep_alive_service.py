"""
Serviço Keep-Alive para Skinlytics

Soluções para manter coleta ativa mesmo com hibernação:
1. Impedir hibernação automática
2. Serviço Windows
3. Deploy em VPS/Cloud
4. Docker containers

Author: CS2 Skin Tracker Team - Skinlytics Platform
Version: 2.0.0 Always-On Ready
"""

import os
import sys
import time
import subprocess
import ctypes
from pathlib import Path
import logging

class KeepAliveService:
    """Mantém sistema ativo e previne hibernação"""
    
    def __init__(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler('logs/keepalive.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def prevent_sleep(self):
        """Impede hibernação do Windows"""
        try:
            # Constantes do Windows API
            ES_CONTINUOUS = 0x80000000
            ES_SYSTEM_REQUIRED = 0x00000001
            ES_DISPLAY_REQUIRED = 0x00000002
            
            # Manter sistema ativo
            ctypes.windll.kernel32.SetThreadExecutionState(
                ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
            )
            
            self.logger.info("🔒 Hibernação prevenida - sistema mantido ativo")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao prevenir hibernação: {e}")
            return False
    
    def setup_windows_service(self):
        """Configura como serviço do Windows (requer admin)"""
        service_script = """
import subprocess
import time
import os
import sys

def run_skinlytics_service():
    project_dir = r"C:\\Users\\dopamine\\Desktop\\Projetos\\Projeto CSGO"
    
    while True:
        try:
            # Ativar venv e executar coletor
            activate_cmd = f'"{project_dir}\\.venv\\Scripts\\activate" && cd "{project_dir}" && python scale_collection.py --interval 600'
            
            subprocess.run(activate_cmd, shell=True, check=True)
            
        except Exception as e:
            print(f"Erro no serviço: {e}")
            time.sleep(60)  # Aguardar 1 min antes de tentar novamente
        
        time.sleep(300)  # Aguardar 5 min entre verificações

if __name__ == "__main__":
    run_skinlytics_service()
        """
        
        # Criar script do serviço
        service_path = Path("skinlytics_service.py")
        with open(service_path, 'w') as f:
            f.write(service_script)
        
        self.logger.info(f"📝 Script de serviço criado: {service_path}")
        
        # Instruções para criar serviço
        instructions = """
🔧 INSTRUÇÕES PARA CRIAR SERVIÇO WINDOWS:

1. Abra PowerShell como Administrador
2. Execute os comandos:

   # Instalar NSSM (Non-Sucking Service Manager)
   choco install nssm
   
   # OU baixar manualmente de: https://nssm.cc/download
   
3. Criar serviço:
   nssm install SkinlyticsService
   
4. Na janela que abrir, configure:
   - Path: C:\\Python\\python.exe (ou caminho do Python)
   - Arguments: C:\\Users\\dopamine\\Desktop\\Projetos\\Projeto CSGO\\skinlytics_service.py
   - Startup directory: C:\\Users\\dopamine\\Desktop\\Projetos\\Projeto CSGO
   
5. Iniciar serviço:
   nssm start SkinlyticsService

📋 O serviço rodará automaticamente mesmo após reinicialização!
        """
        
        print(instructions)
        return service_path
    
    def create_startup_script(self):
        """Cria script de inicialização automática"""
        startup_script = f"""
@echo off
cd /d "{os.getcwd()}"
call .venv\\Scripts\\activate
python scale_collection.py --interval 600
pause
        """
        
        script_path = Path("startup_skinlytics.bat")
        with open(script_path, 'w') as f:
            f.write(startup_script)
        
        # Instrução para adicionar ao startup
        startup_folder = Path.home() / "AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup"
        
        instructions = f"""
🚀 INICIALIZAÇÃO AUTOMÁTICA CONFIGURADA:

1. Script criado: {script_path.absolute()}

2. Para executar na inicialização do Windows:
   - Copie o arquivo para: {startup_folder}
   - OU execute: copy "{script_path.absolute()}" "{startup_folder}"

3. Para executar manualmente:
   - Clique duplo em: {script_path.absolute()}

✅ Agora o Skinlytics iniciará automaticamente com o Windows!
        """
        
        print(instructions)
        return script_path
    
    def simulate_activity(self):
        """Simula atividade para manter sistema acordado"""
        try:
            # Mover mouse invisível para simular atividade
            import pyautogui
            pyautogui.FAILSAFE = False
            
            while True:
                # Mover mouse 1 pixel e voltar (invisível)
                current_pos = pyautogui.position()
                pyautogui.moveTo(current_pos.x + 1, current_pos.y)
                time.sleep(0.1)
                pyautogui.moveTo(current_pos.x, current_pos.y)
                
                self.logger.info("🖱️ Atividade simulada")
                time.sleep(300)  # A cada 5 minutos
                
        except ImportError:
            self.logger.warning("⚠️ pyautogui não instalado - usando apenas API do Windows")
            self.prevent_sleep()
            while True:
                time.sleep(300)
                self.prevent_sleep()
        
        except Exception as e:
            self.logger.error(f"❌ Erro na simulação: {e}")

def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Keep-Alive Service Skinlytics")
    parser.add_argument("--prevent-sleep", action="store_true", help="Prevenir hibernação")
    parser.add_argument("--setup-service", action="store_true", help="Configurar serviço Windows")
    parser.add_argument("--setup-startup", action="store_true", help="Configurar inicialização automática")
    parser.add_argument("--simulate-activity", action="store_true", help="Simular atividade contínua")
    
    args = parser.parse_args()
    
    service = KeepAliveService()
    
    if args.prevent_sleep:
        service.prevent_sleep()
        print("🔒 Hibernação prevenida. Mantenha este terminal aberto.")
        try:
            while True:
                time.sleep(300)  # Verificar a cada 5 min
                service.prevent_sleep()
        except KeyboardInterrupt:
            print("🛑 Serviço interrompido")
    
    elif args.setup_service:
        service.setup_windows_service()
    
    elif args.setup_startup:
        service.create_startup_script()
    
    elif args.simulate_activity:
        service.simulate_activity()
    
    else:
        print("""
🔧 OPÇÕES DISPONÍVEIS:

--prevent-sleep      : Impede hibernação (mantenha terminal aberto)
--setup-service      : Configura como serviço Windows (requer admin)
--setup-startup      : Cria script de inicialização automática
--simulate-activity  : Simula atividade para manter sistema ativo

💡 RECOMENDAÇÃO PARA SUA MÁQUINA PESSOAL:
python keep_alive_service.py --setup-startup
        """)

if __name__ == "__main__":
    main()