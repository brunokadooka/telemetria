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

def show(sensor, rele):
    # --- INICIALIZAÇÃO DE ESTADO ---
    if "confirmacao_pendente" not in st.session_state:
        st.session_state["confirmacao_pendente"] = None
    
    # Variáveis para a "Mentirinha Visual" (Feedback Instantâneo)
    if "override_visual" not in st.session_state:
        st.session_state["override_visual"] = {
            "ativo": False,      # Se estamos fingindo o status agora
            "status_fake": False,# Qual status estamos fingindo
            "timestamp": 0       # Quando começou a fingir
        }

    # Filtros de data
    if "data_inicio_padrao" not in st.session_state:
        st.session_state["data_inicio_padrao"] = datetime.now(BRAZIL_TZ) - timedelta(days=1)
    if "data_final_padrao" not in st.session_state:
        st.session_state["data_final_padrao"] = datetime.now(BRAZIL_TZ)

    # --- FRAGMENTO AUTOMÁTICO ---
    @st.fragment(run_every=INTERVALO_ATUALIZACAO_SEG)
    def painel_telemetria_auto_update():
        
        # 1. OBTER A VERDADE DO HARDWARE
        try:
            status_hardware = rele.get_status_bomba()
        except:
            status_hardware = False 
        
        # 2. DECIDIR O QUE MOSTRAR NA TELA (Hardware vs Mentirinha)
        # ---------------------------------------------------------
        # Verifica se o override (mentirinha) ainda é válido (dura 3 segundos após o clique)
        agora = time.time()
        tempo_override = agora - st.session_state["override_visual"]["timestamp"]
        
        if st.session_state["override_visual"]["ativo"] and tempo_override < 3:
            # MOSTRA O QUE O USUÁRIO QUER VER (Instantâneo)
            status_exibicao = st.session_state["override_visual"]["status_fake"]
            texto_status = "Processando..." # Aviso discreto
        else:
            # MOSTRA A VERDADE DO HARDWARE (Padrão)
            status_exibicao = status_hardware
            texto_status = ""
            # Desativa o override para garantir que na próxima leia o hardware
            st.session_state["override_visual"]["ativo"] = False

        # Monta o objeto para o loop de exibição
        bombas_ui = {
            "bomba_principal": {"nome": "Bomba Principal (Simulação)", "ligada": False},
            "bomba_12":        {"nome": "Bomba 12 Polegadas",          "ligada": status_exibicao},
            "bomba_12_reserva":{"nome": "Bomba 12 Pol (Reserva)",      "ligada": False},
        }

        # 3. LÓGICA DE SEGURANÇA (NÍVEL)
        perc, status_nivel = sensor.get_status_reservatorio()
        nivel_safe = max(0, min(100, perc))

        # Se nível crítico, ignora mentirinha e DESLIGA TUDO
        if int(nivel_safe) <= 20 and status_hardware:
            rele.DESLIGAR_BOMBA()
            st.session_state["override_visual"]["ativo"] = False # Cancela mentirinha
            st.rerun()

        # 4. RENDERIZAÇÃO
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
                
                for chave, dados_bomba in bombas_ui.items():
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([2, 1, 1])
                        
                        with c1: 
                            st.markdown(f"<div style='padding-top:5px; font-weight:bold;'>{dados_bomba['nome']}</div>", unsafe_allow_html=True)
                            # Mostra aviso se estiver no modo "Mentirinha"
                            if chave == "bomba_12" and texto_status:
                                st.caption(f"⏳ {texto_status}")

                        with c2:
                            is_on = dados_bomba['ligada']
                            cor = "#2ECC71" if is_on else "#FF6B6B"
                            txt = "LIGADA" if is_on else "PARADA"
                            st.markdown(f"<div style='text-align:center; color:{cor}; font-weight:500; border:1px solid {cor}; border-radius:4px; padding:6px;'>● {txt}</div>", unsafe_allow_html=True)

                        with c3:
                            if st.session_state["confirmacao_pendente"] == chave:
                                lbl, tp = "CONFIRMAR?", "primary"
                            else:
                                lbl = "DESLIGAR" if is_on else "LIGAR"
                                tp = "secondary"

                            def acao_botao(k=chave, estado_visual_atual=is_on):
                                if st.session_state["confirmacao_pendente"] == k:
                                    # 1. MANDA HARDWARE (Ação Real)
                                    novo_estado_real = not estado_visual_atual
                                    if k == "bomba_12":
                                        if novo_estado_real: 
                                            rele.LIGAR_BOMBA()
                                        else: 
                                            rele.DESLIGAR_B
