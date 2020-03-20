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
        pass

    def load(self):
        from v2.database import session

        sessions = [item for item in self.data]
        loaded_users_ids = [item["user_id"] for item in sessions]

        log.info(f"Lead| Verificando quais dos {len(sessions)} existem no analytics...")
        qs = session.query(Lead.id).filter(Lead.user_id.in_(loaded_users_ids))
        existing_ids = [id[0] for id in qs.all()]

        log.info(f"Lead| Ignorando {len(existing_ids)} registros existentes...")
        items_to_add = []
        for item in sessions:
            if item["user_id"] not in existing_ids:
                items_to_add.append(
                    Lead(created=item["created"], user_id=item["user_id"])
                )

        log.info(f"Lead| Inserindo {len(items_to_add)} novos registros no analytics...")
        session.bulk_save_objects(items_to_add)
        session.commit()
