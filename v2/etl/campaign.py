import sys
from glob import glob
import csv

import sqlalchemy as db

from tasks.load_visits import _fetch_query_string
from utils import log
from v2.etl import ETL
from v2.models import CampaignPerformance


class ETLCampaign(ETL):
    FACEBOOK_ID = 2
    GOOGLE_ID = 1
    facebook_data = []
    google_data = []

    def extract_facebook_report_csv(self, file):
        count = 0
        with open(file) as handle:
            for row in csv.reader(handle, delimiter=",", quotechar='"'):
                count += 1
                if count > 1:
                    self.facebook_data.append(row)

        log.info(
            f"CampaignPerformance| {len(self.facebook_data)} registros carregados..."
        )

    def extract_google_report_csv(self, file):
        count = 0
        with open(file) as handle:
            for row in csv.reader(handle, delimiter=",", quotechar='"'):
                count += 1
                if count > 3:
                    self.google_data.append(row)

        log.info(
            f"CampaignPerformance| {len(self.google_data)} registros carregados..."
        )

    def extract(self):
        for item in sys.argv:
            if "--facebook-ads-report=" in item:
                log.info(
                    f"CampaignPerformance| Carregando relatório do Facebook Ads..."
                )
                files = item.replace("--facebook-ads-report=", "")
                for file in glob(files):
                    log.info(f"CampaignPerformance| Carregando arquivo {file}...")
                    self.extract_facebook_report_csv(file)

            if "--google-ads-report=" in item:
                log.info(f"CampaignPerformance| Carregando relatório do Google Ads...")
                files = item.replace("--google-ads-report=", "")
                for file in glob(files):
                    log.info(f"CampaignPerformance| Carregando arquivo {file}...")
                    self.extract_google_report_csv(file)

    def transform_facebook(self):
        rows = []
        for campaign_name, created, campaign_id, cost, _, _ in self.facebook_data:
            types = {
                1: "LEADS",
                2: "RMKT",
                3: "DIST",
            }
            type_id = None
            for type_id, substring in types.items():
                if substring in campaign_name:
                    break

            row = {
                "campaign_id": campaign_id,
                "name": campaign_name,
                "created": created,
                "cost": cost,
                "type_id": type_id,
                "source_id": self.FACEBOOK_ID,
            }

            rows.append(row)
        self.facebook_data = rows

    def transform_google(self):
        rows = []
        for campaign_id, campaign_name, created, _, cost in self.google_data:
            types = {
                1: "LEADS",
                2: "RMKT",
                3: "DIST",
            }
            type_id = None
            for type_id, substring in types.items():
                if substring in campaign_name:
                    break

            row = {
                "campaign_id": campaign_id,
                "name": campaign_name,
                "created": created,
                "cost": cost,
                "type_id": type_id,
                "source_id": self.GOOGLE_ID,
            }

            rows.append(row)
        self.google_data = rows

    def transform(self):
        self.transform_facebook()
        self.transform_google()

    def load_facebook(self):
        from v2.database import session

        loaded_ids = [item["campaign_id"] for item in self.facebook_data]
        log.info(
            f"CampaignPerformance| Removendo {len(loaded_ids)} registros existentes do Facebook..."
        )
        session.execute(
            CampaignPerformance.__table__.delete().where(
                db.and_(
                    CampaignPerformance.campaign_id.in_(loaded_ids),
                    CampaignPerformance.source_id == self.FACEBOOK_ID,
                )
            )
        )

        items_to_add = [CampaignPerformance(**item) for item in self.facebook_data]
        log.info(
            f"CampaignPerformance| Inserindo {len(items_to_add)} novos registros do Facebook no analytics..."
        )
        session.bulk_save_objects(items_to_add)
        session.commit()

    def load_google(self):
        from v2.database import session

        loaded_ids = [item["campaign_id"] for item in self.google_data]
        log.info(
            f"CampaignPerformance| Removendo {len(loaded_ids)} registros existentes do Google Ads..."
        )
        session.execute(
            CampaignPerformance.__table__.delete().where(
                db.and_(
                    CampaignPerformance.campaign_id.in_(loaded_ids),
                    CampaignPerformance.source_id == self.GOOGLE_ID,
                )
            )
        )

        items_to_add = [CampaignPerformance(**item) for item in self.google_data]
        log.info(
            f"CampaignPerformance| Inserindo {len(items_to_add)} novos registros do Google Ads no analytics..."
        )
        session.bulk_save_objects(items_to_add)
        session.commit()

    def load(self):
        self.load_facebook()
        self.load_google()
