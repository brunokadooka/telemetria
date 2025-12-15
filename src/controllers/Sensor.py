from pathlib import Path
from src.services.SensorClient import SensorClient


class Sensor:
    def __init__(self):
        # Instancia o cliente
        sensor_client = SensorClient()

        # Chama o método que agora é CACHEADO (Rápido!)
        # Se você der F5 ou clicar num botão em menos de 30s, ele pega da memória RAM
        self.__pin_info__ = sensor_client.create_pin_sensor()

    def get_pin_info(self):
        return self.__pin_info__

    def get_vl_percentual(self):
        data = self.get_pin_info()
        # Tratamento de erro caso venha None
        try:
            return int(data[7] * 100)
        except:
            return 0

    def get_local(self):
        data = self.get_pin_info()
        return f"Caixa da {data[2]}"

    def get_status_reservatorio(self):
        data = self.get_pin_info()
        return data[8]  # Retorna "Enchendo", "Esvaziando", etc.

    def get_vl_mA(self):
        data = self.get_pin_info()
        return data[6]

    def get_tempo_pin(self):
        data = self.get_pin_info()
        return data[5]
