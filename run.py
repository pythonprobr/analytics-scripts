from tasks.load_leads import run as load_leads_run
from utils import log

if __name__ == "__main__":
    log.info("--> Iniciando processamento...")

    load_leads_run()

    log.info("--> Fim do processamento.")
