from tasks.load_leads import run as load_leads_run
from tasks.load_transactions import run as load_transactions_run
from tasks.load_leads_activations import run as load_leads_activations_run
from tasks.load_visits import run as load_visits_run
from tasks.send_new_orders_to_telegram import run as send_new_orders_to_telegram_run
from utils import log

if __name__ == "__main__":
    log.info("--> Iniciando processamento...")

    send_new_orders_to_telegram_run()
    load_visits_run()
    load_leads_run()
    load_leads_activations_run()
    load_transactions_run()

    log.info("--> Fim do processamento.")
