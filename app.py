import streamlit as st
from datetime import datetime, timedelta  # AQUI JÁ IMPORTAMOS O TIMEDELTA
import pytz
import base64
import src.ui.dashboards as dashboards

# Seus módulos
from src.controllers.Sensor import Sensor
from src.ui.components import (
    load_css,
    render_card_reservatorio_topo,
    render_header_telemetria,
)


# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Telemetria", page_icon="💧", layout="wide")
BRAZIL_TZ = pytz.timezone("America/Sao_Paulo")
INTERVALO_ATUALIZACAO_SEG = 240  # 4 minutos

# Instancia sensor e carrega CSS
sensor = Sensor()
load_css()


# 2. FUNÇÃO AUXILIAR PARA LER SUA LOGO LOCAL (SVG)
def get_img_as_base64(file_path):
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception as e:
        return None


# Carrega sua logo específica
logo_b64 = get_img_as_base64("assets/img/logo-dark-rancharia.svg")
# Se der erro na leitura, usa um placeholder transparente
img_tag = (
    f'<img src="data:image/svg+xml;base64,{logo_b64}" style="width: 200px; height: 100;">'
    if logo_b64
    else "💧"
)

# 3. CSS PARA NÃO CORTAR O TOPO
st.markdown(
    """
    <style>
        /* Empurra o conteúdo para baixo para não ficar escondido */
        .block-container {
            padding-top: 3.5rem; 
            padding-bottom: 3rem;
        }
        /* Remove menu padrão se quiser limpar a tela */
        #MainMenu {visibility: hidden;}
    </style>
""",
    unsafe_allow_html=True,
)

# AJUSTE AQUI: Aumentei width para 160px para a logo horizontal ficar legível
st.markdown(
    f"""
    <div style="
        display: flex; 
        align-items: center; 
        gap: 20px; 
        margin-bottom: 25px; 
        background-color: #262A3B; 
        padding: 10px 20px; /* Reduzi um pouco o padding vertical para a caixa não ficar gigante */
        border-radius: 12px; 
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    ">
        <img src="data:image/svg+xml;base64,{logo_b64}" 
            style="width: 150px; height: 100; filter: drop-shadow(0px 0px 2px rgba(255,255,255,0.3));">
        <div style="line-height: 1.2; border-left: 1px solid #444; padding-left: 20px;">
            <h3 style="margin: 0; font-size: 1.5rem; font-weight: 700; color: #E0E6ED;">
                Telemetria do SAE
            </h3>
            <span style="font-size: 1rem; color: #00ADB5; font-weight: 500;">
                Rancharia/SP
            </span>
        </div>
    </div>
""",
    unsafe_allow_html=True,
)

# --- ESTADOS GLOBAIS ---
if "config_bombas" not in st.session_state:
    st.session_state["config_bombas"] = {
        "bomba_principal": {"nome": "Bomba Principal (Simulação)", "ligada": False},
        "bomba_12": {"nome": "Bomba 12 Polegadas", "ligada": False},
        "bomba_12_reserva": {"nome": "Bomba 12 Pol (Reserva)", "ligada": False},
    }

if "confirmacao_pendente" not in st.session_state:
    st.session_state["confirmacao_pendente"] = None


# --- LÓGICA DO SESSION STATE (EVITA O RESET DO FILTRO) ---
if "data_inicio_padrao" not in st.session_state:
    agora_inicial = datetime.now(BRAZIL_TZ)
    st.session_state["data_inicio_padrao"] = agora_inicial - timedelta(days=1)

if "data_final_padrao" not in st.session_state:
    st.session_state["data_final_padrao"] = datetime.now(BRAZIL_TZ)
# ---------------------------------------------------------


