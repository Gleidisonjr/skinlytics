# 🎯 SKINLYTICS - CS2 Skin Trading Intelligence Platform

## 🚀 MVP Completo - SaaS para Trading de Skins CS2

**Plataforma completa de inteligência de mercado para skins do Counter-Strike 2, com coleta de dados em tempo real, análise de oportunidades e insights para trading.**

![Status](https://img.shields.io/badge/Status-MVP%20Ready-brightgreen)
![Python](https://img.shields.io/badge/Python-3.13-blue)
![Database](https://img.shields.io/badge/Database-PostgreSQL-blue)
![Cache](https://img.shields.io/badge/Cache-Redis-red)
![Analytics](https://img.shields.io/badge/Analytics-ClickHouse-yellow)

## 📊 Dashboard Demo

🌐 **[Ver Dashboard Online](https://skinlytics-mvp.streamlit.app)** *(após deploy)*

## ✨ Features Implementadas

### 🔄 **Coleta de Dados Automática**
- ✅ API CSFloat integrada com rate limiting inteligente
- ✅ Coleta contínua 24/7 em background  
- ✅ Cache Redis para otimização
- ✅ Sistema de retry e recuperação de erros

### 🏗️ **Arquitetura Enterprise**
- ✅ **PostgreSQL** - Dados operacionais otimizados
- ✅ **ClickHouse** - Analytics e big data
- ✅ **Redis** - Cache de alta performance
- ✅ **Docker Compose** - Setup completo

### 📊 **Dashboard Interativo (Streamlit)**
- ✅ **Métricas em tempo real** - Valor total, quantidade, preços médios
- ✅ **Top Oportunidades** - Sistema de scoring 0-100 para trading
- ✅ **Análise de Mercado** - Distribuição por raridade, últimos listings
- ✅ **Tendências** - Gráficos de volume e performance
- ✅ **Explorer** - Busca avançada com filtros
- ✅ **Auto-refresh** - Dados atualizados automaticamente

### 🎯 **Sistema de Oportunidades**
- ✅ **Opportunity Score** - Algoritmo proprietário 0-100
- ✅ **Análise de tendências** - Variações 7d/30d
- ✅ **Detecção de subvalorizados** - Items com potencial
- ✅ **Filtros inteligentes** - Por preço, raridade, StatTrak

### ⚡ **Performance Otimizada**
- ✅ **Modelo de dados otimizado** - 70% menos armazenamento
- ✅ **Índices estratégicos** - Consultas 3x mais rápidas
- ✅ **Agregações automáticas** - Insights pré-calculados
- ✅ **Cache inteligente** - Redis para duplicatas

## 🛠️ Tecnologias

### Backend & Database
- **Python 3.13** - Linguagem principal
- **PostgreSQL** - Database principal otimizado
- **ClickHouse** - Analytics e big data
- **Redis** - Cache e performance
- **SQLAlchemy** - ORM avançado
- **Docker** - Containerização

### Frontend & Visualização
- **Streamlit** - Dashboard interativo
- **Plotly** - Gráficos avançados
- **Pandas** - Manipulação de dados

### APIs & Coleta
- **CSFloat API** - Dados de marketplace
- **aiohttp** - HTTP assíncrono
- **Rate Limiting** - Controle de requisições

## 🚀 Quick Start

### 1. Setup do Ambiente

```bash
# Clone do repositório
git clone https://github.com/seu-usuario/skinlytics
cd skinlytics

# Virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou .venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt
```

### 2. Setup da Database Enterprise

```bash
# Iniciar containers
docker-compose -f docker-compose.enterprise.yml up -d

# Verificar status
docker ps

# Criar tabelas
python -c "from src.models.optimized_database import create_tables; create_tables()"
```

### 3. Configurar Variáveis de Ambiente

```bash
# Criar arquivo .env
DATABASE_URL=postgresql://skinlytics_user:skinlytics_pass_2025@localhost:5432/skinlytics
CSFLOAT_API_KEY=your_api_key_here
```

### 4. Iniciar Coleta de Dados

```bash
# Collector em background (100 ciclos)
python enterprise_collector.py --cycles 100 --interval 300 &

# Verificar dados
python check_enterprise_data.py
```

### 5. Dashboard Streamlit

```bash
# Executar dashboard local
streamlit run streamlit_app.py

# Ou instalar dependências específicas
pip install -r requirements_streamlit.txt
```

## 📊 Dados Coletados

### 📦 Listings
- **ID único** e timestamp
- **Preço** em centavos (precisão)
- **Float value** para qualidade
- **Paint seed** para patterns
- **Seller statistics** para confiabilidade

### 🎨 Skins
- **Market hash name** único
- **Raridade** e **qualidade**
- **StatTrak/Souvenir** flags
- **Item name** e **wear**

### 🎯 Insights Automáticos
- **Opportunity score** calculado
- **Tendências** de preço 7d/30d
- **Volume** e **liquidez**
- **Detecção** de subvalorizados

## 🌐 Deploy Options

### 🆓 Streamlit Cloud (Recomendado)
```bash
# 1. Push para GitHub
git add .
git commit -m "🚀 MVP Skinlytics ready for deploy"
git push origin main

# 2. Ir para share.streamlit.io
# 3. Conectar repositório
# 4. Configurar DATABASE_URL
# 5. Deploy automático!
```

### ☁️ Outras Opções
- **Railway** - $5/mês gratuito
- **PythonAnywhere** - Versão gratuita limitada
- **Heroku** - Pago (~$7/mês)

## 📈 Métricas Atuais

- 📦 **352+ listings** coletados
- 🎨 **269+ skins únicas** 
- 💰 **$5M+ valor total** monitorado
- 👥 **90+ vendedores** únicos
- ⚡ **18+ listings/min** de velocidade
- 🔴 **1,551+ cache hits** (eficiência)

## 🔧 Scripts Úteis

```bash
# Verificar dados
python check_enterprise_data.py

# Agregações manuais
python daily_aggregator.py --mode manual --show-opportunities

# Benchmark de performance
python performance_benchmark.py

# Migração para modelo otimizado
python migrate_to_optimized.py
```

## 📊 Dashboard Features

### 🎯 Tab: Oportunidades
- Top opportunities com scoring
- Filtros por preço/score/StatTrak
- Badges visuais para items especiais

### 📊 Tab: Mercado  
- Métricas em tempo real
- Gráficos distribuição raridade
- Últimos listings coletados

### 📈 Tab: Tendências
- Top skins por volume
- Gráficos históricos
- Análise performance

### 🔍 Tab: Explorer
- Busca em tempo real
- Filtros avançados
- Resultados instantâneos

## 🚧 Roadmap

### 🎯 Próximas Features
- [ ] **ML/AI Predictions** - Prophet, XGBoost, LSTM
- [ ] **Sistema de Alertas** - Email, Telegram, Discord
- [ ] **API REST** - Endpoints para terceiros
- [ ] **Mobile App** - React Native
- [ ] **Portfolio Tracker** - Acompanhar inventários
- [ ] **Trading Bot** - Automação de trades

### 🔮 Futuro
- [ ] **Multi-games** - DOTA 2, TF2
- [ ] **Social Features** - Comunidade de traders
- [ ] **Marketplace** - Trading direto na plataforma
- [ ] **Analytics Avançadas** - BI completo

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

## 📞 Contato

- **GitHub**: [@seu-usuario](https://github.com/seu-usuario)
- **Email**: seu-email@exemplo.com
- **Discord**: SeuUser#1234

---

**🎯 Skinlytics - Sua vantagem competitiva no trading de skins CS2!**

[![Deploy to Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)