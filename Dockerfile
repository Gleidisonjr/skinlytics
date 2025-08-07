FROM python:3.11-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Definir diretório de trabalho
WORKDIR /app

# Copiar arquivos de requisitos primeiro (para cache do Docker)
COPY requirements.txt .
COPY requirements_streamlit.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements_streamlit.txt

# Copiar código da aplicação
COPY . .

# Expor porta
EXPOSE 8080

# Comando para executar o Streamlit (versão com dados reais)
CMD ["streamlit", "run", "streamlit_app_real.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]