# --- FUNÇÃO DO FRAGMENTO (O Segredo do Não-Reset) ---
# Tudo que estiver aqui dentro atualiza sozinho a cada 240s (4 min).
@st.fragment(run_every=INTERVALO_ATUALIZACAO_SEG)
def painel_telemetria_auto_update():

    # 1. Leitura dos Dados
    perc, status = sensor.get_status_reservatorio()
    hora_atual = datetime.now(BRAZIL_TZ).strftime("%H:%M:%S")

    # CORREÇÃO AQUI: Usamos timedelta nativo em vez de pd.Timedelta
    prox_atualizacao = (
        datetime.now(BRAZIL_TZ) + timedelta(seconds=INTERVALO_ATUALIZACAO_SEG)
    ).strftime("%H:%M:%S")

    dados_atuais = {
        "nivel": perc,
        "status": status,
        "mA": sensor.get_vl_mA(),
        "hora_leitura": hora_atual,
        "local": sensor.get_local(),
    }

    # 2. Header dentro do Fragmento
    st.markdown(
        f"""
        <div style="background-color:#1E1E1E; padding:15px; border-radius:10px; display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
            <span style="color:#FFF; font-size:1.2rem;">⏱️ Última Leitura: <b>{dados_atuais['hora_leitura']}</b></span>
            <span style="color:#00ADB5; font-size:1.0rem;">Próxima atualização: <b>{prox_atualizacao}</b></span>
        </div>
    """,
        unsafe_allow_html=True,
    )

    # 3. Layout das Colunas
    col_monitor, col_controle = st.columns([1, 2])

    # --- COLUNA 1: TANQUE ---
    with col_monitor:
        with st.container(border=True):
            # REMOVI O TITULO AQUI DE FORA ("##### Monitoramento")
            # Ele agora é renderizado dentro do componente para centralizar verticalmente junto
            render_card_reservatorio_topo(
                f"Caixa da {dados_atuais["local"]}",  # Passando o título aqui
                dados_atuais["nivel"],
                dados_atuais["mA"],
                dados_atuais["status"],
            )

    # --- COLUNA 2: BOMBAS ---
    with col_controle:
        with st.container(border=True):
            st.markdown("##### ⚙️ Painel de Controle de Bombas")
            st.info("Clique para armar, clique novamente para confirmar.")

            chaves = list(st.session_state["config_bombas"].keys())

            for chave in chaves:
                bomba = st.session_state["config_bombas"][chave]
                is_ligada = bomba["ligada"]

                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 1, 1])

                    with c1:
                        # Alinhamento vertical
                        st.markdown(
                            f"<div style='padding-top:5px; font-weight:bold;'>{bomba['nome']}</div>",
                            unsafe_allow_html=True,
                        )

                    with c2:
                        cor = "#00ADB5" if is_ligada else "#FF6B6B"
                        txt = "LIGADA" if is_ligada else "PARADA"
                        st.markdown(
                            f"<div style='text-align:center; color:{cor}; font-weight:bold; border:1px solid {cor}; border-radius:4px; padding:2px;'>● {txt}</div>",
                            unsafe_allow_html=True,
                        )

                    with c3:
                        if st.session_state["confirmacao_pendente"] == chave:
                            lbl = "CONFIRMAR?"
                            tp = "primary"
                        else:
                            lbl = "DESLIGAR" if is_ligada else "LIGAR"
                            tp = "secondary"

                        def on_click_bomba(k=chave):
                            if st.session_state["confirmacao_pendente"] == k:
                                st.session_state["config_bombas"][k]["ligada"] = (
                                    not st.session_state["config_bombas"][k]["ligada"]
                                )
                                st.session_state["confirmacao_pendente"] = None
                            else:
                                st.session_state["confirmacao_pendente"] = k

                            # Atualiza apenas este fragmento
                            st.rerun()

                        st.button(
                            lbl,
                            key=f"btn_{chave}",
                            type=tp,
                            on_click=on_click_bomba,
                            use_container_width=True,
                        )


# --- CHAMADA PRINCIPAL ---

# 1. Roda o painel (auto-refresh isolado)
painel_telemetria_auto_update()

st.markdown("---")

# 2. Área dos Dashboards
# --- CARD 1: FILTROS ---
with st.container(border=True):
    col1_data, col2_data = st.columns(2)

    with col1_data:
        data_inicio = st.datetime_input(
            "Data de Inicio:",
            value=st.session_state["data_inicio_padrao"],
            key="input_data_inicio",
        )

    with col2_data:
        data_final = st.datetime_input(
            "Data Final:",
            value=st.session_state["data_final_padrao"],
            key="input_data_final",
        )

# Validação Cronológica
if data_inicio and data_final:
    if data_final < data_inicio:
        st.error("⚠️ Erro: A Data Final deve ser maior que a Data de Início.")
        st.stop()

# --- CARD 2: GRÁFICO DE LINHA ---
with st.container(border=True):
    # Gera o gráfico
    fig = dashboards.create_graph_line(data_inicio, data_final)
    # Renderiza
    st.plotly_chart(fig, width="stretch")

# --- CARD 3: GRÁFICO DE BARRAS ---
with st.container(border=True):
    # Gera o gráfico
    fig_bar = dashboards.create_graph_bar(data_inicio, data_final)
    # Renderiza
    st.plotly_chart(fig_bar, width="stretch")
