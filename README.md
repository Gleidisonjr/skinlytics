# 🎯 SKINLYTICS - Análise de Skins CS2

## ⏸️ **STATUS ATUAL: PROJETO PAUSADO**

**🛑 PROJETO PAUSADO - AGUARDANDO API PAGO**

### ⚠️ **STATUS ATUAL:**
- **Dashboard Streamlit**: ✅ Base funcional implementada
- **Coleta de Dados**: ❌ APIs gratuitas bloqueadas
- **Dados Reais**: ❌ Apenas dados limitados disponíveis
- **Interface Moderna**: ✅ Design implementado
- **Taxa de Sucesso**: ❌ APIs gratuitas não funcionam

### 🔧 **SOLUÇÃO IMPLEMENTADA:**
- **Steam Market API**: ✅ Funcionando mas limitado (60 requests/min)
- **Rate Limiting Inteligente**: ✅ Implementado mas insuficiente
- **Sistema Robusto**: ✅ Base sólida mas precisa de API pago

### 🚨 **PROBLEMA ATUAL:**
- **APIs Gratuitas**: Todas bloqueadas (CSFloat, Pricempire, Buff163)
- **Web Scraping**: Não funciona efetivamente
- **Steam Market**: Muito limitado para projeto robusto
- **Solução**: Necessário investir em API pago (Pricempire Pro: $29.99/mês)

---

## 📊 **O QUE É O SKINLYTICS?**

Sistema completo de análise de skins do CS2 que coleta dados do Steam Market, analisa preços, detecta oportunidades de trading e apresenta insights em tempo real.

### 🎯 **Funcionalidades (Base Implementada):**
- **Coleta Automática**: ✅ Base implementada (precisa API pago)
- **Análise de Preços**: ✅ Estrutura pronta (precisa dados reais)
- **Detecção de Oportunidades**: ✅ Algoritmos implementados
- **Dashboard Interativo**: ✅ Visualizações com Plotly funcionando
- **Dados Confiáveis**: ❌ Precisa API pago para dados robustos

### ⚠️ **Limitações Atuais:**
- **Dados Limitados**: Apenas Steam Market (muito restritivo)
- **Análise Superficial**: Sem dados de múltiplas plataformas
- **Tempo Real**: Dados não atualizados constantemente

---

## 🏗️ **ARQUITETURA ATUALIZADA**

### **Frontend:**
- **Streamlit**: Dashboard interativo e responsivo
- **Plotly**: Gráficos dinâmicos e profissionais
- **Design Moderno**: Interface de usuário intuitiva

### **Backend:**
- **Python 3.13**: Linguagem principal com async/await
- **aiohttp**: Requisições assíncronas eficientes
- **asyncio**: Programação assíncrona para performance
- **Pandas**: Manipulação e análise de dados

### **APIs:**
- **Steam Market**: Fonte de dados principal (funcionando)
- **Rate Limiting**: 60 requests/min (respeitado)

---

## 🚀 **COMO USAR (BASE FUNCIONAL)**

### **⚠️ LIMITAÇÃO ATUAL:**
O projeto está pausado devido ao bloqueio de todas as APIs gratuitas. A base está implementada mas precisa de API pago para funcionar efetivamente.

### **1. Testar Base Funcional (opcional):**
```bash
python steam_only_collector.py
```
**Resultado**: Dados limitados do Steam Market (muito restritivo)

### **2. Visualizar Dashboard Base:**
```bash
streamlit run dashboard_steam.py
```
**Resultado**: Dashboard com dados limitados (demonstração da base)

### **3. Para Funcionamento Completo:**
- **Necessário**: API pago (Pricempire Pro: $29.99/mês)
- **Alternativa**: Desenvolver projeto diferente sem dependências externas

---

## 📁 **ESTRUTURA DO PROJETO ATUALIZADA**

```
Projeto CSGO/
├── 🎮 Coletor de Dados (FUNCIONANDO)
│   ├── steam_only_collector.py     # ✅ Coletor Steam Market
│   ├── reliable_collector.py       # 🔧 Coletor Pricempire+Steam
│   └── test_reliable_apis.py      # ✅ Teste das APIs
├── 📊 Dashboard (FUNCIONANDO)
│   ├── dashboard_steam.py          # ✅ Dashboard Steam Market
│   ├── dashboard_reliable.py       # 🔧 Dashboard Multi-fonte
│   └── streamlit_app_real.py      # 🔧 Dashboard original
├── 📋 Documentação (ATUALIZADA)
│   ├── STATUS_FINAL.md             # ✅ Status final resolvido
│   ├── GUIA_USO_RAPIDO.md         # ✅ Guia de uso rápido
│   ├── STATUS_ATUAL.md             # 📋 Status anterior
│   └── README.md                   # ✅ Este arquivo atualizado
├── 🔧 Dependências
│   ├── requirements_reliable.txt   # ✅ Dependências novas
│   └── requirements.txt            # 📋 Dependências originais
├── 🗄️ Banco de Dados
│   ├── src/models/optimized_database.py
│   └── src/services/csfloat_service.py
├── 🚀 Deploy
│   ├── Procfile                   # Railway
│   ├── Dockerfile                 # Docker
│   └── nixpacks.toml             # Build
└── 📊 Dados Coletados
    └── steam_collection_*.json    # ✅ Dados reais coletados
```

