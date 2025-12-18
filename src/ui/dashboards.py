import plotly.express as px
import plotly.graph_objects as go  # <--- Importante para os marcadores customizados
import pandas as pd
from datetime import datetime, time, date
import pytz
from src.controllers.Sensor import Sensor

sensor = Sensor()
BRAZIL_TZ = pytz.timezone("America/Sao_Paulo")

# --- CONFIGURAÇÕES VISUAIS ---
# Paleta Neon para Fundo Escuro (#1E2130)
CORES_MAPA = {
    "Dia Par": "#00E5FF",  # Ciano Neon (Água Elétrica)
    "Dia Ímpar": "#FF9F1C",  # Laranja Solar (Contraste)
}

# CONTROLE DE DENSIDADE (Marcadores)
# Mostra 1 marcador a cada N linhas de dados.
# Se sua leitura é a cada 5 min, use 12 para ter 1 marcador por hora.
DENSIDADE_MARCADORES = 4


def get_datetimes(dt_input):
    if isinstance(dt_input, str):
        dt = datetime.strptime(dt_input, "%Y-%m-%d %H:%M:%S")
    elif isinstance(dt_input, date) and not isinstance(dt_input, datetime):
        dt = datetime.combine(dt_input, time.min)
    elif isinstance(dt_input, datetime):
        dt = dt_input
    else:
        raise ValueError(f"Tipo de data inválido: {type(dt_input)}")

    if dt.tzinfo is None:
        dt_aware = BRAZIL_TZ.localize(dt)
    else:
        dt_aware = dt.astimezone(BRAZIL_TZ)

    return dt_aware.strftime("%d/%m/%Y %H:%M")


def create_data(data_inicio, data_final):
    data_inicio_str = get_datetimes(data_inicio)
    data_fim_str = get_datetimes(data_final)

    # Carrega dados brutos
    df = sensor.get_dados_historicos_1h(data_inicio_str, data_fim_str)

    # --- CORREÇÃO AQUI ---
    # Seus dados vêm como "13/12/2025" (String).
    # O dayfirst=True é OBRIGATÓRIO para ele não confundir Dia com Mês.
    df["date"] = pd.to_datetime(df["date"], dayfirst=True)

    # Se ainda der warning, você pode forçar o formato assim (opcional, mas mais seguro):
    # df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y %H:%M:%S")

    df["value_percent"] = round(df["value_percent"] * 100, 0)
    df = df.sort_values(by="date")

    # 2. Identificador único do dia
    df["dia_formatado"] = df["date"].dt.strftime("%d/%m")

    # 3. Identificador da Legenda
    df["legenda_tipo"] = df["date"].dt.day.apply(
        lambda x: "Dia Par" if x % 2 == 0 else "Dia Ímpar"
    )

    return df


# --- FUNÇÃO AUXILIAR DE ESTILO (DRY) ---
def aplicar_estilo_dark(fig):
    """Aplica o tema escuro premium, cores de texto claras e tooltips."""
    fig.update_layout(
        # Fundo Transparente (se integra ao container do Streamlit)
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        # Legenda no Topo Direito
        legend=dict(
            title=None,
            orientation="h",
            yanchor="bottom",
            y=1.12,
            x=1,
            xanchor="right",
            font=dict(color="#E0E0E0"),  # Texto Claro
        ),
        margin=dict(t=50, l=0, r=0, b=0),
        # Eixo X (Tempo)
        xaxis=dict(
            title=None,
            showline=True,
            linecolor="#4B4E5F",  # Cinza médio
            linewidth=2,
            showgrid=False,  # Grid vertical desligado para limpar
            tickfont=dict(
                family="Segoe UI", size=12, color="#B0B3C5"
            ),  # Cinza azulado claro
        ),
        # Eixo Y (Nível)
        yaxis=dict(
            title=dict(
                text="Nível da Caixa (%)",
                font=dict(family="Segoe UI", size=14, color="#E0E0E0"),
            ),
            showline=False,
            showgrid=True,  # Mantém grid horizontal para leitura
            gridcolor="#353849",  # Grid muito sutil
            tickfont=dict(family="Segoe UI", size=12, color="#B0B3C5"),
        ),
        hovermode="x unified",
        # Tooltip Estilizado
        hoverlabel=dict(
            bgcolor="#262A3B",  # Fundo do tooltip (combina com seu card)
            bordercolor="#4B4E5F",
            font_size=14,
            font_family="Segoe UI",
            font_color="#FFFFFF",
        ),
    )
    return fig


