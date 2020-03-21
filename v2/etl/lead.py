import sqlalchemy as db

from utils import log
from v2.etl import ETL
from v2.models import Lead, User


class ETLLead(ETL):
    def extract(self):
        from resources.database import connection

        log.info("Lead| Carregando registros do sistema...")

        statement = db.sql.text(
            """
            SELECT
                id as user_id
                , date_joined as created
            FROM core_user
            WHERE 
                date_joined >= :created
            ORDER BY 
                id DESC
            """
        )

        self.data = connection.execute(statement, created=self.date_limit)

    def transform(self):
        self.data = [item for item in self.data]

    def load(self):
        from v2.database import session

        loaded_user_ids = [item["user_id"] for item in self.data]
        qs = session.query(User.id).filter(User.id.in_(loaded_user_ids))
        current_user_ids = [item[0] for item in qs]

        loaded_ids = [
            item["user_id"] for item in self.data if item["user_id"] in current_user_ids
        ]

        log.info(f"Lead| Removendo {len(loaded_ids)} registros existentes...")
        session.execute(Lead.__table__.delete().where(Lead.user_id.in_(loaded_ids)))

        items_to_add = [
            Lead(**item) for item in self.data if item["user_id"] in current_user_ids
        ]
        log.info(f"Lead| Inserindo {len(items_to_add)} novos registros no analytics...")
        session.bulk_save_objects(items_to_add)
        session.commit()
