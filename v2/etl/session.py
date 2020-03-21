import sqlalchemy as db

from utils import log
from v2.etl import ETL
from v2.models import Session, User


class ETLSession(ETL):
    def extract(self):
        from resources.database import connection

        log.info("Session| Carregando registros do sistema...")

        statement = db.sql.text(
            """
            SELECT
                id
                , user_id
            FROM analytics_usersession
            WHERE
                created >= :created
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
        loaded_ids = [item["id"] for item in sessions]
        loaded_users_ids = [item["id"] for item in sessions]

        log.info(
            f"Session| Verificando quais dos {len(sessions)} existem no analytics..."
        )
        qs = session.query(Session.id).filter(Session.id.in_(loaded_ids))
        existing_ids = [id[0] for id in qs.all()]

        log.info(f"Session| Verificando usuários que existem no analytics...")
        qs = session.query(User.id).filter(User.id.in_(loaded_users_ids))
        existing_users_ids = [id[0] for id in qs.all()]

        log.info(f"Session| Ignorando {len(existing_ids)} registros existentes...")
        items_to_add = []
        for item in sessions:
            if item["id"] not in existing_ids and (
                item["user_id"] is None or item["user_id"] in existing_users_ids
            ):
                items_to_add.append(Session(id=item["id"], user_id=item["user_id"]))

        log.info(
            f"Session| Inserindo {len(items_to_add)} novos registros no analytics..."
        )
        session.bulk_save_objects(items_to_add)
        session.commit()
