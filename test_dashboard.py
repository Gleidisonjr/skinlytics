#!/usr/bin/env python3
"""
Script para testar o dashboard localmente antes do deploy
"""

import subprocess
import sys
import webbrowser
import time

def test_dashboard():
    """Testa o dashboard Streamlit localmente"""
    print("🧪 TESTE LOCAL DO DASHBOARD SKINLYTICS")
    print("=" * 50)
    
    # Verificar se o streamlit está instalado
    try:
        result = subprocess.run([sys.executable, "-c", "import streamlit"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Streamlit não encontrado. Instalando...")
            subprocess.run([sys.executable, "-m", "pip", "install", "streamlit"])
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False
    
    print("✅ Streamlit encontrado!")
    print("🚀 Iniciando dashboard em http://localhost:8501")
    print("📊 Carregando dados da database enterprise...")
    print("⏱️ Aguarde alguns segundos para abrir automaticamente...")
    
    # Abrir navegador após 3 segundos
    time.sleep(3)
    webbrowser.open("http://localhost:8501")
    
    # Executar streamlit
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "streamlit_app.py"])
    except KeyboardInterrupt:
        print("\n🛑 Dashboard interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao executar dashboard: {e}")
    
    return True

if __name__ == "__main__":
    test_dashboard()