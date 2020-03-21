from resources.pagarme import pagarme

import sqlalchemy as db

from tasks.load_visits import _fetch_query_string
from utils import log
from v2.etl import ETL
from v2.models import Transaction, Session


class ETLTransaction(ETL):
    def _get_pagarme_filters(self, page_count):
        return {
            "page": page_count,
            "count": 100,
            "date_created": f">={self.date_limit:%Y-%m-%d}",
        }

    def _get_transactions_from_pagarme(self):
        page_count = 0
        while True:
            page_count += 1
            transactions = pagarme.transaction.find_by(
                self._get_pagarme_filters(page_count)
            )
            if not transactions:
                break

            for item in transactions:
                yield item

    def extract(self):
        log.info(f"Transaction| Carregando transações da API...")
        self.data = [item for item in self._get_transactions_from_pagarme()]

    def transform(self):
        rows = []
        for item in self.data:
            offer = None
            user_id = None
            if item["items"]:
                if "pytools-oto-" in item["items"][0]["id"]:
                    offer = "pytools-oto"

                elif "pytools-" in item["items"][0]["id"]:
                    offer = "pytools"

                elif "membership-" in item["items"][0]["id"]:
                    offer = "membership"

                if offer is not None and "pytools" in offer:
                    id_ = item["items"][0]["id"].split("-")[-1]
                    if not id_ == "None":
                        user_id = id_

            row = {
                "tid": item["tid"],
                "created": item["date_created"],
                "paid_amount": item["paid_amount"] / 100,
                "cost": item["cost"] / 100,
                "final_amount": (item["paid_amount"] / 100) - (item["cost"] / 100),
                "is_boleto": item["payment_method"] == "boleto",
                "offer": offer,
                "user_id": user_id,
            }

            rows.append(row)
        self.data = rows

    def load(self):
        from v2.database import session

        loaded_ids = [item["tid"] for item in self.data]
        log.info(f"Transaction| Removendo {len(loaded_ids)} registros existentes...")
        session.execute(
            Transaction.__table__.delete().where(Transaction.tid.in_(loaded_ids))
        )

        items_to_add = [Transaction(**item) for item in self.data]
        log.info(
            f"Transaction| Inserindo {len(items_to_add)} novos registros no analytics..."
        )
        session.bulk_save_objects(items_to_add)
        session.commit()
