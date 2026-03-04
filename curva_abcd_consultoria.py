import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Configuração inicial da página
st.set_page_config(
    page_title="Analisador de Performance - Portfel", 
    page_icon="📊",
    layout="wide"
)

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
        
        # Tratamento de TODAS as Receitas
        colunas_receita = ['Receita', 'Receita Portfel', 'Receita Parceiro(a)']
        for col in colunas_receita:
            if col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                df[col] = 0.0
            
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
        
        id_col1, id_col2, id_col3 = st.columns(3)
        with id_col1:
            st.metric("Nome", str(registro_recente.get('Nome', '-')))
        with id_col2:
            st.metric("E-mail", str(registro_recente.get('E-mail', '-')))
        with id_col3:
            st.metric("Status", str(registro_recente.get('Status', '-')))
            
        st.markdown("<br>", unsafe_allow_html=True)
            
        fin_col1, fin_col2, fin_col3, fin_col4 = st.columns(4)
        
        def formatar_moeda_simples(valor):
            if pd.isna(valor): return "-"
            return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        # Novo formatador exclusivo para o Tooltip (escapando o cifrão para evitar a fonte de matemática)
        def formatar_moeda_tooltip(valor):
            if pd.isna(valor): return "-"
            return f"R\\$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        auc_recente = float(registro_recente.get('AuC', 0))
        auc_formatado = formatar_moeda_simples(auc_recente)
        
        receita_recente = float(registro_recente.get('Receita', 0))
        receita_formatada = formatar_moeda_simples(receita_recente)
        
        curva_auc_atual = str(registro_recente.get('Curva AuC', '-')).upper()
        tempo_meses_atual = registro_recente.get('Tempo (meses)', 0)
        
        # --- LÓGICA DO HOVER (TOOLTIP) DE AuC ---
        def obter_metas_auc(meses):
            if pd.isna(meses):
                return None, None, None
            meses = float(meses)
            if meses < 6:
                return 1800000, 3600000, 7200000
            elif meses < 12:
                return 4800000, 9600000, 19200000
            elif meses < 24:
                return 7500000, 15000000, 30000000
            else:
                return 12000000, 24000000, 48000000

        texto_hover_auc = f"Tempo de casa: {tempo_meses_atual} meses\n\n"
        metas = obter_metas_auc(tempo_meses_atual)
        
        if metas[0] is not None and curva_auc_atual in ['A', 'B', 'C', 'D']:
            meta_c, meta_b, meta_a = metas
            texto_hover_auc += f"Enquadramento na Curva {curva_auc_atual}:\n"
            
            if curva_auc_atual == 'A':
                texto_hover_auc += f"- Mínimo Exigido: {formatar_moeda_tooltip(meta_a)}\n"
                texto_hover_auc += f"- Próximo Nível: Nível Máximo Atingido"
            elif curva_auc_atual == 'B':
                texto_hover_auc += f"- Mínimo Exigido: {formatar_moeda_tooltip(meta_b)}\n"
                texto_hover_auc += f"- Próximo Nível (A): {formatar_moeda_tooltip(meta_a)}"
            elif curva_auc_atual == 'C':
                texto_hover_auc += f"- Mínimo Exigido: {formatar_moeda_tooltip(meta_c)}\n"
                texto_hover_auc += f"- Próximo Nível (B): {formatar_moeda_tooltip(meta_b)}"
            elif curva_auc_atual == 'D':
                texto_hover_auc += f"- Próximo Nível (C): {formatar_moeda_tooltip(meta_c)}"
        else:
            texto_hover_auc = "Não foi possível calcular o enquadramento."
            
        with fin_col1:
            st.metric("AuC Atual (PL)", auc_formatado)
        with fin_col2:
            st.metric("Receita Bruta Atual", receita_formatada)
        with fin_col3:
            # Tooltip ativado no parâmetro help
            st.metric("Curva AuC", curva_auc_atual, help=texto_hover_auc)
        with fin_col4:
            st.metric("Curva Receita", str(registro_recente.get('Curva Receita do Consultor', '-')))
            
        st.markdown("<br>", unsafe_allow_html=True)
        
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
                crescimento_percentual = 100.0 if valor_atual > 0 else 0.0
                
            return media_mensal_crescimento, crescimento_percentual

        tab_auc, tab_receita = st.tabs(["Crescimento do AuC", "Crescimento da Receita"])
        periodos = [("3 Meses", 3), ("6 Meses", 6), ("12 Meses", 12)]
        
        with tab_auc:
            cols_auc = st.columns(3)
            for col, (label, meses) in zip(cols_auc, periodos):
                med_mensal, perc_total = calcular_crescimento(df_consultor, 'AuC', meses)
                with col:
                    if med_mensal is not None:
                        sinal = "-" if med_mensal < 0 else ""
                        valor_formatado = f"{sinal}R$ {abs(med_mensal):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        st.metric(label=f"Média Mensal (Últ. {label})", value=valor_formatado, delta=f"{perc_total:+.2f}% no período", delta_color="normal")
                    else:
                        st.metric(label=f"Média Mensal (Últ. {label})", value="Histórico Insuficiente")

        with tab_receita:
            cols_rec = st.columns(3)
            for col, (label, meses) in zip(cols_rec, periodos):
                med_mensal, perc_total = calcular_crescimento(df_consultor, 'Receita', meses)
                with col:
                    if med_mensal is not None:
                        sinal = "-" if med_mensal < 0 else ""
                        valor_formatado = f"{sinal}R$ {abs(med_mensal):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        st.metric(label=f"Média Mensal (Últ. {label})", value=valor_formatado, delta=f"{perc_total:+.2f}% no período", delta_color="normal")
                    else:
                        st.metric(label=f"Média Mensal (Últ. {label})", value="Histórico Insuficiente")
        
        st.divider()
        
        # ==========================================
        # 6. GRÁFICOS DE EVOLUÇÃO (SEPARADOS)
        # ==========================================
        st.header("📈 Evolução Histórica")
        
        graf_col1, graf_col2 = st.columns(2)
        
        with graf_col1:
            st.subheader("Evolução do AuC (PL)")
            fig_auc = go.Figure()
            fig_auc.add_trace(go.Scatter(x=df_consultor['Data'], y=df_consultor['AuC'], name="AuC (PL)", fill='tozeroy', mode='lines+markers', line=dict(color='#1E88E5', width=3), hovertemplate="<b>Data:</b> %{x|%b/%Y}<br><b>AuC:</b> R$ %{y:,.2f}<extra></extra>"))
            fig_auc.update_layout(xaxis_title="Período", yaxis_title="Volume de AuC (R$)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=0, r=0, t=30, b=0), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), separators=",.")
            fig_auc.update_yaxes(showgrid=True, gridcolor='rgba(200,200,200,0.3)', tickformat=",.2f")
            st.plotly_chart(fig_auc, use_container_width=True)
            
        with graf_col2:
            st.subheader("Composição de Receitas")
            fig_rec = go.Figure()
            fig_rec.add_trace(go.Scatter(x=df_consultor['Data'], y=df_consultor['Receita'], name="Receita Bruta", mode='lines+markers', line=dict(color='#00C853', width=3), hovertemplate="<b>Data:</b> %{x|%b/%Y}<br><b>Rec. Bruta:</b> R$ %{y:,.2f}<extra></extra>"))
            fig_rec.add_trace(go.Scatter(x=df_consultor['Data'], y=df_consultor['Receita Portfel'], name="Receita Portfel", mode='lines+markers', line=dict(color='#8E24AA', width=2), hovertemplate="<b>Data:</b> %{x|%b/%Y}<br><b>Rec. Portfel:</b> R$ %{y:,.2f}<extra></extra>"))
            fig_rec.add_trace(go.Scatter(x=df_consultor['Data'], y=df_consultor['Receita Parceiro(a)'], name="Receita Parceiro(a)", mode='lines+markers', line=dict(color='#FF8F00', width=2), hovertemplate="<b>Data:</b> %{x|%b/%Y}<br><b>Rec. Parceiro:</b> R$ %{y:,.2f}<extra></extra>"))
            fig_rec.update_layout(xaxis_title="Período", yaxis_title="Receita Mensal (R$)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=0, r=0, t=30, b=0), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), separators=",.", hovermode="x unified")
            fig_rec.update_yaxes(showgrid=True, gridcolor='rgba(200,200,200,0.3)', tickformat=",.2f")
            st.plotly_chart(fig_rec, use_container_width=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Comparativo de Curvas (Rankings)")
        fig_curvas = go.Figure()
        fig_curvas.add_trace(go.Scatter(x=df_consultor['Data'], y=df_consultor['Curva AuC'], name="Curva AuC", mode='lines+markers', line_shape='hv', line=dict(color='#1E88E5', width=3)))
        curva_receita_col = 'Curva Receita do Consultor' if 'Curva Receita do Consultor' in df_consultor.columns else 'Curva Receita'
        fig_curvas.add_trace(go.Scatter(x=df_consultor['Data'], y=df_consultor.get(curva_receita_col, pd.Series()), name="Curva Receita", mode='lines+markers', line_shape='hv', line=dict(color='#00C853', width=3)))
        fig_curvas.update_layout(xaxis_title="Período", yaxis_title="Ranking (Curva)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=0, r=0, t=30, b=0), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), yaxis=dict(showgrid=True, gridcolor='rgba(200,200,200,0.3)', type='category', categoryorder='array', categoryarray=['D', 'C', 'B', 'A']))
        st.plotly_chart(fig_curvas, use_container_width=True)
