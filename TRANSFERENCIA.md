# 🚀 Guia de Transferência do Projeto CS2

Este guia te ajudará a transferir seu projeto CS2 Skins Price Collector para uma nova máquina com Cursor.

## 📋 Pré-requisitos na Nova Máquina

- **Python 3.8+** instalado
- **Cursor** instalado
- **Git** (opcional, mas recomendado)

## 🔄 Opção 1: Transferência Manual (Mais Simples)

### Passo 1: Copiar o Projeto
1. **Na máquina antiga**: Copie toda a pasta do projeto
   ```
   C:\Users\seunome\Desktop\Projetos\Projeto CSGO
   ```

2. **Transfira via**:
   - 📁 **Pen Drive**
   - ☁️ **Google Drive / OneDrive**
   - 📧 **Email** (compactado em ZIP)

3. **Na nova máquina**: Cole a pasta no local desejado
   ```
   C:\Users\seunome\Desktop\Projetos\Projeto CSGO
   ```

### Passo 2: Configurar no Cursor
1. Abra o **Cursor**
2. Vá em **File > Open Folder**
3. Selecione a pasta do projeto copiada
4. Aguarde o Cursor carregar o projeto

### Passo 3: Configurar o Ambiente
1. Abra o terminal no Cursor (Ctrl + `)
2. Execute o script de setup:
   ```bash
   python setup.py
   ```

3. Ou instale manualmente:
   ```bash
   pip install -r requirements.txt
   ```

## 🔄 Opção 2: Usando Git (Recomendado)

### Passo 1: Criar Repositório no GitHub
1. Acesse [github.com](https://github.com)
2. Clique em **"New repository"**
3. Nome: `cs2-skins-collector`
4. Deixe público ou privado
5. **NÃO** inicialize com README

### Passo 2: Subir para GitHub (Máquina Antiga)
```bash
cd "C:\Users\seunome\Desktop\Projetos\Projeto CSGO"
git init
git add .
git commit -m "Primeiro commit - Projeto CS2 completo"
git branch -M main
git remote add origin https://github.com/SEU_USER/cs2-skins-collector.git
git push -u origin main
```

### Passo 3: Baixar na Nova Máquina
```bash
cd "C:\Users\seunome\Desktop\Projetos"
git clone https://github.com/SEU_USER/cs2-skins-collector.git
cd cs2-skins-collector
```

### Passo 4: Configurar no Cursor
1. Abra o **Cursor**
2. **File > Open Folder**
3. Selecione a pasta `cs2-skins-collector`

### Passo 5: Instalar Dependências
```bash
python setup.py
```

## ✅ Verificação da Instalação

Após a transferência, teste se tudo está funcionando:

### 1. Teste Básico
```bash
python -c "import pandas, requests, streamlit; print('✅ Todas as dependências instaladas!')"
```

### 2. Teste do Projeto
```bash
python baixar_market_hash_names.py
```

### 3. Verificar Estrutura
```bash
python setup.py
```

## 🚨 Problemas Comuns e Soluções

### ❌ Erro: "pip não encontrado"
**Solução**: Instale o Python corretamente com pip incluído

### ❌ Erro: "módulo não encontrado"
**Solução**: Execute `pip install -r requirements.txt`

### ❌ Erro: "permissão negada"
**Solução**: Execute o terminal como administrador

### ❌ Erro: "versão do Python incompatível"
**Solução**: Instale Python 3.8+ na nova máquina

## 📁 Estrutura Esperada

Após a transferência, você deve ter:
```
Projeto CSGO/
├── 📄 setup.py (NOVO)
├── 📄 requirements.txt (ATUALIZADO)
├── 📄 .gitignore (NOVO)
├── 📄 TRANSFERENCIA.md (NOVO)
├── 📄 README.md
├── 📄 solucao_definitiva.py
├── 📄 baixar_market_hash_names.py
├── 📄 monitor_coleta.py
├── 📄 analise_dados_coletados.py
├── 📄 dashboard_monitoramento.py
├── 📁 data/
│   └── 📄 skins_list_en.csv
├── 📁 src/
└── 📁 notebooks/
```

## 🎯 Próximos Passos

1. **Execute o setup**: `python setup.py`
2. **Gere a lista de skins**: `python baixar_market_hash_names.py`
3. **Inicie a coleta**: `python solucao_definitiva.py`
4. **Monitore**: `python monitor_coleta.py`
5. **Dashboard**: `streamlit run dashboard_monitoramento.py`

## 📞 Suporte

Se encontrar problemas:
1. Verifique se o Python 3.8+ está instalado
2. Execute `python setup.py` para diagnóstico
3. Consulte o `README.md` para instruções detalhadas
4. Verifique se todos os arquivos foram transferidos

---

**🎉 Parabéns! Seu projeto CS2 está pronto para rodar na nova máquina!** 