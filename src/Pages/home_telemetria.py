import streamlit as st
from datetime import datetime, timedelta
import pytz
import time

# Seus imports
import src.ui.dashboards as dashboards
from src.ui.components import render_card_reservatorio_topo

# --- CONFIGURAÇÃO ---
BRAZIL_TZ = pytz.timezone("America/Sao_Paulo")
INTERVALO_ATUALIZACAO_SEG = 190 
TEMPO_RESPIRO_HARDWARE = 10 # <--- Ajuste aqui: Segundos que o sistema "finge" que já ligou enquanto o hardware processa

def show(sensor, rele):
    # --- ESTADOS GLOBAIS ---
    if "confirmacao_pendente" not in st.session_state:
        st.session_state["confirmacao_pendente"] = None
    
    # Armazena o que o usuário "pediu" e quando pediu
    if "estado_otimista" not in st.session_state:
        st.session_state["estado_otimista"] = {
            "ligada": False, # O estado que o usuário quer
            "timestamp": 0   # Quando o usuário clicou
        }

    # Filtros de data
    if "data_inicio_padrao" not in st.session_state:
        st.session_state["data_inicio_padrao"] = datetime.now(BRAZIL_TZ) - timedelta(days=1)
    if "data_final_padrao" not in st.session_state:
        st.session_state["data_final_padrao"] = datetime.now(BRAZIL_TZ)

    # --- FRAGMENTO AUTOMÁTICO ---
    @st.fragment(run_every=INTERVALO_ATUALIZACAO_SEG)
    def painel_telemetria_auto_update():
        
        # 1. LÓGICA DO ESTADO VISUAL (O SEGREDINHO)
        # --------------------------------------------------
        agora = time.time()
        tempo_passado = agora - st.session_state["estado_otimista"]["timestamp"]
        
        # Modo Otimista: Se o usuário clicou há pouco tempo, mostramos o que ele quer ver
        em_modo_espera = tempo_passado < TEMPO_RESPIRO_HARDWARE
        
        if em_modo_espera:
            # Confia no usuário enquanto o hardware trabalha
            status_para_exibir = st.session_state["estado_otimista"]["ligada"]
            aviso_status = "⏳ Processando..."
        else:
            # Já passou o tempo de espera? Agora a verdade é o hardware!
            try:
                status_real_hard = rele.get_status_bomba()
                status_para_exibir = status_real_hard
                aviso_status = "" # Tudo sincronizado
            except:
                status_para_exibir = False
                aviso_status = "⚠️ Erro leitura"

        # Leitura do sensor de nível (Independente da bomba)
        perc, status_nivel = sensor.get_status_reservatorio()
        nivel_safe = max(0, min(100, perc))

        # 2. CAMADA DE PROTEÇÃO AUTOMÁTICA
        # --------------------------------------------------
        # Se for proteção automática, desligamos o otimismo e forçamos desligar
        if int(nivel_safe) <= 20 and status_para_exibir:
            rele.DESLIGAR_BOMBA()
            st.session_state["estado_otimista"]["timestamp"] = 0 # Cancela delay
            st.rerun()

        # 3. HEADER E DADOS
        # --------------------------------------------------
        data_base = sensor.get_tempo_pin()
        try:
            dt_obj = datetime.strptime(data_base, "%d/%m/%Y %H:%M:%S").replace(tzinfo=BRAZIL_TZ)
            prox = (dt_obj + timedelta(seconds=INTERVALO_ATUALIZACAO_SEG)).strftime("%H:%M:%S")
        except:
            prox = "..."

        st.markdown(
            f"""
            <div style="background-color:#1E1E1E; padding:15px; border-radius:10px; display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                <span style="color:#FFF; font-size:1.2rem;">⏱️ Leitura: <b>{sensor.get_tempo_pin()}</b></span>
                <span style="color:#00ADB5; font-size:1.0rem;">Próxima: <b>{prox}</b></span>
            </div>
            """, unsafe_allow_html=True
        )

        col_monitor, col_controle = st.columns([1, 2])

        with col_monitor:
            with st.container(border=True):
                render_card_reservatorio_topo(f"Caixa {sensor.get_local()}", perc, sensor.get_vl_mA(), status_nivel)

        with col_controle:
            with st.container(border=True):
                st.markdown("##### ⚙️ Painel de Controle")
                st.info("Clique para armar, clique novamente para confirmar.")

                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 1, 1])
                    
                    with c1: 
                        st.markdown("<div style='padding-top:5px; font-weight:bold;'>Bomba 12 Polegadas</div>", unsafe_allow_html=True)
                        # Mostra se está aguardando o hardware
                        if aviso_status:
                            st.caption(f"{aviso_status}")

                    with c2:
                        cor = "#2ECC71" if status_para_exibir else "#FF6B6B"
                        txt = "LIGADA" if status_para_exibir else "PARADA"
                        st.markdown(f"<div style='text-align:center; color:{cor}; font-weight:500; border:1px solid {cor}; border-radius:4px; padding:6px;'>● {txt}</div>", unsafe_allow_html=True)

                    with c3:
                        if st.session_state["confirmacao_pendente"] == "bomba_12":
                            lbl, tp = "CONFIRMAR?", "primary"
                        else:
                            lbl = "DESLIGAR" if status_para_exibir else "LIGAR"
                            tp = "secondary"

                        def acao_botao():
                            if st.session_state["confirmacao_pendente"] == "bomba_12":
                                # 1. Define o que queremos fazer
                                novo_estado = not status_para_exibir 
                                
                                # 2. Atualiza o Hardware (sem esperar a resposta lenta)
                                if novo_estado:
                                    rele.LIGAR_BOMBA()
                                else:
                                    rele.DESLIGAR_BOMBA()
                                
                                # 3. Atualiza o Estado Otimista (enganar o olho do usuário por uns segundos)
                                st.session_state["estado_otimista"] = {
                                    "ligada": novo_estado,
                                    "timestamp": time.time() # Começa a contar os 10s agora
                                }
                                
                                st.session_state["confirmacao_pendente"] = None
                            else:
                                st.session_state["confirmacao_pendente"] = "bomba_12"

                        st.button(lbl, type=tp, on_click=acao_botao, use_container_width=True)

    painel_telemetria_auto_update()
    
    st.markdown("---")
    # ... Gráficos ...
    with st.container(border=True):
        col1, col2 = st.columns(2)
        ini = col1.datetime_input("Início", st.session_state["data_inicio_padrao"])
        fim = col2.datetime_input("Fim", st.session_state["data_final_padrao"])
        if ini and fim:
            st.plotly_chart(dashboards.create_graph_line(ini, fim), use_container_width=True)
            st.plotly_chart(dashboards.create_graph_bar(ini, fim), use_container_width=True)
