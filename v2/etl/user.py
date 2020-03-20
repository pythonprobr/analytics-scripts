import sqlalchemy as db

from utils import log
from v2.etl import ETL
from v2.models import User


class ETLUser(ETL):
    def extract(self):
        from resources.database import connection

        log.info("Carregando usuários do sistema...")

        statement = db.sql.text(
            """
            SELECT
                core_user.id as id
                , core_user.email as email
            FROM core_user
            ORDER BY 
                date_joined DESC
            """
        )

        self.data = connection.execute(statement)

    def transform(self):
        pass

    def load(self):
        from v2.database import session

        users = [item for item in self.data]
        loaded_ids = [item["id"] for item in users]

        log.info(f"Verificando quais dos {len(users)} usuários existem no analytics...")
        qs = session.query(User.id).filter(User.id.in_(loaded_ids))
        existing_ids = [id[0] for id in qs.all()]

        log.info(f"Ignorando {len(existing_ids)} registros existentes...")
        items_to_add = []
        for item in users:
            if item["id"] not in existing_ids:
                items_to_add.append(User(id=item["id"], email=item["email"]))

        log.info(f"Inserindo {len(items_to_add)} novos usuários no analytics...")
        session.bulk_save_objects(items_to_add)
        session.commit()
