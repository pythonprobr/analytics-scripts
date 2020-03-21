import sqlalchemy as db

from utils import log
from v2.etl import ETL
from v2.models import Session, User, PageView


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
        self.data = [
            {"id": item["id"], "user_id": item["user_id"],} for item in self.data
        ]

    def load(self):
        from v2.database import session

        loaded_user_ids = [item["user_id"] for item in self.data]
        qs = session.query(User.id).filter(User.id.in_(loaded_user_ids))
        current_user_ids = [item[0] for item in qs]

        loaded_ids = [
            item["id"] for item in self.data if item["user_id"] in current_user_ids
        ]

        log.info(f"Session| Removendo {len(loaded_ids)} registros existentes...")
        session.execute(
            PageView.__table__.delete().where(PageView.session_id.in_(loaded_ids))
        )
        session.execute(Session.__table__.delete().where(Session.id.in_(loaded_ids)))

        items_to_add = [
            Session(**item) for item in self.data if item["user_id"] in current_user_ids
        ]
        log.info(
            f"Session| Inserindo {len(items_to_add)} novos registros no analytics..."
        )
        session.bulk_save_objects(items_to_add)
        session.commit()
