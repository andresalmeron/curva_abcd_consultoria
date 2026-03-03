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
        
        # Tratamento da Receita (Novo Dado)
        if 'Receita' in df.columns:
            if df['Receita'].dtype == 'object':
                df['Receita'] = df['Receita'].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
            df['Receita'] = pd.to_numeric(df['Receita'], errors='coerce').fillna(0)
        else:
            df['Receita'] = 0.0 # Fallback caso a coluna não exista
            
        return df
    
    # Carregando os dados
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
        df_consultor = df[df['E-mail'] == email_selecionado].copy()
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
        # 5. GRÁFICOS DE EVOLUÇÃO
        # ==========================================
        st.header("📈 Evolução Histórica")
        
        graf_col1, graf_col2 = st.columns(2)
        
        with graf_col1:
            st.subheader("AuC vs Receita")
            
            # Criando o gráfico com eixos Y duplos
            fig_auc_rec = make_subplots(specs=[[{"secondary_y": True}]])
            
            # Adicionando AuC (Área - Eixo Y da Esquerda)
            fig_auc_rec.add_trace(
                go.Scatter(
                    x=df_consultor['Data'], 
                    y=df_consultor['AuC'], 
                    name="AuC (PL)", 
                    fill='tozeroy',
                    mode='lines+markers',
                    line=dict(color='#1E88E5') # Azul
                ),
                secondary_y=False,
            )
            
            # Adicionando Receita (Linha - Eixo Y da Direita)
            fig_auc_rec.add_trace(
                go.Scatter(
                    x=df_consultor['Data'], 
                    y=df_consultor['Receita'], 
                    name="Receita", 
                    mode='lines+markers',
                    line=dict(color='#00C853', width=3) # Verde
                ),
                secondary_y=True,
            )
            
            fig_auc_rec.update_layout(
                xaxis_title="Período",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=30, b=0),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            fig_auc_rec.update_yaxes(title_text="Volume de AuC (R$)", secondary_y=False, showgrid=True, gridcolor='rgba(200,200,200,0.3)')
            fig_auc_rec.update_yaxes(title_text="Receita Mensal (R$)", secondary_y=True, showgrid=False)
            
            st.plotly_chart(fig_auc_rec, use_container_width=True)
            
        with graf_col2:
            st.subheader("Comparativo de Curvas (Rankings)")
            
            # Usando go.Figure() para ter controle total sobre as duas linhas
            fig_curvas = go.Figure()
            
            # Adicionando Curva AuC
            fig_curvas.add_trace(
                go.Scatter(
                    x=df_consultor['Data'], 
                    y=df_consultor['Curva AuC'], 
                    name="Curva AuC",
                    mode='lines+markers',
                    line_shape='hv', # Mantém o estilo de degrau (step-line)
                    line=dict(color='#1E88E5', width=3) # Azul
                )
            )
            
            # Adicionando Curva Receita
            # Usamos get() com fallback para caso o nome da coluna mude ligeiramente
            curva_receita_col = 'Curva Receita do Consultor' if 'Curva Receita do Consultor' in df_consultor.columns else 'Curva Receita'
            
            fig_curvas.add_trace(
                go.Scatter(
                    x=df_consultor['Data'], 
                    y=df_consultor.get(curva_receita_col, pd.Series()), 
                    name="Curva Receita",
                    mode='lines+markers',
                    line_shape='hv',
                    line=dict(color='#00C853', width=3) # Verde
                )
            )
            
            # Ajuste de Layout travando D na base e A no teto
            fig_curvas.update_layout(
                xaxis_title="Período",
                yaxis_title="Ranking (Curva)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=30, b=0),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                yaxis=dict(
                    showgrid=True, 
                    gridcolor='rgba(200,200,200,0.3)',
                    type='category',
                    categoryorder='array',
                    categoryarray=['D', 'C', 'B', 'A'] # Trava o D no chão e o A no teto
                )
            )
            
            st.plotly_chart(fig_curvas, use_container_width=True)
