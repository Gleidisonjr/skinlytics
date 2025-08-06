# 🚂 RAILWAY DEPLOY GUIDE - SKINLYTICS

## ✅ **VANTAGENS DO RAILWAY**
- ✅ **Database PostgreSQL incluído** (gratuito)
- ✅ **Deploy automático** do GitHub
- ✅ **HTTPS nativo** 
- ✅ **Domínio personalizado** possível
- ✅ **$5 crédito gratuito** por mês

---

## 🚀 **PASSO A PASSO COMPLETO**

### 1. 📱 **CRIAR CONTA RAILWAY**
1. **Acessar:** https://railway.app
2. **Sign Up:** with GitHub (conecta automaticamente)
3. **Autorizar:** Railway acessar seus repositórios

### 2. 🗄️ **CRIAR DATABASE POSTGRESQL**
1. **New Project** → **Provision PostgreSQL**
2. **Nome:** `skinlytics-db`
3. **Anotar credenciais:**
   - Host: `xxxx.railway.app`
   - Port: `5432`
   - Database: `railway`
   - Username: `postgres`
   - Password: `[gerado automaticamente]`

### 3. 🔗 **DEPLOY DA APLICAÇÃO**
1. **New Project** → **Deploy from GitHub repo**
2. **Selecionar:** `Gleidisonjr/skinlytics`
3. **Root Directory:** `/` (deixar vazio)
4. **Build Command:** `pip install -r requirements_streamlit.txt`
5. **Start Command:** `streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0`

### 4. ⚙️ **CONFIGURAR VARIÁVEIS DE AMBIENTE**
No Railway, ir em **Variables** e adicionar:

```bash
DATABASE_URL=postgresql://postgres:SENHA@HOST:5432/railway
PORT=8080
PYTHONPATH=/app
```

### 5. 🔄 **CONFIGURAR AUTO-DEPLOY**
- ✅ **GitHub Integration** ativado
- ✅ **Auto-deploy** on push to main
- ✅ **Build logs** disponíveis

---

## 📋 **ARQUIVOS NECESSÁRIOS (JÁ CRIADOS)**

### ✅ `requirements_streamlit.txt`
- Todas dependências do Streamlit
- PostgreSQL drivers
- Plotly, pandas, etc.

### ✅ `Procfile` 
```
web: streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0
```

### ✅ `runtime.txt`
```
python-3.11
```

---

## 🎯 **CONFIGURAÇÃO ESPECÍFICA RAILWAY**

### 🔧 **Start Command**
```bash
streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0 --server.enableCORS=false --server.enableXsrfProtection=false
```

### 🗄️ **Database Connection**
Railway fornece:
- **URL completa** de conexão
- **Credenciais automáticas**
- **SSL habilitado** por padrão

---

## ⚡ **MIGRAÇÃO DE DADOS**

### 📊 **Exportar dados locais**
```bash
# Backup da database local
pg_dump skinlytics > backup_local.sql

# Ou exportar tabelas específicas
python -c "
import pandas as pd
from src.models.database import get_db_connection
conn = get_db_connection()
df = pd.read_sql('SELECT * FROM skin_listings', conn)
df.to_csv('export_skins.csv', index=False)
"
```

### 📥 **Importar para Railway**
```bash
# Conectar na database Railway e importar
psql DATABASE_URL < backup_local.sql
```

---

## 🌐 **RESULTADO FINAL**

Após deploy completo:
- ✅ **URL:** `https://skinlytics-production.up.railway.app`
- ✅ **Database:** PostgreSQL na nuvem
- ✅ **Auto-deploy:** Push → Deploy automático
- ✅ **Logs:** Monitoring completo
- ✅ **SSL:** HTTPS nativo

---

## 🧪 **TESTE LOCAL ANTES DO DEPLOY**

```bash
# Testar localmente com DATABASE_URL Railway
export DATABASE_URL="postgresql://..."
python test_dashboard.py
```

---

## 💡 **DICAS IMPORTANTES**

### 🔒 **Segurança**
- ✅ Credenciais em variáveis de ambiente
- ✅ SSL/TLS habilitado
- ✅ Firewall Railway ativo

### 💰 **Custos**
- ✅ **$5/mês gratuito** Railway
- ✅ Database PostgreSQL incluído
- ✅ SSL e domínio incluídos

### 📈 **Escalabilidade**
- ✅ Auto-scaling disponível
- ✅ Metrics and monitoring
- ✅ Custom domains

---

## 🛠️ **TROUBLESHOOTING**

### ❌ **Deploy falha**
- Verificar `requirements_streamlit.txt`
- Confirmar start command
- Checar logs no Railway

### ❌ **Database connection error**
- Verificar DATABASE_URL
- Confirmar SSL settings
- Testar conexão manual

### ❌ **Streamlit não carrega**
- Verificar PORT variable
- Confirmar server settings
- Checar firewall

---

## 🎉 **NEXT STEPS APÓS DEPLOY**

1. ✅ **Configurar domínio customizado**
2. ✅ **Setup monitoring alerts**
3. ✅ **Configure backup automático**
4. ✅ **Add custom analytics**

**🚀 Seu MVP estará online em menos de 20 minutos!**