import os
import requests
import streamlit as st
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz


class SensorClient:
    def __init__(self, usuario="Usuario", local="Lavadeira", minutes_to_timestamp=15):
        load_dotenv()
        self._base_url = os.getenv("BASE_URL")
        self.__TOKEN__ = None
        self._MINIMO = 4.0
        self._MAXIMO = 6.8
        self._MINUTES_TO_TIMESTAMP = minutes_to_timestamp * 60 * 1000
        self._usuario = usuario
        self._local = local
        self._BRAZIL_TZ = pytz.timezone("America/Sao_Paulo")  # Fuso Horário Definido

    def _renovar_token_(self):
        # Lógica de renovação de token (mantida simplificada aqui)
        payload = {"username": os.getenv("USUARIO"), "password": os.getenv("PASSWORD")}
        try:
            response = requests.post(
                f"{self._base_url}/api/auth/login", json=payload, timeout=10
            )
            if response.status_code == 200:
                self.__TOKEN__ = f"Bearer {response.json()['token']}"
            else:
                raise Exception("FalhaToken")
        except:
            raise Exception("ErroConexaoToken")

    @st.cache_data(ttl=30, show_spinner=False)
    def _consultar_api_unique_(_self):
        # Busca último dado
        url = f"{_self._base_url}/api/plugins/telemetry/DEVICE/{os.getenv('SENSOR_LAVADEIRA')}/values/timeseries"
        headers = {"Authorization": _self.__TOKEN__}
        try:
            response = requests.get(
                url, headers=headers, params={"useStrictDataTypes": "false"}, timeout=5
            )
            if response.status_code == 401:
                _self._renovar_token_()
                headers["Authorization"] = _self.__TOKEN__
                response = requests.get(
                    url,
                    headers=headers,
                    params={"useStrictDataTypes": "false"},
                    timeout=5,
                )
            return response.json()
        except:
            return {}

    @st.cache_data(ttl=60, show_spinner=False)
    def _consultar_api_time_series_(_self, ts_inicio, ts_fim):
        # Busca histórico
        url = f"{_self._base_url}/api/plugins/telemetry/DEVICE/{os.getenv('SENSOR_LAVADEIRA')}/values/timeseries?keys=ia&startTs={ts_inicio}&endTs={ts_fim}&interval=3600000&limit=1000&agg=AVG"
        headers = {"Authorization": _self.__TOKEN__}
        try:
            response = requests.get(
                url, headers=headers, params={"useStrictDataTypes": "false"}, timeout=10
            )
            if response.status_code == 401:
                _self._renovar_token_()
                headers["Authorization"] = _self.__TOKEN__
                response = requests.get(
                    url,
                    headers=headers,
                    params={"useStrictDataTypes": "false"},
                    timeout=10,
                )
            return response.json()
        except:
            return {}

    def _analisando_tendencias_(self, ts_ini, ts_fim, valor_atual):
        try:
            dados = self._consultar_api_time_series_(ts_ini, ts_fim)
            if not dados or "ia" not in dados:
                return 0, "Sem Dados"

            valores = [float(i["value"]) for i in dados["ia"]]
            if not valores:
                return 0, "Aguardando"

            media = sum(valores) / len(valores)
            margem = media * 0.003  # 0.3%

            if valor_atual > (media + margem):
                status = "Enchendo"
            elif valor_atual < (media - margem):
                status = "Esvaziando"
            else:
                status = "Estavel"

            return round(media, 2), status
        except:
            return 0, "Com Problema"

    def get_dados_instantaneos(self):
        """Retorna lista bruta: [user, status, local, data, hora, full_dt, mA, perc, tendencia, media]"""
        try:
            dados = self._consultar_api_unique_()
            if not dados or "ia" not in dados:
                return None

            val_mA = float(dados["ia"][0]["value"])
            ts = int(dados["ia"][0]["ts"])

            # Timestamp para Data BR
            dt_obj = datetime.fromtimestamp(ts / 1000, self._BRAZIL_TZ)

            # Normalização simples
            perc = max(
                0.0, min(1.0, (val_mA - self._MINIMO) / (self._MAXIMO - self._MINIMO))
            )

            # Simulação de status (para simplificar o código aqui, ou use sua lógica de tendência)
            media, status = self._analisando_tendencias_(
                int(ts - self._MINUTES_TO_TIMESTAMP), int(ts), val_mA
            )

            return [
                self._usuario,  # 0
                "Normal",  # 1
                self._local,  # 2
                dt_obj.strftime("%Y%m%d"),  # 3
                dt_obj.strftime("%H:%M:%S"),  # 4
                dt_obj.strftime("%d/%m/%Y %H:%M:%S"),  # 5
                val_mA,  # 6
                perc,  # 7
                status,  # 8
                media,  # 9
            ]
        except:
            return None

    def _converter_para_ms_(self, data_str):
        """
        Função auxiliar para converter string (dd/mm/yyyy [HH:MM])
        para timestamp em milissegundos.
        """
        if not data_str:
            return None

        # 1. Normalização: Se a string tiver apenas a data (ex: 10 chars "01/08/2025"),
        # adiciona o horário 00:00.
        if len(data_str.strip()) <= 10:
            data_str = f"{data_str.strip()} 00:00"

        try:
            # 2. Criação do objeto datetime
            # Formato esperado: Dia/Mês/Ano Hora:Minuto
            dt_obj = datetime.strptime(data_str, "%d/%m/%Y %H:%M")

            # 3. Conversão para timestamp (segundos) e depois para milissegundos
            # int() remove as casas decimais
            timestamp_ms = int(dt_obj.timestamp() * 1000)

            return timestamp_ms
        except ValueError as e:
            print(f"Erro ao converter data '{data_str}': {e}")
            return None

    def get_historico_raw(self, date_inicio, date_fim):
        """Busca dados brutos para o gráfico

        Parameters:
        date_inicio: precisa estar no formato 01/12/2000 23:45 caso não tenha as horas
        será considerado o padrão de 00:00

        date_fim: precisa estar no formato 01/12/2000 23:45 caso não tenha as horas
        será considerado o padrão de 00:00
        """

        timestamp_inicio = self._converter_para_ms_(date_inicio)
        timestamp_fim = self._converter_para_ms_(date_fim)

        dados = self._consultar_api_time_series_(timestamp_inicio, timestamp_fim)
        lista_final = []
        if dados and "ia" in dados:
            for p in dados["ia"]:
                perc = max(
                    0.0,
                    min(
                        1.0,
                        (float(p["value"]) - self._MINIMO)
                        / (self._MAXIMO - self._MINIMO),
                    ),
                )
                lista_final.append(
                    {
                        "date": datetime.fromtimestamp(
                            int(p["ts"]) / 1000, self._BRAZIL_TZ
                        ).strftime("%d/%m/%Y %H:%M:%S"),
                        "ts": int(p["ts"]),
                        "value_mA": float(p["value"]),
                        "value_percent": round(perc, 2),
                    }
                )
        return lista_final
