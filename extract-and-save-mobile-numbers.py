import os
import sys
import zipfile
from datetime import datetime, timedelta
from glob import glob

from activecampaign.client import Client

from flatten_dict import flatten
from resources.gsheets import spreadsheet
from resources.active_campaign import client
from utils import log
from settings import TIME_ZONE

GLOB_STRING = "*RUMO*.zip"


class Numbers:
    def __init__(self, *args, **kwargs):
        self.numbers = []
        self.numbers_prepared = []
        self.numbers_from_sheet = []
        self.numbers_to_sheet = []

    def run(self):
        log.info("Iniciando carregamento de novas transações...")

        self.get_numbers()
        if self.numbers:
            self.prepare_data_to_be_loaded()
            self.get_gsheets_current_data()
            self.generate_data_with_new_items()
            self.save_new_data_in_gsheets()

        log.info("Fim da tarefa.")

    def get_numbers(self):
        log.info("Buscando numbers...")

        directory = sys.argv[1]
        word_identifier = "joined"
        count = 0
        for file in glob(os.path.join(directory, GLOB_STRING)):
            log.info(f"Extraindo números do arquivo {file}...")

            with zipfile.ZipFile(file) as archive:
                with archive.open("_chat.txt") as handle:
                    for line in handle.read().decode().split("\n"):
                        if word_identifier in line:
                            line = line.strip()
                            number = line.split("+")[-1]
                            number = "+{}".format(
                                number.split(word_identifier)[0].strip()
                            )
                            # number = number.replace("+55", "")
                            # number = number.replace("+", "")
                            # number = number.replace("‑", "")
                            number = number.strip()

                            if number not in self.numbers:
                                count += 1
                                self.numbers.append(number)

        log.info(f"{count} números extraidos.")

    def get_numbers_tags(self):
        log.info("Buscando tags dos numbers...")

        tags_ids = []
        for email in self.emails:
            for tag_id in self.emails[email]["tags"]:
                if tag_id not in tags_ids:
                    tags_ids.append(tag_id)

        log.info(f"Buscando {len(tags_ids)} nomes de tags...")
        for tag_id in tags_ids:
            response_tag = self._get_tag_name(tag_id)
            self.tags[tag_id] = response_tag["tag"]

    def prepare_data_to_be_loaded(self):
        log.info("Tratando informações recuperadas...")

        origin = sys.argv[2]

        for number in self.numbers:
            now = datetime.now().astimezone(TIME_ZONE).strftime("%Y-%m-%d")
            row = [f"'{number}", now, origin]
            self.numbers_prepared.append(row)

    def _get_transactions_worksheet(self):
        return spreadsheet.worksheet_by_title("DB | WPP | Números")

    def get_gsheets_current_data(self):
        log.info("Baixando informações atuais da planilha...")

        worksheet = self._get_transactions_worksheet()
        for line in worksheet.get_all_values(include_tailing_empty_rows=False):
            self.numbers_from_sheet.append(line)

    def generate_data_with_new_items(self):
        log.info("Juntando números...")

        data_from_api = {item[0]: item for item in self.numbers_prepared}

        count_existing = 0
        for row in self.numbers_from_sheet:
            number = "'{}".format(row[0])
            if number in data_from_api:
                row = data_from_api[number]
                del data_from_api[number]
                count_existing += 1

            self.numbers_to_sheet.append(row)

        count_new = 0
        for number in data_from_api:
            row = data_from_api[number]
            self.numbers_to_sheet.append(row)
            count_new += 1

        log.info(f"{count_existing} linhas existentes.")
        log.info(f"{count_new} linhas adicionadas.")

    def save_new_data_in_gsheets(self):
        log.info("Salvando novas transações na planilha...")

        worksheet = self._get_transactions_worksheet()
        if self.numbers_to_sheet:
            worksheet.update_values("A1", self.numbers_to_sheet)


if __name__ == "__main__":
    Numbers().run()