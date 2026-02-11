import os
import pandas as pd

from dotenv import load_dotenv
from time import sleep
from src.services.TuyaClient import TuyaClient
from src.services.ReleClient import ReleClient

class Rele:
    def __init__(self, id_rele):
        # Salvamos o ID para usar depois
        self.id_rele = id_rele
        
        # Mantemos uma instância inicial (opcional, mas bom pra cache se precisar)
        self._rele = ReleClient(id_rele)

    def get_status_bomba(self):
        # Criamos um cliente novo momentâneo para pegar o dado fresco do banco/API.
        new_cliente = ReleClient(self.id_rele)
        
        # Retorna o status que acabou de ser lido
        return new_cliente._status == 1

    def LIGAR_BOMBA(self):
        # Aqui podemos usar o self._rele mesmo, pois é só comando de envio
        self._rele.acionar_rele("LIGAR")
        pass

    def DESLIGAR_BOMBA(self):
        self._rele.acionar_rele("DESLIGAR")
        pass


class ReleTuya:
    def __init__(self, id_dispositivo):
        load_dotenv()
        self._rele_tuya = TuyaClient(
            id_dispositivo=os.getenv("RELE_LAV_8P_ID"),
            secret_dispositivo=os.getenv("RELE_LAV_8P_SECRET"),
            device_id_dispositivo=id_dispositivo,
            endpoint=os.getenv("API_ENDPOINT"),
        )

    def criando_pulso(self, time_pulso, ligar):

        valor = True if ligar else False

        self._rele_tuya.acionar_rele(valor)

        sleep(time_pulso / 2)

        self._rele_tuya.verificar_status()

        sleep(time_pulso / 2)

        self._rele_tuya.acionar_rele((not valor))
