#!/usr/bin/env python3
"""
Teste simples para verificar se o plotly está funcionando
"""

try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    print("✅ Plotly importado com sucesso!")
    
    # Teste básico
    import pandas as pd
    import numpy as np
    
    # Criar dados de teste
    df = pd.DataFrame({
        'x': np.random.randn(100),
        'y': np.random.randn(100)
    })
    
    # Criar gráfico
    fig = px.scatter(df, x='x', y='y', title='Teste Plotly')
    print("✅ Gráfico criado com sucesso!")
    
    # Salvar como HTML para teste
    fig.write_html("test_plotly.html")
    print("✅ Gráfico salvo como HTML!")
    
except ImportError as e:
    print(f"❌ Erro ao importar plotly: {e}")
except Exception as e:
    print(f"❌ Erro geral: {e}")

print("🎯 Teste concluído!")
