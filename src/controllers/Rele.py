import pandas as pd
from src.services.ReleClient import ReleClient


class Rele:
    def __init__(self, id_rele):
        self._rele = ReleClient(id_rele)
        self._status = self._rele._status
        self._ultima_atividade = self._rele._ultima_atividade

    def get_status_bomba(self):
        return self._status == 1

    def LIGAR_BOMBA(self):
        self._rele.acionar_rele("LIGAR")
        pass

    def DESLIGAR_BOMBA(self):
        self._rele.acionar_rele("DESLIGAR")
        pass
