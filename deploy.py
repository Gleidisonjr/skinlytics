#!/usr/bin/env python3
"""
CS2 Skin Tracker - Script de Deploy e Otimização

Este script automatiza todo o processo de preparação para produção,
incluindo otimizações, testes e deploy em diferentes plataformas.

Funcionalidades:
    - Verificação de dependências
    - Otimização do banco de dados
    - Testes automatizados
    - Build para produção
    - Deploy para Streamlit Cloud, Heroku, ou Docker

Author: CS2 Skin Tracker Team
Version: 2.0.0
"""

import os
import sys
import subprocess
import logging
import argparse
from pathlib import Path
from typing import List, Optional
import json
import time
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('deploy.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CS2TrackerDeployer:
    """Classe principal para deploy do CS2 Tracker"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.requirements_file = self.project_root / "requirements.txt"
        self.env_file = self.project_root / ".env"
        
    def check_dependencies(self) -> bool:
        """Verifica se todas as dependências estão instaladas"""
        logger.info("🔍 Verificando dependências...")
        
        try:
            # Verificar Python version
            python_version = sys.version_info
            if python_version < (3, 11):
                logger.error(f"❌ Python 3.11+ necessário. Versão atual: {python_version.major}.{python_version.minor}")
                return False
            
            logger.info(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
            
            # Verificar dependências críticas
            critical_deps = [
                'fastapi', 'streamlit', 'sqlalchemy', 
                'aiohttp', 'plotly', 'pandas'
            ]
            
            for dep in critical_deps:
                try:
                    __import__(dep)
                    logger.info(f"✅ {dep}")
                except ImportError:
                    logger.error(f"❌ {dep} não encontrado")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar dependências: {e}")
            return False
    
    def optimize_database(self) -> bool:
        """Otimiza o banco de dados para produção"""
        logger.info("🗄️ Otimizando banco de dados...")
        
        try:
            from src.models.database import get_engine, create_tables
            from sqlalchemy import text
            
            engine = get_engine()
            
            # Criar tabelas se não existirem
            create_tables(engine)
            
            # Executar otimizações específicas para SQLite
            with engine.connect() as conn:
                # VACUUM para compactar banco
                conn.execute(text("VACUUM"))
                
                # ANALYZE para atualizar estatísticas
                conn.execute(text("ANALYZE"))
                
                # Verificar integridade
                result = conn.execute(text("PRAGMA integrity_check")).fetchone()
                if result[0] != "ok":
                    logger.error(f"❌ Problema de integridade: {result[0]}")
                    return False
                
                conn.commit()
            
            logger.info("✅ Banco de dados otimizado")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao otimizar banco: {e}")
            return False
    
    def run_tests(self) -> bool:
        """Executa testes automatizados"""
        logger.info("🧪 Executando testes...")
        
        try:
            # Teste básico de importação
            from src.models.database import Skin, Listing
            from src.services.csfloat_service import CSFloatService
            from src.collectors.mass_collector import MassCollector
            
            logger.info("✅ Importações básicas")
            
            # Teste de conexão com banco
            from src.models.database import get_engine
            engine = get_engine()
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1")).fetchone()
                if result[0] != 1:
                    raise Exception("Falha no teste de conexão")
            
            logger.info("✅ Conexão com banco")
            
            # Teste de API Key (se disponível)
            api_key = os.getenv('CSFLOAT_API_KEY')
            if api_key:
                # Teste simples sem fazer requisição real
                service = CSFloatService(api_key)
                logger.info("✅ CSFloat service inicializado")
            else:
                logger.warning("⚠️ CSFLOAT_API_KEY não configurada")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro nos testes: {e}")
            return False
    
    def create_production_config(self) -> bool:
        """Cria configurações para produção"""
        logger.info("⚙️ Criando configuração de produção...")
        
        try:
            # Arquivo de configuração para Streamlit
            streamlit_config = """
[server]
port = 8501
address = 0.0.0.0
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false

[theme]
base = "dark"
primaryColor = "#38bdf8"
backgroundColor = "#0f172a"
secondaryBackgroundColor = "#1e293b"
textColor = "#ffffff"

[logger]
level = "info"
"""
            
            config_dir = self.project_root / ".streamlit"
            config_dir.mkdir(exist_ok=True)
            
            with open(config_dir / "config.toml", "w") as f:
                f.write(streamlit_config)
            
            logger.info("✅ Configuração Streamlit criada")
            
            # Arquivo para Heroku
            procfile_content = """
web: streamlit run src/dashboard/streamlit_app.py --server.port=$PORT --server.address=0.0.0.0
api: uvicorn src.api.main:app --host=0.0.0.0 --port=$PORT
"""
            
            with open(self.project_root / "Procfile", "w") as f:
                f.write(procfile_content.strip())
            
            logger.info("✅ Procfile criado")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar configurações: {e}")
            return False
    
    def build_docker(self) -> bool:
        """Cria imagem Docker"""
        logger.info("🐳 Criando imagem Docker...")
        
        dockerfile_content = """
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Criar diretório de dados
RUN mkdir -p data logs

# Expor portas
EXPOSE 8501 8000

# Script de entrada
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
"""
        
        entrypoint_content = """#!/bin/bash
set -e

# Inicializar banco se necessário
python -c "from src.models.database import create_tables; create_tables()"

# Verificar se deve executar coleta inicial
if [ "$RUN_INITIAL_COLLECTION" = "true" ]; then
    echo "Executando coleta inicial..."
    python src/collectors/realtime_collector.py --duration 2 &
fi

# Iniciar serviços
if [ "$1" = "streamlit" ]; then
    exec streamlit run src/dashboard/streamlit_app.py --server.port=8501 --server.address=0.0.0.0
elif [ "$1" = "api" ]; then
    exec uvicorn src.api.main:app --host=0.0.0.0 --port=8000
elif [ "$1" = "collector" ]; then
    exec python src/collectors/realtime_collector.py
else
    # Modo desenvolvimento - ambos os serviços
    uvicorn src.api.main:app --host=0.0.0.0 --port=8000 &
    exec streamlit run src/dashboard/streamlit_app.py --server.port=8501 --server.address=0.0.0.0
fi
"""
        
        try:
            with open(self.project_root / "Dockerfile", "w") as f:
                f.write(dockerfile_content)
            
            with open(self.project_root / "docker-entrypoint.sh", "w") as f:
                f.write(entrypoint_content)
            
            # Docker Compose
            compose_content = """
version: '3.8'

services:
  cs2-tracker:
    build: .
    ports:
      - "8501:8501"
      - "8000:8000"
    environment:
      - CSFLOAT_API_KEY=${CSFLOAT_API_KEY}
      - DATABASE_URL=sqlite:///data/skins_saas.db
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    command: ["streamlit"]
    
  collector:
    build: .
    environment:
      - CSFLOAT_API_KEY=${CSFLOAT_API_KEY}
      - DATABASE_URL=sqlite:///data/skins_saas.db
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    command: ["collector"]
    depends_on:
      - cs2-tracker
"""
            
            with open(self.project_root / "docker-compose.yml", "w") as f:
                f.write(compose_content)
            
            logger.info("✅ Arquivos Docker criados")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar Docker: {e}")
            return False
    
    def deploy_streamlit_cloud(self) -> bool:
        """Prepara para deploy no Streamlit Cloud"""
        logger.info("☁️ Preparando para Streamlit Cloud...")
        
        try:
            # Criar arquivo de secrets
            secrets_content = """
[general]
CSFLOAT_API_KEY = "sua_api_key_aqui"

[database]
DATABASE_URL = "sqlite:///data/skins_saas.db"
"""
            
            streamlit_dir = self.project_root / ".streamlit"
            streamlit_dir.mkdir(exist_ok=True)
            
            with open(streamlit_dir / "secrets.toml.example", "w") as f:
                f.write(secrets_content)
            
            # Instruções de deploy
            deploy_instructions = """
# Deploy no Streamlit Cloud

1. Faça push do código para GitHub
2. Acesse https://share.streamlit.io/
3. Conecte seu repositório GitHub
4. Configure os secrets em Advanced Settings:
   - CSFLOAT_API_KEY: sua_chave_da_api
5. Deploy será automático!

## Arquivo principal
app_file: src/dashboard/streamlit_app.py

## Secrets necessários
- CSFLOAT_API_KEY
"""
            
            with open(self.project_root / "DEPLOY_STREAMLIT.md", "w") as f:
                f.write(deploy_instructions)
            
            logger.info("✅ Preparação para Streamlit Cloud concluída")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro na preparação Streamlit Cloud: {e}")
            return False
    
    def create_requirements_lock(self) -> bool:
        """Cria requirements.txt com versões fixas"""
        logger.info("📋 Criando requirements.txt otimizado...")
        
        optimized_requirements = """
# Core Framework
fastapi==0.104.1
uvicorn==0.24.0
streamlit==1.48.0

# Database
sqlalchemy==2.0.23
alembic==1.12.1

# HTTP & API
aiohttp==3.12.15
requests==2.32.4

# Data Processing
pandas==2.3.1
numpy==2.3.2

# Visualization
plotly==6.2.0

# Utilities
python-dotenv==1.1.1
tenacity==9.1.2
pydantic==2.11.7

# Production
gunicorn==21.2.0
psycopg2-binary==2.9.9; sys_platform != "win32"

# Optional ML (for future features)
# scikit-learn==1.5.2
# prophet==1.1.5
"""
        
        try:
            with open("requirements_production.txt", "w") as f:
                f.write(optimized_requirements.strip())
            
            logger.info("✅ requirements_production.txt criado")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar requirements: {e}")
            return False
    
    def full_deploy_preparation(self) -> bool:
        """Executa toda a preparação para deploy"""
        logger.info("🚀 INICIANDO PREPARAÇÃO COMPLETA PARA DEPLOY")
        logger.info("=" * 60)
        
        steps = [
            ("Verificar dependências", self.check_dependencies),
            ("Otimizar banco de dados", self.optimize_database),
            ("Executar testes", self.run_tests),
            ("Criar configurações", self.create_production_config),
            ("Preparar Docker", self.build_docker),
            ("Preparar Streamlit Cloud", self.deploy_streamlit_cloud),
            ("Criar requirements otimizado", self.create_requirements_lock),
        ]
        
        success_count = 0
        
        for step_name, step_func in steps:
            logger.info(f"\n📋 {step_name}...")
            try:
                if step_func():
                    success_count += 1
                    logger.info(f"✅ {step_name} - SUCESSO")
                else:
                    logger.error(f"❌ {step_name} - FALHOU")
            except Exception as e:
                logger.error(f"❌ {step_name} - ERRO: {e}")
        
        logger.info("\n" + "=" * 60)
        logger.info(f"📊 RESULTADO: {success_count}/{len(steps)} etapas concluídas")
        
        if success_count == len(steps):
            logger.info("🎉 PREPARAÇÃO COMPLETA - PRONTO PARA DEPLOY!")
            self._show_deploy_instructions()
            return True
        else:
            logger.error("❌ PREPARAÇÃO INCOMPLETA - VERIFIQUE OS ERROS")
            return False
    
    def _show_deploy_instructions(self):
        """Mostra instruções de deploy"""
        instructions = """
🚀 PROJETO PRONTO PARA DEPLOY!

📋 Opções de Deploy:

1. 🌊 STREAMLIT CLOUD (Mais Fácil):
   - Push para GitHub
   - Conecte em share.streamlit.io
   - Configure CSFLOAT_API_KEY nos secrets
   
2. 🔥 HEROKU:
   heroku create cs2-tracker
   heroku config:set CSFLOAT_API_KEY=sua_chave
   git push heroku main
   
3. 🐳 DOCKER:
   docker build -t cs2-tracker .
   docker run -p 8501:8501 -e CSFLOAT_API_KEY=sua_chave cs2-tracker
   
4. ☁️ AWS/GCP/AZURE:
   - Use PostgreSQL gerenciado
   - Configure auto-scaling
   - Setup SSL/HTTPS

📊 URLs após deploy:
- Dashboard: https://seu-app.streamlit.app
- API: https://seu-app.herokuapp.com/docs

🔧 Próximos passos:
1. Configure monitoramento
2. Setup backup automático
3. Configure alertas de erro
4. Teste load balancing

💡 Dicas:
- Use PostgreSQL em produção
- Configure CDN para assets
- Implemente cache Redis
- Setup CI/CD automático
"""
        logger.info(instructions)

def main():
    parser = argparse.ArgumentParser(description="CS2 Tracker Deploy Script")
    parser.add_argument("--step", choices=[
        "check", "optimize", "test", "config", 
        "docker", "streamlit", "requirements", "full"
    ], default="full", help="Etapa específica para executar")
    
    args = parser.parse_args()
    
    deployer = CS2TrackerDeployer()
    
    if args.step == "full":
        success = deployer.full_deploy_preparation()
    else:
        step_map = {
            "check": deployer.check_dependencies,
            "optimize": deployer.optimize_database,
            "test": deployer.run_tests,
            "config": deployer.create_production_config,
            "docker": deployer.build_docker,
            "streamlit": deployer.deploy_streamlit_cloud,
            "requirements": deployer.create_requirements_lock,
        }
        success = step_map[args.step]()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()