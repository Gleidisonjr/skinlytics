# 🎯 SKINLYTICS - Análise de Skins CS:GO

## 🚀 **STATUS ATUAL: DASHBOARD ONLINE!**

**URL**: https://skinlytics-production.up.railway.app

### ✅ **FUNCIONANDO:**
- **Dashboard Streamlit**: 100% operacional
- **Banco PostgreSQL**: Conectado e populado
- **Interface Moderna**: Design profissional
- **Dados de Exemplo**: 100 listings, $262,317.96 USD

### 🔧 **EM DESENVOLVIMENTO:**
- **Coleta CSFloat**: Corrigindo autenticação API
- **Dados Reais**: Implementando rate limiting inteligente

---

## 📊 **O QUE É O SKINLYTICS?**

Sistema completo de análise de skins do CS:GO que coleta dados do CSFloat, analisa preços, detecta oportunidades de trading e apresenta insights em tempo real.

### 🎯 **Funcionalidades:**
- **Coleta Automática**: Dados do CSFloat API
- **Análise de Preços**: Histórico e tendências
- **Detecção de Oportunidades**: Trading insights
- **Dashboard Interativo**: Visualizações em tempo real
- **Machine Learning**: Previsões de preços

---

## 🏗️ **ARQUITETURA**

### **Frontend:**
- **Streamlit**: Dashboard interativo
- **Plotly**: Gráficos dinâmicos
- **Design Responsivo**: Mobile-friendly

### **Backend:**
- **FastAPI**: API REST
- **PostgreSQL**: Banco principal
- **ClickHouse**: Analytics (preparado)
- **Redis**: Cache (preparado)

### **Infraestrutura:**
- **Railway**: Deploy automático
- **Docker**: Containerização
- **GitHub**: Versionamento

---

## 🚀 **COMO USAR**

### **1. Dashboard Online:**
```
https://skinlytics-production.up.railway.app
```

### **2. Executar Localmente:**
```bash
# Instalar dependências
pip install -r requirements.txt
pip install -r requirements_streamlit.txt

# Executar dashboard
streamlit run streamlit_app_real.py
```

### **3. Coletar Dados:**
```bash
# Executar coletor (corrigir autenticação primeiro)
python demo_collector.py
```

---

## 📁 **ESTRUTURA DO PROJETO**

```
Projeto CSGO/
├── 📊 Dashboard
│   ├── streamlit_app_real.py      # Dashboard principal
│   └── requirements_streamlit.txt  # Dependências Streamlit
├── 🔧 Coleta de Dados
│   ├── demo_collector.py          # Coletor otimizado
│   └── monitor_populacao.py       # Monitor de população
├── 🗄️ Banco de Dados
│   ├── src/models/optimized_database.py
│   └── src/services/csfloat_service.py
├── 🚀 Deploy
│   ├── Procfile                   # Railway
│   ├── Dockerfile                 # Docker
│   └── nixpacks.toml             # Build
└── 📋 Documentação
    ├── STATUS_ATUAL.md            # Status detalhado
    └── README.md                  # Este arquivo
```

---

## 🔧 **CONFIGURAÇÃO**

### **Variáveis de Ambiente:**
```bash
# Railway (automático)
DATABASE_URL=postgresql://...

# Local
POSTGRES_HOST=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=skinlytics
```

### **API Keys:**
```bash
# CSFloat API
CSFLOAT_API_KEY=phtZp7cjyjCviMBP9J7nvBpEkggaUQQO
```

---

## 📊 **MÉTRICAS ATUAIS**

- **Dashboard**: ✅ ONLINE
- **Banco**: ✅ CONECTADO
- **Dados Reais**: 🔧 EM CORREÇÃO
- **Coleta Automática**: 🔧 EM CORREÇÃO

---

## 🎯 **PRÓXIMOS PASSOS**

1. **Corrigir autenticação CSFloat API**
2. **Implementar rate limiting inteligente**
3. **Popular banco com dados reais**
4. **Implementar coleta contínua**

---

## 🤝 **CONTRIBUIÇÃO**

1. Fork o projeto
2. Crie uma branch: `git checkout -b feature/nova-funcionalidade`
3. Commit: `git commit -m 'Adiciona nova funcionalidade'`
4. Push: `git push origin feature/nova-funcionalidade`
5. Abra um Pull Request

---

## 📄 **LICENÇA**

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

---

## 📞 **CONTATO**

- **Projeto**: Skinlytics CS:GO Analytics
- **Status**: Em desenvolvimento ativo
- **Dashboard**: https://skinlytics-production.up.railway.app

---

**Última Atualização**: 06/08/2025  
**Versão**: 1.0.0  
**Status**: 🟡 Parcialmente Funcional