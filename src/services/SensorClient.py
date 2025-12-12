import os
import time
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta


class SensorClient:

    def __init__(self, usuario="Usuario", local="Lavadeira"):

        # Carregando as informações do arquivo .env
        load_dotenv()

        self._base_url = os.getenv("BASE_URL")
        self.__TOKEN__ = None
        self._MINIMO = 4.0
        self._MAXIMO = 6.8

        # Informações AINDA estática para usuario e local
        self._usuario = usuario
        self._local = local

    ## >>>>> API para pegar o token JWT <<<<< ##
    def renovar_token(self):
        payload = {"username": os.getenv("USUARIO"), "password": os.getenv("PASSWORD")}

        url_api_token = f"{self._base_url}/api/auth/login"

        try:
            # aguardando a resposta por 10 segundos, depois desiste
            response = requests.post(url_api_token, json=payload, timeout=10)

            # Resposta positiva para o tokene configurar o token
            if response.status_code == 200:
                dados = response.json()
                token = dados["token"]
                self.__TOKEN__ = f"Bearer {token}"

            else:
                raise Exception("FalhaAoAcessarAPI")
        except Exception as e:
            raise Exception("ErroNoToken")

    ## >>>>> API para soltar os valores de sensores a respeito da sonda mA (mili Amperes) <<<<< ##
    # TODO: Ao inves de retornar o 401 no log, poderia informar ao sensor o valor 0 na medicao e na situacao que esta com problema
    # Ja esta implementado a situacao, basta dizer o valor zero para a medicao, retornar um json vazio
    def consultar_api(self):
        url_api_dados_sensor = f"{self._base_url}/api/plugins/telemetry/DEVICE/{os.getenv('SENSOR_LAVADEIRA')}/values/timeseries"

        headers = {"Authorization": self.__TOKEN__}
        params = {"useStrictDataTypes": "false"}

        try:
            # Acessar a API do tipo GET
            # timeout(5, 10)
            # 5     --> Tempo máximo para estabelecer a conexão
            # 10    --> Tempo máximo para receber a resposta
            response = requests.get(
                url_api_dados_sensor, headers=headers, params=params, timeout=(5, 10)
            )

            # Cenário: Token Vencido: error 401
            if response.status_code == 401:
                self.renovar_token()

                # Tenta novamente o novo token (recursividade)
                headers = {"Authorization": self.__TOKEN__}
                params = {"useStrictDataTypes": "false"}

            # Tentar novamente a conexao com token renovado
            response = requests.get(
                url_api_dados_sensor, headers=headers, params=params, timeout=(5, 10)
            )

            # Caso dê erro depois de tentar renovar, levanta a exceção do erro
            response.raise_for_status()

            return response.json()

        except requests.exceptions.Timeout:
            raise Exception("TimeoutConexao")

        except requests.exceptions.ConnectionError:
            raise Exception("ErroConexao")

        except Exception as e:
            raise e

    ## >>>>> Método para converter o numero de timestamp em datetime em formato string e no tipo datetime <<<<< ##
    def convert_timestamp_date(self, timestamp):
        if timestamp is None:
            return None, None

        timestamp_ms = float(timestamp)  # Garante que é numero
        timestamp_s = timestamp_ms / 1000

        # Objeto datetime (para uso no cálculo de tempo)
        data_hora_obj = datetime.fromtimestamp(timestamp_s)

        # String formatada (para salvar no banco/csv)
        data_formatada_str = data_hora_obj.strftime("%d/%m/%Y %H:%M:%S")

        # Retorna os dois valores como uma tupla
        return data_hora_obj, data_formatada_str

    ## >>>>> Populando a lista ou os pins que são retornados do sensor <<<<< ##
    # TODO: Aqui precisa futuramente quando tiver o sistema de login e mais sensores trocar e passar as informações aqui
    # é preciso passar lá no construtor o usuario, local
    def create_pin_sensor(self):
        try:
            dados_json = self.consultar_api()

            # Validação do sensor sem dados
            if "ia" not in dados_json or len(dados_json["ia"]) == 0:
                no_situacao = "Com Problema"

            valor_mA = float(dados_json["ia"][0]["value"])
            valor_timestamp = int(dados_json["ia"][0]["ts"])

            # Caso o valor de mA esteja abaixo de 4, não necessariamente 0, tambem é um erro
            no_situacao = "Normal" if valor_mA > 4.0 else "Com Problema"

            # esta variavel é para ligar com a dim_tempo, sera no formato 20250113 (aqui a data seria 13/01/2025)
            co_tempo = datetime.now().strftime("%Y%m%d")
            dt_requisicao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

            # O sensor retorna o tempo dele em timestamp por isso usamos o modulo acima
            dt_pin_obj, dt_pin_str = self.convert_timestamp_date(valor_timestamp)

            # Valor de medicao em mA (é o valor padrão que vem no SENSOR)
            vl_medicao = valor_mA

            # O sensor ele vai de 4 até 20 mA, acontece que esta sonda esta no local errado (ele vai de 4 até 6.8 mA, nao chega até 20mA)
            # mas tambem gera confusão esse range de 4 até 6.8 mA, logo, pediu-se que trabalhe em porcentagem sendo 4 mA como 0% e
            # 6.8 mA é de 100%.. embora tenha registros de 6.9 mA, vamos capturar este caso depois para tentar verificar e alterar no
            # construtor os valores considerados máximo e minimo.. abaixo segue o calculo
            # (Valor Atual Sensor - Valor Mínimo) / (Valor Máximo - Valor Mínimo)
            vl_percentual = round(
                (valor_mA - self._MINIMO) / (self._MAXIMO - self._MINIMO), 4
            )

            # Retornando a lista de pins para inserir depois em um buffer
            lista_pin = [
                self._usuario,
                no_situacao,
                self._local,
                co_tempo,
                dt_requisicao,
                dt_pin_str,
                vl_medicao,
                vl_percentual,
            ]

            return lista_pin

        except Exception as e:
            raise e
