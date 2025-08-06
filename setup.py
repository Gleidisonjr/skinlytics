#!/usr/bin/env python3
"""
Script de setup para o projeto CS2 Skins Price Collector & Analysis
Execute este script na nova máquina para configurar o ambiente.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Executa um comando e mostra o resultado"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} concluído com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao {description.lower()}:")
        print(f"   Comando: {command}")
        print(f"   Erro: {e.stderr}")
        return False

def check_python_version():
    """Verifica se a versão do Python é compatível"""
    print("🐍 Verificando versão do Python...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} detectado. Python 3.8+ é necessário.")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detectado.")
    return True

def install_dependencies():
    """Instala as dependências do projeto"""
    print("\n📦 Instalando dependências...")
    
    # Atualiza pip primeiro
    if not run_command("python -m pip install --upgrade pip", "Atualizando pip"):
        return False
    
    # Instala as dependências
    if not run_command("pip install -r requirements.txt", "Instalando dependências do requirements.txt"):
        return False
    
    return True

def create_directories():
    """Cria diretórios necessários se não existirem"""
    print("\n📁 Criando diretórios necessários...")
    
    directories = [
        "data",
        "logs",
        "notebooks"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Diretório '{directory}' verificado/criado")

def verify_files():
    """Verifica se os arquivos essenciais existem"""
    print("\n📋 Verificando arquivos essenciais...")
    
    essential_files = [
        "requirements.txt",
        "README.md",
        "solucao_definitiva.py",
        "baixar_market_hash_names.py",
        "monitor_coleta.py",
        "analise_dados_coletados.py",
        "dashboard_monitoramento.py"
    ]
    
    missing_files = []
    for file in essential_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} (FALTANDO)")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n⚠️  Arquivos faltando: {', '.join(missing_files)}")
        return False
    
    return True

def main():
    """Função principal do setup"""
    print("🚀 Setup do Projeto CS2 Skins Price Collector & Analysis")
    print("=" * 60)
    
    # Verifica versão do Python
    if not check_python_version():
        print("\n❌ Setup interrompido devido a incompatibilidade de versão.")
        return False
    
    # Verifica arquivos essenciais
    if not verify_files():
        print("\n❌ Setup interrompido devido a arquivos faltando.")
        return False
    
    # Cria diretórios
    create_directories()
    
    # Instala dependências
    if not install_dependencies():
        print("\n❌ Setup interrompido devido a erro na instalação de dependências.")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 Setup concluído com sucesso!")
    print("\n📖 Próximos passos:")
    print("1. Execute: python baixar_market_hash_names.py")
    print("2. Execute: python solucao_definitiva.py")
    print("3. Para monitorar: python monitor_coleta.py")
    print("4. Para dashboard: streamlit run dashboard_monitoramento.py")
    print("\n📚 Consulte o README.md para mais informações.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 