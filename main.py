import os
from src.services.ReleClient import ReleClient
from src.controllers.Rele import Rele
from dotenv import load_dotenv


load_dotenv()


id_rele = os.getenv("RELE_IE")

rele = Rele(id_rele)

print(rele._status, rele._ultima_atividade)

# print(rele.acionar_rele('LIGAR'))