def create_graph_line(data_inicio, data_final):
    df = create_data(data_inicio, data_final)

    # --- LÓGICA DE PREENCHIMENTO DE BURACOS ---
    novas_linhas = []
    dias_unicos = df["dia_formatado"].unique()

    for i in range(len(dias_unicos) - 1):
        dia_atual = dias_unicos[i]
        dia_seguinte = dias_unicos[i + 1]

        mask_dia_seguinte = df["dia_formatado"] == dia_seguinte
        if mask_dia_seguinte.any():
            primeiro_ponto_next = df[mask_dia_seguinte].iloc[0].copy()
            primeiro_ponto_next["dia_formatado"] = dia_atual
            dia_atual_num = int(dia_atual.split("/")[0])
            primeiro_ponto_next["legenda_tipo"] = (
                "Dia Par" if dia_atual_num % 2 == 0 else "Dia Ímpar"
            )
            novas_linhas.append(primeiro_ponto_next)

    if novas_linhas:
        df = pd.concat([df, pd.DataFrame(novas_linhas)], ignore_index=True)
        df = df.sort_values(by="date")
    # ------------------------------------------

    # 1. CRIA A LINHA SUAVE
    fig = px.line(
        df,
        x="date",
        y="value_percent",
        title="Evolução do Nível (Linha)",
        color="legenda_tipo",
        line_group="dia_formatado",
        color_discrete_map=CORES_MAPA,
    )

    fig.update_traces(
        line_shape="spline",
        line_width=5,
        hovertemplate="<b>Data:</b> %{x|%d/%m %H:%M}<br><b>Nível:</b> %{y}%<br><extra></extra>",
    )

    # 2. ADICIONA MARCADORES (BOLINHAS)
    # Filtra 1 a cada N pontos (definido em DENSIDADE_MARCADORES)
    df_markers = df.iloc[::DENSIDADE_MARCADORES, :].copy()

    # --- NOVO: FORÇA O MARCADOR NO ÚLTIMO REGISTRO ---
    if not df.empty:
        ultimo_registro = df.iloc[[-1]]  # Pega a última linha (o dado mais atual)

        # Concatena o último registro ao dataframe de marcadores
        # O drop_duplicates garante que se o último ponto JÁ for um múltiplo de 12, ele não duplica
        df_markers = pd.concat([df_markers, ultimo_registro]).drop_duplicates(
            subset=["date"]
        )
    # -------------------------------------------------

    for tipo_legenda, color_hex in CORES_MAPA.items():
        df_group = df_markers[df_markers["legenda_tipo"] == tipo_legenda]

        if not df_group.empty:
            fig.add_trace(
                go.Scatter(
                    x=df_group["date"],
                    y=df_group["value_percent"],
                    mode="markers",
                    marker=dict(
                        color=color_hex, size=10, line=dict(width=1, color="#1E2130")
                    ),
                    name=tipo_legenda,
                    legendgroup=tipo_legenda,
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

    return aplicar_estilo_dark(fig)


def create_graph_bar(data_inicio, data_final):
    df = create_data(data_inicio, data_final)

    fig = px.bar(
        df,
        x="date",
        y="value_percent",
        title="Evolução do Nível (Barras)",
        color="legenda_tipo",
        color_discrete_map=CORES_MAPA,
    )

    fig.update_traces(
        marker_line_width=0,  # Mantém sem borda para não poluir visualmente
        hovertemplate="<b>Data:</b> %{x|%d/%m %H:%M}<br><b>Nível:</b> %{y}%<br><extra></extra>",
    )

    fig = aplicar_estilo_dark(fig)

    # --- AJUSTE DE ESPAÇAMENTO ---
    # bargap=0.1 coloca um pequeno respiro entre as barras.
    # Se quiser mais espaço, aumente para 0.2. Se quiser menos, use 0.05.
    fig.update_layout(bargap=0.1)

    return fig
