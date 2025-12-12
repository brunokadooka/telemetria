import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

# >>>> Configurações do Log <<<<

# Caminho do log (caminho universal)
BASE_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

# formato do log: Tempo - Tipo Log - Mensagem
log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")


file_handler = RotatingFileHandler(
    LOG_FILE,
    mode="a",
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=10,
    encoding="utf-8",
)
file_handler.setFormatter(log_formatter)

# Criando um logger específico para não conflitar com bibliotecas externas
logger = logging.getLogger("SaneamentoLogger")
logger.setLevel(logging.INFO)  # Define que INFO pra cima é importante

# Verifica se já tem handlers para não duplicar logs (importante no VS Code/Jupyter)
if not logger.hasHandlers():
    logger.addHandler(file_handler)
