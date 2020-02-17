from datetime import datetime, timedelta
from time import sleep

import telegram
from resources.pagarme import pagarme

from settings import TIME_ZONE, TELEGRAM_BOT_TOKEN
from utils import log

TELEGRAM_GROUP_CHAT_ID = -355393771


def _get_date_delta():
    # return datetime(2020, 2, 16)
    return datetime.now() - timedelta(minutes=5)


def _get_pagarme_filters(page_count, since):
    return {
        "page": page_count,
        "count": 100,
        "date_created": f">={since:%Y-%m-%dT%H:%M}",
        "sort": [{"date_created": {"order": "asc"}}],
    }


def _get_transactions_from_pagarme():
    page_count = 0
    while True:
        page_count += 1
        transactions = pagarme.transaction.find_by(
            _get_pagarme_filters(page_count, _get_date_delta())
        )
        if not transactions:
            break

        for item in transactions:
            yield item


def _str_to_datetime(creation):
    if not creation:
        return

    date = creation.split("T")[0]
    time = creation.split("T")[1].split(".")[0]
    creation = f"{date} {time} +0000"
    return datetime.strptime(creation, "%Y-%m-%d %H:%M:%S %z")


def _prepare_datetime(creation):
    creation = _str_to_datetime(creation)
    if not creation:
        return

    return creation.astimezone(TIME_ZONE).strftime("%Y-%m-%d %H:%M:%S")


def _send_messages(transactions):
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

    for transaction in transactions:
        if (
            not transaction["items"]
            or "pytools" not in transaction["items"][0]["id"].lower()
            or transaction["status"] not in ("authorized", "paid", "waiting_payment")
        ):
            continue

        msg = "<b>🚀 Venda Realizada!</b>\n\n"

        created = _prepare_datetime(transaction["date_created"])
        msg += f"🕖 <b>Data</b>: {created}\n"

        client = transaction["customer"]["name"].title()
        msg += f"👤 <b>Nome</b>: {client}\n"

        if transaction["billing"]["address"]:
            city = transaction["billing"]["address"]["city"]
            state = transaction["billing"]["address"]["state"]
            location = f"{city} - {state}"
            msg += f"📍 <b>Localização</b>: {location}\n"

        amount = transaction["authorized_amount"] / 100
        amount = f"{amount:.2f}".replace(".", ",")
        msg += f"💰 <b>Valor</b>: R$ {amount}\n"

        msg += f"💳 <b>Forma de Pagamento</b>: {transaction['payment_method']}"

        bot.send_message(chat_id=TELEGRAM_GROUP_CHAT_ID, text=msg, parse_mode="html")


def run():
    log.info("Iniciando carregamento de novas ativações...")

    log.info("Recuperando transações do pagarme...")
    transactions = _get_transactions_from_pagarme()

    log.info("Enviando transações para o Telegram...")
    _send_messages(transactions)

    log.info("Fim da tarefa.")
