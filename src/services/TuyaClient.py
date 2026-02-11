import requests
import os
from dotenv import load_dotenv
from tuya_connector import TuyaOpenAPI


class TuyaClient:
    def __init__(
        self, id_dispositivo, secret_dispositivo, device_id_dispositivo, endpoint
    ):

        self._id = id_dispositivo
        self._secret = secret_dispositivo
        self._device_id = device_id_dispositivo
        self._endpoint = endpoint
        self._conexao_api = self._criando_conexao()

    def _criando_conexao(self):
        openapi = TuyaOpenAPI(self._endpoint, self._id, self._secret)
        openapi.connect()

        return openapi

    def verificar_status(self):
        """
        Consulta a nuvem para saber se o relé está ligado ou desligado.
        Retorna: True (Ligado), False (Desligado) ou None (Erro)
        """

        try:
            response = self._conexao_api.get(f"/v1.0/devices/{self._device_id}/status")
            if response.get("success"):
                # A resposta vem como uma lista de status. Procuramos o 'switch_1'
                status_list = response["result"]
                for item in status_list:
                    if item["code"] == "switch_1":
                        estado = item["value"]
                        # Print para mostrar no terminal... depois excluir o que esta abaixo
                        texto = "LIGADA (ON)" if estado else "DESLIGADA (OFF)"
                        print(f"Status Atual da Bomba: {texto}")
                        return estado
            else:
                print("Erro ao verificar status:", response)
                return None
        except:
            return None

    # FUNÇÃO PARA LIGAR/DESLIGAR
    def acionar_rele(self, ligar=False):
        try:
            # true para LIGAR, false para DESLIGAR
            valor = True if ligar else False

            commands = {"commands": [{"code": "switch_1", "value": valor}]}

            # Envia comando para a nuvem
            resposta = self._conexao_api.post(
                f"/v1.0/devices/{self._device_id}/commands", commands
            )

            print(f"Comando enviado: {resposta}")
        except:
            pass
