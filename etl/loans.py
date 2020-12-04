from datetime import datetime, timedelta

from flatten_dict import flatten
from resources.gsheets import spreadsheet
from resources.pagarme import pagarme
import requests

from resources.provi import get_transactions
from utils import log


class Loans:
    def __init__(self, *args, **kwargs):
        self.headers = []
        self.transactions_raw = []
        self.transactions_prepared = []
        self.transactions_from_sheet = []
        self.transactions_to_sheet = []

    def run(self):
        log.info("Iniciando carregamento de novos parcelamentos...")

        self.get_transactions_from_pagarme()
        self.prepare_data_to_be_loaded()
        self.get_gsheets_current_data()
        self.generate_data_with_new_transactions()
        self.save_new_data_in_gsheets()

        log.info("Fim da tarefa.")

    def get_transactions_from_pagarme(self):
        log.info("Recuperando transações da API da Provi...")

        for item in get_transactions():
            self.transactions_raw.append(item)

    def prepare_data_to_be_loaded(self):
        log.info("Tratando informações recuperadas...")

        for transaction in self.transactions_raw:
            if "courses" in transaction and transaction["courses"]:
                transaction["item"] = transaction["courses"][0]
                del transaction["courses"]

            transaction = flatten(
                transaction,
                reducer="path",
            )

            for key, value in transaction.items():
                if key not in self.headers:
                    self.headers.append(key)

            transaction_ordered = {}
            for header in self.headers:
                if header in transaction:
                    transaction_ordered[header] = transaction[header]
                else:
                    transaction_ordered[header] = None

            for key, value in transaction_ordered.items():
                if type(value) in (list, dict):
                    transaction_ordered[key] = str(value)

            self.transactions_prepared.append(transaction_ordered)

    def _get_transactions_worksheet(self):
        return spreadsheet.worksheet_by_title("DB | Provi | Transações")

    def get_gsheets_current_data(self):
        log.info("Baixando informações atuais da planilha...")

        worksheet = self._get_transactions_worksheet()
        for line in worksheet.get_all_values(include_tailing_empty_rows=False):
            self.transactions_from_sheet.append(line)

    def generate_data_with_new_transactions(self):
        log.info("Juntando transações...")
        # self.transactions_to_sheet.append(self.headers)

        data_from_api = {item["id"]: item for item in self.transactions_prepared}

        count_existing = 0
        for row in self.transactions_from_sheet:
            transaction_id = row[0]
            try:
                transaction_id = int(transaction_id)
            except ValueError:
                pass

            if transaction_id in data_from_api:
                row = list(data_from_api[transaction_id].values())
                del data_from_api[transaction_id]
                count_existing += 1

            self.transactions_to_sheet.append(row)

        count_new = 0
        for transaction_id in data_from_api:
            row = list(data_from_api[transaction_id].values())
            self.transactions_to_sheet.append(row)
            count_new += 1

        log.info(f"{count_existing} linhas atualizadas.")
        log.info(f"{count_new} linhas adicionadas.")

    def save_new_data_in_gsheets(self):
        log.info("Salvando novas transações na planilha...")

        worksheet = self._get_transactions_worksheet()
        worksheet.update_values("A1", self.transactions_to_sheet)
