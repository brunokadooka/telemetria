import requests
import os
from dotenv import load_dotenv
import streamlit as st


class ReleClient:
    def __init__(self, id_rele, pin=7):
        load_dotenv()
        self._base_url = os.getenv("BASE_URL")
        self._id_rele = id_rele
        self._pin = pin
        self.__TOKEN__ = self._renovar_token_()
        self._status, self._ultima_atividade = self.get_status_rele()

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

    ## --> Retornando um objeto JSON para API ligar/desligar o rele <-- ##
    def _enviar_comando_ligar_desligar(self, command):

        # qualquer valor errado desligamos o relé, evitar erros maiores
        if command == "LIGAR":
            value = 1
        else:
            value = 0

        # Criando o dicionario (json) que será enviado pela API
        dict_rele = {
            "method": "setGpio",
            "params": {"pin": self._pin, "value": value},
            "timeout": 30000,
        }

        return dict_rele

    ## --> Função para verificar o status do rele <-- ##
    # @st.cache_data(ttl=30, show_spinner=False) --> ativar depois
    def get_status_rele(self):
        url = f"https://monitorie.com.br:443/api/plugins/telemetry/DEVICE/{self._id_rele}/values/timeseries?keys=rele"
        headers = {"Authorization": self.__TOKEN__}

        try:
            response = requests.get(url, headers=headers, timeout=5)

            if response.status_code == 401:
                self._renovar_token_()
                headers["Authorization"] = self.__TOKEN__
                response = requests.get(url, headers=headers, timeout=5)

            dados_api = response.json()

            # Inicializa com padrão caso não encontre
            rele_atual = 0
            ultima_atividade_tmp = 0

            # 1. Verifica se a chave "rele" existe
            if "rele" in dados_api and len(dados_api["rele"]) > 0:
                item_mais_recente = dados_api["rele"][0]
                rele_atual = int(item_mais_recente["value"])
                ultima_atividade_tmp = item_mais_recente["ts"]

            return rele_atual, ultima_atividade_tmp

        except Exception as e:
            print(f"Erro ao buscar status: {e}")
            # Em caso de erro (ex: sem internet), retorna 0, 0 para não travar
            return 0, 0

    ## --> Usando Atributos Compartilhados (SHARED_SCOPE) <-- ##
    def acionar_rele(self, comando):
        # 1. Define o valor baseado no comando
        if comando == "LIGAR":
            valor = 1
        else:
            valor = 0

        # 2. Monta o JSON simples (Baseado no Content-Length: 10 da sua imagem)
        payload = {"rele": valor}

        # 3. A URL correta descoberta no F12 (SHARED_SCOPE)
        # Atenção: /api/plugins/telemetry/DEVICE/{id}/SHARED_SCOPE
        url = f"{self._base_url}/api/plugins/telemetry/DEVICE/{self._id_rele}/SHARED_SCOPE"

        headers = {"Content-Type": "application/json", "Authorization": self.__TOKEN__}

        try:
            # 4. Envia o POST
            print(f"Enviando para: {url}")
            print(f"Payload: {payload}")

            response = requests.post(url, json=payload, headers=headers, timeout=10)

            # Lógica de renovação de token
            if response.status_code == 401:
                self._renovar_token_()
                headers["Authorization"] = self.__TOKEN__
                response = requests.post(url, json=payload, headers=headers, timeout=10)

            # 5. Verifica o resultado
            if response.status_code == 200:
                self._status = valor
                return True, f"Comando '{comando}' enviado! (Atributo atualizado)"
            else:
                return False, f"Erro na API: {response.status_code} - {response.text}"

        except Exception as e:
            return False, f"Erro de conexão: {str(e)}"
