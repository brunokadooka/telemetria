import os
from src.controllers.Rele import ReleTuya
from dotenv import load_dotenv

load_dotenv()

rele_on = os.getenv("RELE_LAV_8P_ON_DEVICE_ID")
rele_off = os.getenv("RELE_LAV_8P_OFF_DEVICE_ID")


# print("----------- Testando botao de desligar -----------")
# rele_tuya = ReleTuya(rele_off)
# rele_tuya.criando_pulso(0.1, False)

# print("----------- Testando botao de ligar -----------")
# rele_tuya = ReleTuya(rele_on)
# rele_tuya.criando_pulso(0.1, True)


rele = ReleTuya(rele_on)

print(rele.acionando_rele(True))
