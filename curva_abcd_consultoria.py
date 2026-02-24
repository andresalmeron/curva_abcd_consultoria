import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuração inicial da página (deve ser o primeiro comando Streamlit)
st.set_page_config(
    page_title="Analisador de Performance - Portfel", 
    page_icon="📊",
    layout="wide"
)

# Título e cabeçalho da aplicação
st.title("📊 Analisador de Performance Individual - Portfel")
st.markdown("Faça o upload da planilha com a base de dados unificada para iniciar a análise.")

# 2. Upload do arquivo CSV
uploaded_file = st.file_uploader("Escolha a planilha Base Unificada (formato .csv)", type="csv")

if uploaded_file is not None:
    # Função com cache para otimizar o carregamento do arquivo
    @st.cache_data
    def load_data(file):
        df = pd.read_csv(file)
        
        # Converte a coluna de Data para o tipo datetime do Pandas e garante a ordem cronológica
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        df = df.sort_values(by='Data')
        
        # Opcional: Tratar os valores de AuC para garantir que sejam numéricos caso venham com vírgulas
        if df['AuC'].dtype == 'object':
            df['AuC'] = df['AuC'].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
        df['AuC'] = pd.to_numeric(df['AuC'], errors='coerce').fillna(0)
        
        return df
    
    # Carregando os dados
    df = load_data(uploaded_file)
    
    # 3. Filtro com Autocompletar (Streamlit Selectbox já faz isso nativamente)
    # Extraímos a lista de e-mails únicos, removemos nulos e ordenamos em ordem alfabética
    emails_disponiveis = sorted(df['E-mail'].dropna().unique().tolist())
    
    st.markdown("### Seleção de Consultor(a)")
    email_selecionado = st.selectbox(
        "Digite ou selecione o e-mail (autocompletar ativado):", 
        options=emails_disponiveis,
        index=None, # Inicia vazio para não carregar ninguém por padrão
        placeholder="Ex: andre..."
    )
    
    # Só exibe a ficha e gráficos SE um e-mail for selecionado
    if email_selecionado:
        # Filtra a base apenas para a pessoa selecionada
        df_consultor = df[df['E-mail'] == email_selecionado].copy()
        
        # Captura a linha (série) mais recente desse consultor
        registro_recente = df_consultor.iloc[-1]
        
        st.divider() # Linha divisória visual
        
        # ==========================================
        # 4. FICHA CORRIDA (INFORMAÇÕES EM DESTAQUE)
        # ==========================================
        st.header("👤 Ficha do Consultor")
        
        # Cria colunas para organizar as métricas lado a lado
        col1, col2, col3, col4, col5 = st.columns(5)
        
        # Formata o valor numérico do AuC para o padrão brasileiro (R$ XX.XXX,XX)
        auc_recente = float(registro_recente.get('AuC', 0))
        auc_formatado = f"R$ {auc_recente:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        # Exibe os dados de ALTO DESTAQUE
        with col1:
            st.metric("Nome", str(registro_recente.get('Nome', '-')))
        with col2:
            st.metric("E-mail", str(registro_recente.get('E-mail', '-')))
        with col3:
            st.metric("Status", str(registro_recente.get('Status', '-')))
        with col4:
            st.metric("AuC Atual (PL)", auc_formatado)
        with col5:
            st.metric("Curva Atual", str(registro_recente.get('Curva AuC', '-')))
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Exibe os dados de MENOR DESTAQUE
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
            st.subheader("Evolução do AuC (PL)")
            
            # Gráfico de Área para AuC (passa noção material de acúmulo financeiro)
            fig_auc = px.area(
                df_consultor, 
                x="Data", 
                y="AuC", 
                markers=True,
                color_discrete_sequence=['#1E88E5'] # Azul de alto contraste
            )
            fig_auc.update_layout(
                xaxis_title="Período",
                yaxis_title="Volume de AuC (R$)",
                plot_bgcolor="rgba(0,0,0,0)", # Fundo transparente para integrar com o Streamlit
                margin=dict(l=0, r=0, t=30, b=0),
                yaxis=dict(showgrid=True, gridcolor='rgba(200,200,200,0.3)') # Grid sutil
            )
            st.plotly_chart(fig_auc, use_container_width=True)
            
        with graf_col2:
            st.subheader("Evolução da Curva (Ranking)")
            
            # Gráfico de Linha em Degraus para as Curvas (A, B, C, D)
            # Definimos a ordem das categorias no eixo Y para que o A fique sempre no topo
            ordem_curva = ["D", "C", "B", "A"] 
            
            fig_curva = px.line(
                df_consultor, 
                x="Data", 
                y="Curva AuC", 
                markers=True,
                category_orders={"Curva AuC": ordem_curva},
                color_discrete_sequence=['#FF8F00'] # Laranja/Âmbar de alto contraste
            )
            
            # O parâmetro 'hv' cria uma linha reta horizontal e depois vertical, 
            # ideal para progressão de níveis/ranqueamentos.
            fig_curva.update_traces(line_shape='hv') 
            
            fig_curva.update_layout(
                xaxis_title="Período",
                yaxis_title="Ranking (Curva)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=30, b=0),
                yaxis=dict(
                    showgrid=True, 
                    gridcolor='rgba(200,200,200,0.3)',
                    type='category' # Força o eixo a tratar como categoria (D, C, B, A)
                )
            )
            st.plotly_chart(fig_curva, use_container_width=True)
