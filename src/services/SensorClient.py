import os
import requests
import streamlit as st  # Necessário para o Cache
from dotenv import load_dotenv
from datetime import datetime, timedelta


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

    def _renovar_token_(self):
        payload = {"username": os.getenv("USUARIO"), "password": os.getenv("PASSWORD")}
        url = f"{self._base_url}/api/auth/login"
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                self.__TOKEN__ = f"Bearer {response.json()['token']}"
            else:
                raise Exception("FalhaToken")
        except Exception:
            raise Exception("ErroConexaoToken")

    # --- O TURBO: Cache de 30 segundos nas chamadas de API ---
    @st.cache_data(ttl=30, show_spinner=False)
    def _consultar_api_unique_(_self):
        # _self com underline evita erro de hash do Streamlit
        url = f"{_self._base_url}/api/plugins/telemetry/DEVICE/{os.getenv('SENSOR_LAVADEIRA')}/values/timeseries"
        headers = {"Authorization": _self.__TOKEN__}
        params = {"useStrictDataTypes": "false"}

        try:
            response = requests.get(
                url, headers=headers, params=params, timeout=(5, 10)
            )
            if response.status_code == 401:
                _self._renovar_token_()
                headers["Authorization"] = _self.__TOKEN__
                response = requests.get(
                    url, headers=headers, params=params, timeout=(5, 10)
                )

            response.raise_for_status()
            return response.json()
        except Exception:
            return {}

    @st.cache_data(ttl=60, show_spinner=False)
    def _consultar_api_time_series_(_self, ts_inicio, ts_fim):
        url = f"{_self._base_url}/api/plugins/telemetry/DEVICE/{os.getenv('SENSOR_LAVADEIRA')}/values/timeseries?keys=ia&startTs={ts_inicio}&endTs={ts_fim}&agg=AVG"
        headers = {"Authorization": _self.__TOKEN__}

        try:
            response = requests.get(
                url,
                headers=headers,
                params={"useStrictDataTypes": "false"},
                timeout=(10, 20),
            )
            if response.status_code == 401:
                _self._renovar_token_()
                headers["Authorization"] = _self.__TOKEN__
                response = requests.get(
                    url,
                    headers=headers,
                    params={"useStrictDataTypes": "false"},
                    timeout=(10, 20),
                )
            return response.json()
        except Exception:
            return {}

    def _convert_timestamp_date_(self, timestamp):
        if timestamp is None:
            return None, None
        dt_obj = datetime.fromtimestamp(float(timestamp) / 1000)
        return dt_obj, dt_obj.strftime("%d/%m/%Y %H:%M:%S")

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

    def create_pin_sensor(self):
        try:
            # Chama a função cacheada
            dados_json = self._consultar_api_unique_()

            if not dados_json or "ia" not in dados_json or not dados_json["ia"]:
                # Retorna estrutura vazia padrão em caso de erro para não quebrar índices
                return [
                    self._usuario,
                    "Sem Sinal",
                    self._local,
                    "",
                    "",
                    "---",
                    0.0,
                    0.0,
                    "Aguardando",
                    0.0,
                ]

            val_mA = float(dados_json["ia"][0]["value"])
            ts = int(dados_json["ia"][0]["ts"])

            _, dt_str = self._convert_timestamp_date_(ts)

            # Cálculo Percentual
            perc = round((val_mA - self._MINIMO) / (self._MAXIMO - self._MINIMO), 4)

            # Tendência
            media, status = self._analisando_tendencias_(
                int(ts - self._MINUTES_TO_TIMESTAMP), int(ts), val_mA
            )

            situacao = (
                "Normal"
                if val_mA > 4.0 and status != "Com Problema"
                else "Com Problema"
            )

            # MANTIVE A MESMA ESTRUTURA DE LISTA QUE SEU CONTROLLER USA
            return [
                self._usuario,  # 0
                situacao,  # 1
                self._local,  # 2
                datetime.now().strftime("%Y%m%d"),  # 3
                datetime.now().strftime("%d/%m/%Y %H:%M:%S"),  # 4
                dt_str,  # 5 (DATA DO PIN)
                val_mA,  # 6 (VALOR mA)
                perc,  # 7 (PERCENTUAL)
                status,  # 8 (STATUS)
                media,  # 9
            ]

        except Exception as e:
            print(f"Erro create_pin: {e}")
            return [
                self._usuario,
                "Erro",
                self._local,
                "",
                "",
                "---",
                0.0,
                0.0,
                "Erro",
                0.0,
            ]
