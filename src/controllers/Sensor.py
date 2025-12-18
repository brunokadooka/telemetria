import pandas as pd
from src.services.SensorClient import SensorClient


class Sensor:
    def __init__(self):
        self.client = SensorClient()
        self._cache_dados = None

    def get_dados_historicos_1h(self, data_inicio, data_fim):
        lista_dados = self.client.get_historico_raw(data_inicio, data_fim)
        return pd.DataFrame(lista_dados)

    def get_status_reservatorio(self):
        """Retorna (Percentual Inteiro, Texto Status)"""
        data = self.client.get_dados_instantaneos()
        if not data:
            return (0, "Offline")

        self._cache_dados = data
        return (int(data[7] * 100), data[8])

    def get_vl_mA(self):
        return self._cache_dados[6] if self._cache_dados else 0.0

    def get_vl_percentual(self):
        return int(self._cache_dados[7] * 100) if self._cache_dados else 0

    def get_local(self):
        return self.client._local

    def get_tempo_pin(self):
        data = self.client.get_dados_instantaneos()
        return data[5]

    def get_historico_dataframe(self, periodo="24h"):
        """
        Gera DataFrame corrigido e reamostrado.
        periodo: '24h', '7d', '30d'
        """
        # 1. Define quantas horas buscar na API baseado no período
        mapa_horas = {"24h": 24, "7d": 168, "30d": 720}  # 7 * 24  # 30 * 24
        horas_busca = mapa_horas.get(periodo, 24)

        # 2. Busca dados brutos (mA)
        raw = self.client.get_historico_raw(horas=horas_busca)

        if not raw:
            return pd.DataFrame(columns=["timestamp", "percentual", "mA"])

        df = pd.DataFrame(raw)

        # 3. Converter timestamp e Fuso
        df["timestamp"] = pd.to_datetime(df["ts"], unit="ms")
        df["timestamp"] = (
            df["timestamp"].dt.tz_localize("UTC").dt.tz_convert("America/Sao_Paulo")
        )

        # 4. Calcular Colunas (mA e Percentual)
        min_ma, max_ma = self.client._MINIMO, self.client._MAXIMO

        # Coluna mA (já vem como 'value')
        df["mA"] = df["value"]

        # Coluna Percentual
        df["percentual"] = df["value"].apply(
            lambda x: max(0, min(100, ((x - min_ma) / (max_ma - min_ma)) * 100))
        )

        # 5. Reamostragem (Resample) baseada no período solicitado
        df = df.set_index("timestamp")

        if periodo == "24h":
            # Minuto a minuto
            df_resampled = df.resample("1min").mean()
        elif periodo == "7d":
            # Hora a hora
            df_resampled = df.resample("1h").mean()
        elif periodo == "30d":
            # Dia a dia
            df_resampled = df.resample("1D").mean()
        else:
            df_resampled = df

        # Remove linhas vazias (geradas pelo resample se houver buracos) e reseta index
        return df_resampled.dropna().reset_index()
