from urllib.parse import urlparse, parse_qsl

import sqlalchemy as db

from tasks.load_visits import _fetch_query_string
from utils import log
from v2.etl import ETL
from v2.models import PageView, Session


class ETLPageView(ETL):
    def extract(self):
        from resources.database import connection

        log.info("PageView| Carregando registros do sistema...")

        statement = db.sql.text(
            """
            SELECT
                p1.id
                , p1.created
                , p1.session_id
                , p1.meta->>'PATH_INFO'
                , p1.meta->>'QUERY_STRING'
            FROM analytics_pageview p1
            WHERE
                (
                    p1.meta->>'PATH_INFO' LIKE '%curso-de-python%'
                    OR p1.meta->>'QUERY_STRING' = '/'
                )
                AND p1.created >= :created
            ORDER BY p1.created DESC
            ;
            """
        )

        self.data = connection.execute(statement, created=self.date_limit)

    def transform(self):
        rows = []
        for id_, created, session_id, path_info, query_string in self.data:
            items = _fetch_query_string(query_string)
            row = {
                "id": id_,
                "created": created,
                "session_id": session_id,
                "path_info": path_info,
                "query_string": query_string[:1000],
                "utm_source": items.get("utm_source", "")[:1000],
                "utm_medium": items.get("utm_medium", "")[:1000],
                "utm_campaign": items.get("utm_campaign", "")[:1000],
                "utm_term": items.get("utm_term", "")[:1000],
                "utm_content": items.get("utm_content", "")[:1000],
            }
            rows.append(row)
        self.data = rows

    def load(self):
        from v2.database import session

        loaded_session_ids = [item["session_id"] for item in self.data]
        qs = session.query(Session.id).filter(Session.id.in_(loaded_session_ids))
        current_session_ids = [item[0] for item in qs]

        loaded_ids = [
            item["id"]
            for item in self.data
            if item["session_id"] in current_session_ids
        ]

        log.info(f"PageView| Removendo {len(loaded_ids)} registros existentes...")
        session.execute(PageView.__table__.delete().where(PageView.id.in_(loaded_ids)))

        # count = 0
        # for item in self.data:
        #     row = Session(**item)
        #     session.add(row)

        #     count += 1
        #     if count % 500 == 0:
        #         log.info(f"Session| Inserindo {count} novos registros no analytics...")
        #         session.commit()

        # log.info(f"Session| Inserindo {count} novos registros no analytics...")
        # session.commit()

        items_to_add = [
            PageView(**item)
            for item in self.data
            if item["session_id"] in current_session_ids
        ]

        count = 0
        for item in items_to_add:
            session.add(item)

            count += 1
            if count % 1000 == 0:
                log.info(f"PageView| Inserindo {count} novos registros no analytics...")
                session.commit()

        log.info(f"PageView| Inserindo {count} novos registros no analytics...")
        session.commit()
