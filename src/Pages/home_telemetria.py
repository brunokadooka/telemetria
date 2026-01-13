import streamlit as st
from datetime import datetime, timedelta
import pytz

# Seus módulos (Ajuste os imports conforme a estrutura exata, se necessário)
# Assumindo que você está rodando do diretório raiz onde 'ui' e 'src' são visíveis
import src.ui.dashboards as dashboards
from src.ui.components import render_card_reservatorio_topo

# --- CONFIGURAÇÃO ---
BRAZIL_TZ = pytz.timezone("America/Sao_Paulo")
INTERVALO_ATUALIZACAO_SEG = 190  # 3 minutos


def show(sensor, rele):
    # --- ESTADOS GLOBAIS (Inicialização) ---
    if "config_bombas" not in st.session_state:
        # Importante: Lê o hardware na primeira carga
        st.session_state["config_bombas"] = {
            "bomba_principal": {"nome": "Bomba Principal (Simulação)", "ligada": False},
            "bomba_12": {
                "nome": "Bomba 12 Polegadas",
                "ligada": rele.get_status_bomba(),
            },
            "bomba_12_reserva": {"nome": "Bomba 12 Pol (Reserva)", "ligada": False},
        }

    if "confirmacao_pendente" not in st.session_state:
        st.session_state["confirmacao_pendente"] = None

    # --- ESTADOS DE FILTRO ---
    if "data_inicio_padrao" not in st.session_state:
        st.session_state["data_inicio_padrao"] = datetime.now(BRAZIL_TZ) - timedelta(
            days=1
        )
    if "data_final_padrao" not in st.session_state:
        st.session_state["data_final_padrao"] = datetime.now(BRAZIL_TZ)

    # --- FRAGMENTO AUTOMÁTICO (O Coração da Telemetria) ---
    @st.fragment(run_every=INTERVALO_ATUALIZACAO_SEG)
    def painel_telemetria_auto_update():

        # 1. Leitura de Sensores (Reservatório)
        perc, status = sensor.get_status_reservatorio()
        data_base = sensor.get_tempo_pin()

        nivel_safe = max(0, min(100, perc))

        ### ----> CAMADA DE PROTEÇÃO <---- ##
        #      DESLIGAR A BOMBA            #
        #        QUANDO ATINGIR O NIVEL    #
        #           CONSIDERADO 25%        #
        ### ------------------------------ ##

        # Primeiro verificamos se ela consta como ligada na memória
        bomba_esta_ligada = st.session_state["config_bombas"]["bomba_12"]["ligada"]

        # Se o nível for baixo E ela estiver ligada:
        #if int(nivel_safe) <= 20 and bomba_esta_ligada:
            # 1. Ação Física: Desliga o relé
            #rele.DESLIGAR_BOMBA()

            # 2. Ação Lógica: Atualiza a memória IMEDIATAMENTE
            #st.session_state["config_bombas"]["bomba_12"]["ligada"] = False

            # 3. Reinício: Manda o Streamlit rodar a tela de novo agora mesmo
            # Isso garante que o botão fique vermelho instantaneamente
            # st.rerun()

        # Tratamento de erro caso data_base venha vazia ou com formato diferente
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

        # Header do Painel (Informações de atualização)
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

                        # Nome
                        with c1:
                            st.markdown(
                                f"<div style='padding-top:5px; font-weight:bold;'>{bomba['nome']}</div>",
                                unsafe_allow_html=True,
                            )

                        # Luzinha (Status Visual)
                        with c2:
                            is_ligada = bomba["ligada"]
                            cor = "#2ECC71" if is_ligada else "#FF6B6B"
                            txt = "LIGADA" if is_ligada else "PARADA"
                            st.markdown(
                                f"<div style='text-align:center; color:{cor}; font-weight:500; border:1px solid {cor}; border-radius:4px; padding:6px;'>● {txt}</div>",
                                unsafe_allow_html=True,
                            )

                        # Botão de Ação
                        with c3:
                            if st.session_state.get("confirmacao_pendente") == chave:
                                lbl = "CONFIRMAR?"
                                tp = "primary"
                            else:
                                lbl = "DESLIGAR" if is_ligada else "LIGAR"
                                tp = "secondary"

                            # --- CALLBACK OTIMISTA ---
                            def on_click_bomba(k=chave):
                                if st.session_state.get("confirmacao_pendente") == k:
                                    # Lógica de confirmação e envio para hardware
                                    estado_atual = st.session_state["config_bombas"][k][
                                        "ligada"
                                    ]
                                    novo_estado = not estado_atual

                                    # Atualiza UI
                                    st.session_state["config_bombas"][k][
                                        "ligada"
                                    ] = novo_estado

                                    # Envia hardware
                                    if k == "bomba_12":
                                        if novo_estado:
                                            rele.LIGAR_BOMBA()
                                        else:
                                            rele.DESLIGAR_BOMBA()

                                    st.session_state["confirmacao_pendente"] = None
                                else:
                                    # Primeiro clique (Armar)
                                    st.session_state["confirmacao_pendente"] = k

                            st.button(
                                lbl,
                                key=f"btn_{chave}",
                                type=tp,
                                on_click=on_click_bomba,
                                use_container_width=True,
                            )

    # --- CHAMADA DO PAINEL ---
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
