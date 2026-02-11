import streamlit as st
from datetime import datetime, timedelta
import pytz
import os
from dotenv import load_dotenv

# --- SEUS IMPORTS ---
import src.ui.dashboards as dashboards
from src.ui.components import render_card_reservatorio_topo
from src.controllers.Rele import ReleTuya

# Carrega variaveis de ambiente
load_dotenv()

# --- CONFIGURAÇÃO ---
BRAZIL_TZ = pytz.timezone("America/Sao_Paulo")
INTERVALO_ATUALIZACAO_SEG = 190

# ==============================================================================
# --- SOLUÇÃO DE MEMÓRIA GLOBAL (RAM) ---
# Substitui o arquivo .txt por um objeto persistente na memória do servidor
# ==============================================================================


class EstadoSistema:
    def __init__(self):
        self.bomba_8_ligada = False


@st.cache_resource
def get_estado_global():
    # Esta função roda apenas UMA vez e fica em cache.
    # O objeto 'EstadoSistema' será o mesmo para todos os usuários.
    return EstadoSistema()


# Instancia a memória global
memoria_global = get_estado_global()

# ==============================================================================


def show(sensor, rele):
    # --- 1. INICIALIZAÇÃO DOS CONTROLADORES DE PULSO ---
    try:
        id_on = os.getenv("RELE_LAV_8P_ON_DEVICE_ID")
        id_off = os.getenv("RELE_LAV_8P_OFF_DEVICE_ID")
        ctrl_8_on = ReleTuya(id_on)
        ctrl_8_off = ReleTuya(id_off)
    except Exception as e:
        st.error(f"Erro ao configurar Relés Tuya: {e}")
        ctrl_8_on = None
        ctrl_8_off = None

    # --- ESTADOS LOCAIS (INTERFACE) ---
    if "config_bombas" not in st.session_state:
        st.session_state["config_bombas"] = {
            "bomba_8": {
                "nome": "Bomba Principal (8 Polegadas)",
                "ligada": memoria_global.bomba_8_ligada,  # <--- Pega da memória RAM Global
            },
            "bomba_12": {
                "nome": "Bomba 12 Polegadas",
                "ligada": rele.get_status_bomba(),
            },
            "bomba_12_reserva": {"nome": "Bomba 12 Pol (Reserva)", "ligada": False},
        }

    if "confirmacao_pendente" not in st.session_state:
        st.session_state["confirmacao_pendente"] = None

    # Filtros de data
    if "data_inicio_padrao" not in st.session_state:
        st.session_state["data_inicio_padrao"] = datetime.now(BRAZIL_TZ) - timedelta(
            days=1
        )
    if "data_final_padrao" not in st.session_state:
        st.session_state["data_final_padrao"] = datetime.now(BRAZIL_TZ)

    # --- FRAGMENTO AUTOMÁTICO ---
    @st.fragment(run_every=INTERVALO_ATUALIZACAO_SEG)
    def painel_telemetria_auto_update():

        # Sincroniza a memória global com a visualização local a cada atualização
        # Isso garante que se outra pessoa ligou, você vê atualizado aqui
        st.session_state["config_bombas"]["bomba_8"][
            "ligada"
        ] = memoria_global.bomba_8_ligada

        # Leitura Sensores
        perc, status = sensor.get_status_reservatorio()
        data_base = sensor.get_tempo_pin()
        nivel_safe = max(0, min(100, perc))

        # --- CAMADA DE PROTEÇÃO (25%) ---
        bomba_12_ligada = (
            st.session_state["config_bombas"].get("bomba_12", {}).get("ligada", False)
        )
        bomba_8_ligada = memoria_global.bomba_8_ligada  # Verifica direto na RAM Global

        if int(nivel_safe) <= 25:
            mudou_algo = False

            # Desliga Bomba 12
            if bomba_12_ligada:
                rele.DESLIGAR_BOMBA()
                st.session_state["config_bombas"]["bomba_12"]["ligada"] = False
                mudou_algo = True

            # Desliga Bomba 8
            if bomba_8_ligada:
                if ctrl_8_off:
                    ctrl_8_off.criando_pulso(0.1, False)

                # Atualiza memória GLOBAL e LOCAL
                memoria_global.bomba_8_ligada = False
                st.session_state["config_bombas"]["bomba_8"]["ligada"] = False
                mudou_algo = True

            if mudou_algo:
                st.rerun()

        # Tratamento de data/hora
        try:
            data_base_dt = datetime.strptime(data_base, "%d/%m/%Y %H:%M:%S")
            data_base_dt = data_base_dt.replace(tzinfo=BRAZIL_TZ)
            prox_atualizacao = (
                data_base_dt + timedelta(seconds=INTERVALO_ATUALIZACAO_SEG)
            ).strftime("%H:%M:%S")
        except:
            prox_atualizacao = "..."

        dados = {
            "nivel": perc,
            "status": status,
            "mA": sensor.get_vl_mA(),
            "hora": sensor.get_tempo_pin(),
            "local": sensor.get_local(),
        }

        # --- HEADER ---
        st.markdown(
            f"""
            <div style="background-color:#1E1E1E; padding:15px; border-radius:10px; display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                <span style="color:#FFF; font-size:1.2rem;">⏱️ Última Leitura: <b>{dados['hora']}</b></span>
                <span style="color:#00ADB5; font-size:1.0rem;">Próxima atualização: <b>{prox_atualizacao}</b></span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_monitor, col_controle = st.columns([1, 2])

        # Coluna 1: Reservatório
        with col_monitor:
            with st.container(border=True):
                render_card_reservatorio_topo(
                    f"Caixa da {dados['local']}",
                    dados["nivel"],
                    dados["mA"],
                    dados["status"],
                )

        # Coluna 2: Bombas
        with col_controle:
            with st.container(border=True):
                st.markdown("##### ⚙️ Painel de Controle de Bombas")
                st.info("Clique para armar, clique novamente para confirmar.")

                chaves = list(st.session_state["config_bombas"].keys())

                for chave in chaves:
                    bomba = st.session_state["config_bombas"][chave]

                    with st.container(border=True):
                        c1, c2, c3 = st.columns([2, 1, 1])

                        # 1. Nome
                        with c1:
                            st.markdown(
                                f"<div style='padding-top:5px; font-weight:bold;'>{bomba['nome']}</div>",
                                unsafe_allow_html=True,
                            )

                        # 2. Status Visual
                        with c2:
                            is_ligada = bomba["ligada"]
                            cor = "#2ECC71" if is_ligada else "#FF6B6B"
                            txt = "LIGADA" if is_ligada else "PARADA"
                            st.markdown(
                                f"<div style='text-align:center; color:{cor}; font-weight:500; border:1px solid {cor}; border-radius:4px; padding:6px;'>● {txt}</div>",
                                unsafe_allow_html=True,
                            )

                        # 3. Botão
                        with c3:
                            if st.session_state.get("confirmacao_pendente") == chave:
                                lbl = "CONFIRMAR?"
                                tp = "primary"
                            else:
                                lbl = "DESLIGAR" if is_ligada else "LIGAR"
                                tp = "secondary"

                            def on_click_bomba(k=chave):
                                if st.session_state.get("confirmacao_pendente") == k:
                                    # -- AÇÃO CONFIRMADA --
                                    estado_atual = st.session_state["config_bombas"][k][
                                        "ligada"
                                    ]
                                    novo_estado = not estado_atual

                                    # HARDWARE & MEMÓRIA
                                    if k == "bomba_12":
                                        if novo_estado:
                                            rele.LIGAR_BOMBA()
                                        else:
                                            rele.DESLIGAR_BOMBA()

                                    elif k == "bomba_8":
                                        # 1. Hardware (Pulso)
                                        if ctrl_8_on and ctrl_8_off:
                                            if novo_estado:
                                                ctrl_8_on.criando_pulso(0.02, True)
                                            else:
                                                ctrl_8_off.criando_pulso(1, True)
                                                verifica_desligado = (
                                                    ctrl_8_off.verifica_status(3)
                                                )

                                                if verifica_desligado:
                                                    ctrl_8_off.acionando_rele(
                                                        ligar=True
                                                    )

                                        # 2. Salva memória GLOBAL (RAM Server)
                                        memoria_global.bomba_8_ligada = novo_estado

                                    # Atualiza UI Local
                                    st.session_state["config_bombas"][k][
                                        "ligada"
                                    ] = novo_estado
                                    st.session_state["confirmacao_pendente"] = None
                                else:
                                    # -- PRIMEIRO CLIQUE --
                                    st.session_state["confirmacao_pendente"] = k

                            st.button(
                                lbl,
                                key=f"btn_{chave}",
                                type=tp,
                                on_click=on_click_bomba,
                                use_container_width=True,
                            )

    # --- EXECUÇÃO ---
    painel_telemetria_auto_update()

    st.markdown("---")

    # --- DASHBOARDS (Filtros e Gráficos) ---
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

    if data_inicio and data_final:
        if data_final < data_inicio:
            st.error("⚠️ Erro: A Data Final deve ser maior que a Data de Início.")
            # st.stop() não é ideal dentro de uma função parcial, melhor usar return
            return

        with st.container(border=True):
            fig = dashboards.create_graph_line(data_inicio, data_final)
            st.plotly_chart(fig, width="stretch")

        with st.container(border=True):
            fig_bar = dashboards.create_graph_bar(data_inicio, data_final)
            st.plotly_chart(fig_bar, width="stretch")
