from datetime import datetime, timedelta

import pytz
from resources.pagarme import pagarme
from settings import TIME_ZONE
from utils import log


def _get_seven_days_ago():
    # return datetime(2019, 12, 1)
    return datetime.now() - timedelta(days=7)


def _get_pagarme_filters(page_count, since):
    return {
        "page": page_count,
        "count": 100,
        "date_created": f">={since:%Y-%m-%d}",
    }


def _get_transactions_from_pagarme(since):
    page_count = 0
    while True:
        page_count += 1
        transactions = pagarme.transaction.find_by(
            _get_pagarme_filters(page_count, since)
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


def _prepare_data_to_be_loaded(since=_get_seven_days_ago()):
    needed_keys = [
        "amount",
        "authorized_amount",
        "cost",
        "date_created",
        "date_updated",
        "boleto_expiration_date",
        "id",
        "ip",
        "nsu",
        "order_id",
        "paid_amount",
        "status",
        "subscription_id",
        "tid",
        "email",
        "payment_method",
        "items",
    ]

    transactions = []
    for transaction in _get_transactions_from_pagarme(since):
        row = {}
        for key, value in transaction.items():
            if key in needed_keys:
                row[key] = value

            row["email"] = transaction["customer"]["email"]
            row["name"] = transaction["customer"]["name"]
            row["phone_number"] = transaction["customer"]["phone_numbers"][0]

        if "@python.pro.br" in row["email"]:
            continue

        expiration = _str_to_datetime(row["boleto_expiration_date"])

        row["date_created"] = _prepare_datetime(row["date_created"])
        row["date_updated"] = _prepare_datetime(row["date_updated"])
        row["boleto_expiration_date"] = _prepare_datetime(row["boleto_expiration_date"])

        row["expired"] = 0
        if (
            expiration
            and expiration < datetime.now(tz=pytz.utc)
            and row["status"] != "paid"
        ):
            row["expired"] = 1

        row["offer"] = ""

        if row["items"]:
            if "pytools-oto-" in row["items"][0]["id"]:
                row["offer"] = "pytools-oto"

            elif "pytools-" in row["items"][0]["id"]:
                row["offer"] = "pytools"

            elif "membership-" in row["items"][0]["id"]:
                row["offer"] = "membership"

            row["user_id"] = ""
            if "pytools" in row["offer"]:
                id_ = row["items"][0]["id"].split("-")[-1]
                if not id_ == "None":
                    row["user_id"] = id_

        del row["items"]
        transactions.append(row)
    return transactions


def _get_transactions_worksheet():
    from resources.gsheets import spreadsheet

    return spreadsheet.worksheet_by_title("Transações")


def _get_gsheets_current_data():
    worksheet = _get_transactions_worksheet()
    return worksheet.get_all_values(include_tailing_empty_rows=False)


def _save_new_data_in_gsheets(data):
    worksheet = _get_transactions_worksheet()
    worksheet.update_values("A1", data)


def _generate_data_with_new_transactions(data_from_api, data_from_gsheets):
    data_to_gsheets = []

    # headers = list(data_from_api[0].keys())
    # data_to_gsheets.append(headers)

    data_from_api = {item["id"]: item for item in data_from_api}

    for row in data_from_gsheets:
        transaction_id = row[8]
        try:
            transaction_id = int(row[8])
        except ValueError:
            pass

        if transaction_id in data_from_api:
            row = list(data_from_api[transaction_id].values())
            del data_from_api[transaction_id]

        data_to_gsheets.append(row)

    for transaction_id in data_from_api:
        row = list(data_from_api[transaction_id].values())
        data_to_gsheets.append(row)

    return data_to_gsheets


def run(since=_get_seven_days_ago()):
    log.info("Iniciando carregamento de novas transações...")

    log.info("Recuperando transações da API do Pagarme...")
    leads_from_api = _prepare_data_to_be_loaded(since)

    log.info("Recuperando transações da planilha...")
    data_from_gsheets = _get_gsheets_current_data()

    log.info("Juntando transações...")
    new_data = _generate_data_with_new_transactions(leads_from_api, data_from_gsheets)

    log.info("Salvando novas transações na planilha...")
    _save_new_data_in_gsheets(new_data)

    log.info("Fim da tarefa.")


if __name__ == "__main__":
    run()
