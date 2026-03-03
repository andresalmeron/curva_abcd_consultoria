import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. Configuração inicial da página
st.set_page_config(
    page_title="Analisador de Performance - Portfel", 
    page_icon="📊",
    layout="wide"
)

# Título e cabeçalho da aplicação
st.title("📊 Analisador de Performance Individual - Portfel")
st.markdown("Faça o upload da planilha com a base de dados unificada (Master) para iniciar a análise.")

# 2. Upload do arquivo CSV
uploaded_file = st.file_uploader("Escolha a planilha Base Unificada (formato .csv)", type="csv")

if uploaded_file is not None:
    @st.cache_data
    def load_data(file):
        df = pd.read_csv(file)
        
        # Tratamento de Data
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        df = df.sort_values(by='Data')
        
        # Tratamento do AuC
        if df['AuC'].dtype == 'object':
            df['AuC'] = df['AuC'].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
        df['AuC'] = pd.to_numeric(df['AuC'], errors='coerce').fillna(0)
        
        # Tratamento da Receita
        if 'Receita' in df.columns:
            if df['Receita'].dtype == 'object':
                df['Receita'] = df['Receita'].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
            df['Receita'] = pd.to_numeric(df['Receita'], errors='coerce').fillna(0)
        else:
            df['Receita'] = 0.0
            
        return df
    
    df = load_data(uploaded_file)
    
    # 3. Filtro com Autocompletar
    emails_disponiveis = sorted(df['E-mail'].dropna().unique().tolist())
    
    st.markdown("### Seleção de Consultor(a)")
    email_selecionado = st.selectbox(
        "Digite ou selecione o e-mail (autocompletar ativado):", 
        options=emails_disponiveis,
        index=None, 
        placeholder="Ex: andre..."
    )
    
    if email_selecionado:
        # Filtra os dados e garante que estão ordenados cronologicamente
        df_consultor = df[df['E-mail'] == email_selecionado].copy()
        df_consultor = df_consultor.sort_values(by='Data')
        registro_recente = df_consultor.iloc[-1]
        
        st.divider()
        
        # ==========================================
        # 4. FICHA CORRIDA (INFORMAÇÕES EM DESTAQUE)
        # ==========================================
        st.header("👤 Ficha do Consultor")
        
        # BLOCO 1: Identificação
        id_col1, id_col2, id_col3 = st.columns(3)
        with id_col1:
            st.metric("Nome", str(registro_recente.get('Nome', '-')))
        with id_col2:
            st.metric("E-mail", str(registro_recente.get('E-mail', '-')))
        with id_col3:
            st.metric("Status", str(registro_recente.get('Status', '-')))
            
        st.markdown("<br>", unsafe_allow_html=True)
            
        # BLOCO 2: Performance Financeira
        fin_col1, fin_col2, fin_col3, fin_col4 = st.columns(4)
        
        auc_recente = float(registro_recente.get('AuC', 0))
        auc_formatado = f"R$ {auc_recente:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        receita_recente = float(registro_recente.get('Receita', 0))
        receita_formatada = f"R$ {receita_recente:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        with fin_col1:
            st.metric("AuC Atual (PL)", auc_formatado)
        with fin_col2:
            st.metric("Receita Atual", receita_formatada)
        with fin_col3:
            st.metric("Curva AuC", str(registro_recente.get('Curva AuC', '-')))
        with fin_col4:
            st.metric("Curva Receita", str(registro_recente.get('Curva Receita do Consultor', '-')))
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # BLOCO 3: Informações Secundárias
        st.markdown("#### Informações Secundárias")
        sec_col1, sec_col2, sec_col3, sec_col4 = st.columns(4)
        with sec_col1:
            st.markdown(f"**Turma:** {registro_recente.get('Turma', '-')}")
        with sec_col2:
            st.markdown(f"**Tempo:** {registro_recente.get('Tempo (meses)', '-')} meses")
        with sec_col3:
            st.markdown(f"**MF:** {registro_recente.get('MF', '-')}")
        with sec_col4:
            st.markdown(f"**Regional:** {registro_recente.get('Regional', '-')}")
            
        st.divider()
        
        # ==========================================
        # 5. CRESCIMENTO MÉDIO 
        # ==========================================
        st.header("🚀 Crescimento Médio da Carteira")
        st.markdown("Os valores abaixo representam a **média de crescimento mensal** (em R$) dentro do período analisado. O percentual indica o crescimento total no mesmo intervalo.")
        
        def calcular_crescimento(df_calc, coluna, meses_atras):
            if len(df_calc) < meses_atras + 1:
                return None, None
                
            valor_atual = float(df_calc[coluna].iloc[-1])
            valor_antigo = float(df_calc[coluna].iloc[-(meses_atras + 1)])
            
            crescimento_absoluto_total = valor_atual - valor_antigo
            media_mensal_crescimento = crescimento_absoluto_total / meses_atras
            
            if valor_antigo > 0:
                crescimento_percentual = (crescimento_absoluto_total / valor_antigo) * 100
            else:
                st.metric(label=f"Média Mensal (Últ. {label})", value="Histórico Insuficiente")
