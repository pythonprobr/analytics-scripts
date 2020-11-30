from datetime import datetime, timedelta

from activecampaign.client import Client

from flatten_dict import flatten
from resources.gsheets import spreadsheet
from resources.active_campaign import client
from utils import log


class Leads:
    def __init__(self, *args, **kwargs):
        self.leads_tags = ["tpp-webiorico"]
        self.emails = {}
        self.tags = {}

        self.headers = []
        self.leads_raw = []
        self.leads_prepared = []
        self.leads_from_sheet = []
        self.leads_to_sheet = []

    def run(self):
        log.info("Iniciando carregamento de novas transações...")

        self.get_leads()
        self.get_leads_tags()
        self.prepare_data_to_be_loaded()
        self.get_gsheets_current_data()
        self.generate_data_with_new_items()
        self.save_new_data_in_gsheets()

        log.info("Fim da tarefa.")

    def _get_days_ago(self):
        # return datetime(2020, 10, 1)
        return datetime.now() - timedelta(hours=4)

    def _get_tags_ids(self):
        log.info("Buscando ID das tags...")

        tags_ids = []
        for tag in self.leads_tags:
            response = client._get(f"/tags/?search={tag}")
            for item in response["tags"]:
                if item["tag"] == tag:
                    tags_ids.append(item["id"])

        return tags_ids

    def _get_tag_name(self, tag_id):
        return client._get(f"/tags/{tag_id}")

    def get_leads(self):
        log.info("Buscando leads...")

        limit = 100
        for tag in self._get_tags_ids():
            offset = 0
            count = 0

            log.info(f"Buscando leads da tag {tag}...")
            while True:

                params = {
                    "tagid": tag,
                    "filters[updated_after]": self._get_days_ago(),
                    "offset": offset,
                    "limit": limit,
                }

                response = client.contacts.list_all_contacts(**params)

                total = int(response["meta"]["total"])
                if count == 0:
                    log.info(f"Total de leads: {total}...")

                for contact in response["contacts"]:
                    contact_id = contact["id"]
                    email = contact["email"]

                    self.emails[email] = contact
                    self.emails[email]["tags"] = {}

                    response_tags = client._get(
                        f"/contacts/{contact_id}/contactTags",
                        params={
                            "offset": offset,
                            "limit": limit,
                        },
                    )

                    for item in response_tags["contactTags"]:
                        tag_id = item["tag"]
                        self.emails[email]["tags"][tag_id] = item

                    count += 1
                    # break

                log.debug(f"Baixados {count}/{total} leads...")

                offset += limit
                if total <= offset:
                    break

    def get_leads_tags(self):
        log.info("Buscando tags dos leads...")

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

        for email in self.emails:
            data = self.emails[email]
            cdate = data["created_timestamp"]
            now = datetime.now().strftime("%Y-%m-%d")
            utm_tags = [self.tags[tag]["tag"] for tag in data["tags"]]

            utms = {}
            for item in [
                "utm_source",
                "utm_medium",
                "utm_campaign",
                "utm_term",
                "utm_content",
            ]:
                utms[item] = None
                for tag in utm_tags:
                    if item in tag:
                        utms[item] = tag.replace(f"{item}=", "").strip()

            row = [
                email,
                cdate,
                now,
            ]
            row += list(utms.values())
            self.leads_prepared.append(row)

    def _get_transactions_worksheet(self):
        return spreadsheet.worksheet_by_title("DB | AC | Leads")

    def get_gsheets_current_data(self):
        log.info("Baixando informações atuais da planilha...")

        worksheet = self._get_transactions_worksheet()
        for line in worksheet.get_all_values(include_tailing_empty_rows=False):
            self.leads_from_sheet.append(line)

    def generate_data_with_new_items(self):
        log.info("Juntando leads...")

        data_from_api = {item[0]: item for item in self.leads_prepared}

        count_existing = 0
        for row in self.leads_from_sheet:
            email = row[0]
            if email in data_from_api:
                del data_from_api[email]
                count_existing += 1

        count_new = 0
        for email in data_from_api:
            row = data_from_api[email]
            self.leads_to_sheet.append(row)
            count_new += 1

        log.info(f"{count_existing} linhas existentes.")
        log.info(f"{count_new} linhas adicionadas.")

    def save_new_data_in_gsheets(self):
        log.info("Salvando novas transações na planilha...")

        worksheet = self._get_transactions_worksheet()
        if self.leads_to_sheet:
            worksheet.update_values("A2", self.leads_to_sheet)
