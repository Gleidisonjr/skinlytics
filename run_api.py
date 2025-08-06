#!/usr/bin/env python3
"""
Script para executar a API FastAPI do CS2 Skin Tracker
"""

import uvicorn
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

if __name__ == "__main__":
    # Configurações da API
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    print(f"🚀 Iniciando CS2 Skin Tracker API...")
    print(f"📍 Host: {host}")
    print(f"🔌 Porta: {port}")
    print(f"🐛 Debug: {debug}")
    print(f"📚 Docs: http://{host}:{port}/docs")
    print(f"🔍 API: http://{host}:{port}")
    
    # Executa a API
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    ) 