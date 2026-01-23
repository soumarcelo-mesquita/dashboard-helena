import streamlit as st
import pandas as pd
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from api_client import HelenaAPIClient
from data_processor import DataProcessor
from visualizations import Visualizer
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Page config
st.set_page_config(page_title="Dashboard", layout="wide")

# Load environment variables
load_dotenv()

def format_currency_br(value):
    """Formata valor numérico para o padrão monetário PT-BR (R$ 1.234,56)"""
    if value is None: return "R$ 0,00"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Load auth config
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Authenticator
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Login
# Em versões recentes, o login não recebe mais o rótulo como primeiro argumento posicional
authenticator.login(location='main')

# O status de autenticação fica disponível em st.session_state
authentication_status = st.session_state.get('authentication_status')
name = st.session_state.get('name')
username = st.session_state.get('username')

if authentication_status:
    st.sidebar.title(f"Bem-vindo, {name}")
    
    # Initialize API and Data Processor
    api_client = HelenaAPIClient()
    data_processor = DataProcessor()
    
    # Sidebar Filters
    st.sidebar.header("Filtros e Configurações")
    
    # Action Type Filter (visto no sampleCode.js)
    action_types = ["Todos", "258", "439", "FUNASA", "CARPH"]
    selected_action = st.sidebar.selectbox("Filtrar por Tipo de Ação", action_types)
    
    today = datetime.now().date()
    start_default = today - timedelta(days=30)
    
    col_d1, col_d2 = st.sidebar.columns(2)
    with col_d1:
        start_date = st.date_input("Data Inicial", value=start_default, format="DD/MM/YYYY")
    with col_d2:
        end_date = st.date_input("Data Final", value=today, format="DD/MM/YYYY")
    
    # Panel ID is constant as per requested
    panel_id = os.getenv("HELENA_PANEL_ID")
    
    # Threshold for stuck cards
    threshold_days = st.sidebar.slider("Dias para considerar card 'travado'", 1, 60, 15)
    
    # Refresh button
    if st.sidebar.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.rerun()

    if not panel_id:
        st.warning("Por favor, insira um Panel ID na barra lateral ou no arquivo .env")
        st.stop()

    # Data Fetching
    with st.spinner("Buscando dados da API Helena..."):
        cards = api_client.get_cards(panel_id)
    
    if not cards:
        st.error("Nenhum card encontrado para este painel. Verifique o ID e o Token da API.")
        st.stop()
        
    # Data Processing
    df_raw = data_processor.process_cards(cards)
    
    # Aplicar filtros
    df = df_raw.copy()
    
    # Filtro de Action Type
    if selected_action != "Todos":
        df = df[df["actionType"] == selected_action]
        
    # Filtro de Data de Criação
    # Converter para datetime64[ns, UTC] para comparar com createdAt que tem timezone
    start_dt = pd.to_datetime(start_date).tz_localize('UTC')
    # Para o end_date, somar 1 dia para pegar até o final do dia selecionado
    end_dt = pd.to_datetime(end_date).tz_localize('UTC') + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    
    df = df[(df["createdAt"] >= start_dt) & (df["createdAt"] <= end_dt)]
    
    # Check if empty
    if df.empty:
        st.warning("⚠️ Nenhum card encontrado para o período e filtros selecionados.")
        st.stop()
    
    # KPIs atop the page
    st.title("Diogo Nobre Advogados")
    st.subheader("Performance no CRM")

    st.divider()
    
    metrics = data_processor.get_velocity_metrics(df)
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total de Cards", metrics['card_count'])
    kpi2.metric("Valor Total", format_currency_br(metrics['total_value']))
    kpi3.metric("Tempo Médio no Pipeline", f"{metrics['avg_total_days']} dias")
    
    # Stuck cards count
    stuck_df = df[df['days_in_status'] > threshold_days]
    kpi4.metric("Cards Travados", len(stuck_df), delta=f"{len(stuck_df)} alertas", delta_color="inverse")

    # Tabs for different visualizations
    tab_summary, tab_time, tab_tags, tab_alerts = st.tabs([
        "📋 Funil de Conversão", 
        "⏱️ Tempo & Velocidade", 
        "🏷️ Etiquetas", 
        "🚨 Alertas"
    ])

    with tab_summary:
        # Funnels at the beginning
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.subheader("Funil de Conversão (Quantidade)")
            funnel_data = data_processor.get_conversion_data(df)
            fig_funnel = Visualizer.plot_funnel(funnel_data)
            if fig_funnel:
                st.plotly_chart(fig_funnel, width="stretch")
            else:
                st.info("Sem dados para o funil de quantidade.")
            
        with col_f2:
            st.subheader("Funil de Conversão (Valor)")
            funnel_val = df.groupby("stepTitle")["monetaryAmount"].sum().reset_index()
            funnel_val.columns = ["Etapa", "Quantidade"]
            funnel_val["Etapa"] = pd.Categorical(funnel_val["Etapa"], categories=data_processor.step_order, ordered=True)
            funnel_val = funnel_val.sort_values("Etapa").dropna(subset=["Etapa"])
            
            fig_funnel_val = Visualizer.plot_funnel(funnel_val, title="Valor por Etapa")
            if fig_funnel_val:
                st.plotly_chart(fig_funnel_val, width="stretch")
            else:
                st.info("Sem dados para o funil de valor.")

        st.divider()
        st.subheader("Quantidade de Cards por Status")
        pivot_table = data_processor.get_status_pivot_table(df)
        
        # Tabela sem a configuração de alinhamento para evitar erros de compatibilidade
        cols_config = {col: st.column_config.NumberColumn(format="%d") for col in pivot_table.columns}
        st.dataframe(pivot_table, width="stretch", column_config=cols_config)

    with tab_time:
        st.subheader("Tempo Médio por Etapa")
        fig_time = Visualizer.plot_avg_time_by_step(df, threshold_slow=threshold_days)
        if fig_time:
            st.plotly_chart(fig_time, width="stretch")
        
        st.info(f"💡 As barras em vermelho indicam etapas onde o tempo médio excede {threshold_days} dias.")

    with tab_tags:
        col_t1, col_t2 = st.columns(2)
        tag_dist = data_processor.get_tag_distribution(df)
        
        with col_t1:
            st.subheader("Distribuição de Valor por Etiqueta")
            fig_tree = Visualizer.plot_tag_treemap(tag_dist)
            if fig_tree:
                st.plotly_chart(fig_tree, width="stretch")
            else:
                st.write("Sem dados de etiquetas.")
        
        with col_t2:
            st.subheader("Top Etiquetas por Receita")
            st.dataframe(
                tag_dist, 
                width="stretch",
                column_config={
                    "Valor Total": st.column_config.NumberColumn(format="R$ %.2f")
                }
            )

    with tab_alerts:
        st.subheader(f"Cards Travados (Há mais de {threshold_days} dias)")
        if not stuck_df.empty:
            # Selecionar colunas existentes
            available_cols = [c for c in ['title', 'stepTitle', 'days_in_status', 'responsibleUser', 'monetaryAmount'] if c in stuck_df.columns]
            alert_display = stuck_df[available_cols].copy()
            
            # Renomear para exibição
            rename_map = {
                'title': 'Título',
                'stepTitle': 'Etapa Atual',
                'days_in_status': 'Dias Parado',
                'responsibleUser': 'Responsável',
                'monetaryAmount': 'Valor'
            }
            alert_display.rename(columns=rename_map, inplace=True)
            
            # Formatar nome do responsável se for dict
            if 'Responsável' in alert_display.columns:
                alert_display['Responsável'] = alert_display['Responsável'].apply(lambda x: x.get('name') if isinstance(x, dict) else x)
            
            st.dataframe(
                alert_display.sort_values('Dias Parado', ascending=False),
                width="stretch",
                column_config={
                    "Valor": st.column_config.NumberColumn(format="R$ %.2f")
                }
            )
        else:
            st.success("Nenhum card travado encontrado!")

    # Logout button fixed at the bottom of sidebar
    st.sidebar.markdown('<div class="sidebar-spacer" style="height: 30vh;"></div>', unsafe_allow_html=True)
    st.sidebar.divider()
    authenticator.logout(location='sidebar')

elif authentication_status == False:
    st.error('Usuário ou senha incorretos')
elif authentication_status == None:
    st.warning('Por favor, insira suas credenciais')

# CSS Customization for Dark Mode
st.markdown("""
<style>
    .stMetric {
        background-color: #1e2130;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #3d4156;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #262730;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding: 10px 20px 10px 20px !important;
    }
    /* Estilo para garantir que o logout fique embaixo se houver espaço */
    .sidebar-spacer {
        flex-grow: 1;
    }
</style>
""", unsafe_allow_html=True)