---

## 🔧 **CONFIGURAÇÃO SIMPLIFICADA**

### **Instalar Dependências:**
```bash
pip install -r requirements_reliable.txt
```

### **Ou Instalar Manualmente:**
```bash
pip install streamlit plotly pandas aiohttp
```

### **Variáveis de Ambiente:**
```bash
# Nenhuma API key necessária!
# Steam Market API é pública e gratuita
```

---

## 📊 **MÉTRICAS ATUAIS (BASE IMPLEMENTADA)**

- **Dashboard**: ✅ Base funcional implementada
- **Coleta de Dados**: ❌ APIs gratuitas bloqueadas
- **Dados Reais**: ❌ Apenas Steam Market (limitado)
- **Taxa de Sucesso**: ❌ APIs não funcionam
- **Rate Limiting**: ✅ Implementado mas insuficiente
- **Status**: ⏸️ **PROJETO PAUSADO** - Aguardando API pago

---

## 🎯 **FUNCIONALIDADES DO DASHBOARD**

### **Métricas Principais:**
- Total de skins coletadas
- Taxa de sucesso da coleta
- Valor total das skins
- Timestamp da coleta

### **Visualizações Interativas:**
- Distribuição de preços por faixa
- Top skins mais caras
- Análise de volume de vendas
- Tabela detalhada com filtros

### **Filtros Disponíveis:**
- Por faixa de preço
- Por termo de busca
- Por tipo de preço (médio/mais baixo)

---

## 🚀 **PRÓXIMOS PASSOS RECOMENDADOS**

### **1. Para Portfólio (Imediato):**
- ⚠️ **Projeto pausado** - APIs gratuitas bloqueadas
- 💡 **Desenvolver projeto alternativo** sem dependências externas
- 🎯 **Foco**: Web apps, sistemas internos, aplicações locais
- ✅ **Demonstrar habilidades técnicas** em outros contextos

### **2. Para Retomar Skinlytics (Futuro):**
- **Investir em API pago**: Pricempire Pro ($29.99/mês)
- **Implementar coleta robusta**: Dados de múltiplas plataformas
- **Expandir funcionalidades**: Histórico, alertas, ML
- **Dashboard completo**: Análises avançadas e insights

---

## 💰 **ALTERNATIVAS FUTURAS (Opcional)**

### **APIs Pagas (Mais Robustas):**
- **Skinport API**: Oficial, documentada
- **Bitskins API**: Histórico completo
- **CSMoney API**: Dados em tempo real

### **APIs Gratuitas (Alternativas):**
- **Pricempire**: 120 requests/min (testar novamente)
- **Steam Charts**: Dados de jogadores
- **IGDB**: Informações de jogos

---

## 🛑 **STATUS ATUAL DO PROJETO**

### **❌ PROBLEMA ATUAL:**
- **Todas as APIs gratuitas**: Bloqueadas ou muito limitadas
- **CSFloat**: Rate limiting extremo + autenticação mudou
- **Pricempire**: Cloudflare Challenge (403 Forbidden)
- **Buff163**: Web scraping não funciona efetivamente
- **Steam Market**: Muito limitado (60 requests/min)

### **⚠️ SITUAÇÃO ATUAL:**
- **Base implementada**: ✅ Dashboard e estrutura funcionais
- **Dados limitados**: ❌ Apenas Steam Market disponível
- **Qualidade insuficiente**: ❌ Para projeto robusto de portfólio
- **Solução necessária**: 💰 API pago (Pricempire Pro: $29.99/mês)

### **📊 COMPARAÇÃO:**
| Aspecto | Status Atual | Com API Pago |
|---------|--------------|--------------|
| **Funcionamento** | ⚠️ Limitado | ✅ Completo |
| **Estabilidade** | ❌ APIs bloqueadas | ✅ Estável |
| **Rate Limiting** | ❌ Muito restritivo | ✅ Adequado |
| **Dados** | ❌ Apenas Steam | ✅ Múltiplas fontes |
| **Qualidade** | ❌ Insuficiente | ✅ Profissional |

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

- **Projeto**: Skinlytics CS2 Analytics
- **Status**: ⏸️ **PROJETO PAUSADO**
- **Dashboard**: Base funcional implementada
- **Última Coleta**: APIs gratuitas bloqueadas

---

**Última Atualização**: 21/08/2025  
**Versão**: 2.0.0 (Base Implementada)  
**Status**: 🟡 **PROJETO PAUSADO**  
**Compatibilidade**: Windows, Linux, macOS  
**Recomendação**: ⚠️ **AGUARDANDO API PAGO**

---

## 🎯 **CONCLUSÃO**

**O projeto Skinlytics está pausado devido ao bloqueio de APIs gratuitas. A base está implementada mas precisa de investimento em API pago para funcionar efetivamente.**

- ⚠️ **Projeto pausado** - APIs gratuitas bloqueadas
- ✅ **Base implementada** - Dashboard e estrutura funcionais
- 💰 **Solução necessária** - API pago (Pricempire Pro: $29.99/mês)
- 💡 **Recomendação** - Desenvolver projeto alternativo sem dependências externas