import pandas as pd
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
