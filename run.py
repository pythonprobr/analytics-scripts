from tasks.load_leads import run as load_leads_run
from tasks.load_transactions import run as load_transactions_run
from utils import log

if __name__ == "__main__":
    log.info("--> Iniciando processamento...")

    load_transactions_run()
    load_leads_run()

    log.info("--> Fim do processamento.")
