# 🚀 SKINLYTICS MVP - Guia de Deploy

## 📊 Dashboard Criado

✅ **Dashboard Streamlit completo** com:
- 📊 Métricas em tempo real
- 🎯 Top oportunidades de trading
- 📈 Gráficos de tendências e distribuição
- 🔍 Explorer com filtros avançados
- 🔄 Auto-refresh opcional

## 🌐 Opções de Deploy

### 1. 🚀 **Streamlit Cloud (RECOMENDADO - GRÁTIS)**

**Passos:**
1. Fazer commit e push do código para GitHub
2. Ir para [share.streamlit.io](https://share.streamlit.io)
3. Conectar GitHub e selecionar o repositório
4. Configurar as variáveis de ambiente:
   ```
   DATABASE_URL=postgresql://user:pass@host:port/db
   ```
5. Deploy automático!

**Vantagens:**
- ✅ 100% gratuito
- ✅ Deploy automático via GitHub
- ✅ HTTPS incluído
- ✅ Escalabilidade automática

### 2. 🐍 **PythonAnywhere (GRÁTIS com limitações)**

**Passos:**
1. Criar conta no [pythonanywhere.com](https://pythonanywhere.com)
2. Upload dos arquivos via web interface
3. Configurar Web App:
   ```bash
   # No console bash
   pip install --user -r requirements_streamlit.txt
   ```
4. Configurar WSGI file

**Limitações versão gratuita:**
- ⚠️ 512MB RAM
- ⚠️ 1 worker
- ⚠️ Apenas HTTP (não HTTPS)

### 3. ☁️ **Heroku (PAGO)**

**Passos:**
1. Instalar Heroku CLI
2. Criar app Heroku
3. Configurar database addon
4. Deploy via Git

**Custos:**
- 💰 ~$7/mês para hobby dyno
- 💰 Database addon adicional

### 4. 🔥 **Railway (RECOMENDADO para produção)**

**Passos:**
1. Conectar GitHub no [railway.app](https://railway.app)
2. Deploy automático
3. Configurar variáveis de ambiente

**Vantagens:**
- ✅ $5/mês gratuito
- ✅ Database PostgreSQL incluído
- ✅ Auto-scaling
- ✅ Deploy via GitHub

## 🛠️ Configuração Local (Teste)

```bash
# Instalar dependências
pip install -r requirements_streamlit.txt

# Configurar variável de ambiente
export DATABASE_URL="postgresql://skinlytics_user:skinlytics_pass_2025@localhost:5432/skinlytics"

# Executar dashboard
streamlit run streamlit_app.py
```

## 🔧 Variáveis de Ambiente Necessárias

```bash
DATABASE_URL=postgresql://user:password@host:port/database
```

## 📱 Features do Dashboard

### 🎯 **Tab: Oportunidades**
- Top oportunidades com scoring 0-100
- Filtros por preço, score, StatTrak
- Badges visuais para items especiais

### 📊 **Tab: Mercado**
- Métricas em tempo real
- Gráficos de distribuição por raridade
- Últimos listings coletados

### 📈 **Tab: Tendências**
- Top skins por volume
- Simulação de gráficos históricos
- Análise de performance

### 🔍 **Tab: Explorer**
- Busca em tempo real
- Filtros por preço e float
- Resultados instantâneos

## 🚀 Deploy Recomendado: **Streamlit Cloud**

**Por que escolher Streamlit Cloud:**
1. **100% Gratuito** para projetos públicos
2. **Deploy automático** via GitHub
3. **HTTPS** incluído
4. **Domínio** personalizado possível
5. **Integração** perfeita com Streamlit

## 📋 Checklist de Deploy

- [ ] Código commitado no GitHub
- [ ] Arquivo `requirements_streamlit.txt` criado
- [ ] Configuração `.streamlit/config.toml` criada
- [ ] Variáveis de ambiente configuradas
- [ ] Database acessível publicamente
- [ ] Deploy realizado
- [ ] Testes de funcionalidade

## 🎯 Próximos Passos

1. **Escolher plataforma** de deploy
2. **Configurar database** público (ou usar Railway)
3. **Fazer deploy** do MVP
4. **Testar funcionalidades**
5. **Compartilhar link** público

## 🔗 URLs de Exemplo

Após o deploy, você terá URLs como:
- Streamlit Cloud: `https://skinlytics-mvp.streamlit.app`
- Railway: `https://skinlytics-production.up.railway.app`
- PythonAnywhere: `https://yourusername.pythonanywhere.com`

---

**🎉 Seu MVP estará online e acessível para qualquer pessoa!**