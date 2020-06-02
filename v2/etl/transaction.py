from resources.pagarme import pagarme

import sqlalchemy as db

from tasks.load_visits import _fetch_query_string
from utils import log
from v2.etl import ETL
from v2.models import Transaction, Session


class ETLTransaction(ETL):
    def extract(self):
        from resources.database import connection

        log.info("Lead| Carregando registros do sistema...")

        statement = db.sql.text(
            """
            SELECT 
                *
            FROM django_pagarme_pagarmepayment p
            JOIN django_pagarme_pagarmenotification n ON p.id = n.payment_id
            JOIN django_pagarme_pagarmepaymentitem pi ON pi.payment_id = n.payment_id
            JOIN django_pagarme_pagarmeitemconfig i ON i.id = pi.item_id
            WHERE
                status = 'paid'
                AND creation >= :created
            ;
            """
        )

        self.data = connection.execute(statement, created=self.date_limit)

    def transform(self):
        rows = []
        for item in self.data:
            row = {
                "tid": item["transaction_id"],
                "created": item["creation"],
                "paid_amount": item["amount"] / 100,
                "cost": 0,
                "final_amount": item["amount"] / 100,
                "is_boleto": item["payment_method"] == "boleto",
                "offer": item["slug"],
                "user_id": item["user_id"],
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
