import streamlit as st
import datetime


def load_css():
    """Lê o arquivo CSS e injeta no Streamlit."""
    try:
        with open("assets/css/style.css", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass


def _obter_classes_visuais(nivel_percentual, status_tendencia):
    # Regra de Cores
    if nivel_percentual < 30:
        cls_cor = "nivel-critico"
    elif 30 <= nivel_percentual < 50:
        cls_cor = "nivel-alerta"
    else:
        cls_cor = "nivel-normal"

    # Regra de Movimento
    status_lower = str(status_tendencia).lower()
    if "enchendo" in status_lower:
        cls_anim, icone, classe_icone = "anim-rapida", "⬆️", "piscando"
    elif "esvaziando" in status_lower:
        cls_anim, icone, classe_icone = "anim-rapida", "⬇️", "piscando"
    else:
        cls_anim, icone, classe_icone = "anim-lenta", "⏸️", ""

    return cls_cor, cls_anim, icone, classe_icone


def render_card_reservatorio_topo(titulo, nivel_atual, vl_mA, estado_reservatorio):
    nivel_safe = max(0, min(100, nivel_atual))
    altura_visual = max(10, nivel_safe) if nivel_safe > 0 else 0

    cls_cor, cls_anim, icone, cls_icone = _obter_classes_visuais(
        nivel_safe, estado_reservatorio
    )

    # CORREÇÃO VISUAL:
    # 1. Removi a classe 'card-dashboard' para não ter borda dupla.
    # 2. Aumentei min-height para 460px (para alinhar com as 3 bombas da direita).
    # 3. Adicionei display:flex para centralizar o tanque verticalmente no espaço maior.
    st.markdown(
        f"""
    <div style="height: 80%; min-height: 383px; display: flex; flex-direction: column; justify-content: center; align-items: center;">
        <div class="card-title" style="margin-bottom: 5px;">{titulo}</div>
        <div class="tanque-moderno">
            <div class="agua-base {cls_cor} {cls_anim}" style="height: {altura_visual}%;"></div>
            <div class="texto-porcentagem">{int(nivel_safe)}%</div>
        </div>
        <div style="margin-bottom: 5px; font-weight: bold; color: var(--texto-corpo);">
            Leitura: <span style="color: var(--destaque);">{vl_mA} mA</span>
        </div>
        <div class="indicador-container">
            <span class="{cls_icone}">{icone}</span>
            <span>{estado_reservatorio}</span>
        </div>
    </div>
        """,
        unsafe_allow_html=True,
    )


def render_header_telemetria(tempo_captura, segundos_restantes):
    """
    Renderiza o cabeçalho com a hora da captura e o contador regressivo.
    """
    mins, secs = divmod(int(segundos_restantes), 60)
    timer_fmt = f"{mins:02d}:{secs:02d}"

    cor_timer = "#00ADB5" if segundos_restantes > 60 else "#FF6B6B"

    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; 
                    background-color: #1E1E1E; padding: 10px 20px; border-radius: 8px; 
                    border: 1px solid #333; margin-bottom: 20px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 1.5rem;">⏱️</span>
                <div>
                    <div style="font-size: 0.8rem; color: #aaa;">Telemetria Capturada</div>
                    <div style="font-size: 1.1rem; font-weight: bold; color: #fff;">{tempo_captura}</div>
                </div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 0.8rem; color: #aaa;">Próxima atualização em:</div>
                <div style="font-size: 1.5rem; font-weight: bold; color: {cor_timer}; font-family: monospace;">
                    {timer_fmt}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
