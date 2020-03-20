import sqlalchemy as db

from utils import log
from v2.etl import ETL
from v2.models import UserProgress, User


class ETLProgress(ETL):
    def extract(self):
        from resources.database import connection

        log.info("UserProgress| Carregando registros do sistema...")

        statement = db.sql.text(
            """
            SELECT
                core_user.id as user_id
                , MAX(interaction.creation) as last_interaction
                , SUM(topic.duration) as topic_duration
                , SUM(interaction.total_watched_time) as total_watched_time
            FROM modules_module AS module
            INNER JOIN modules_section section ON module.id = section.module_id
            INNER JOIN modules_chapter AS chapter ON chapter.section_id=section.id
            INNER JOIN modules_topic AS topic ON topic.chapter_id=chapter.id
            INNER JOIN dashboard_topicinteraction AS interaction ON interaction.topic_id=topic.id
            INNER JOIN core_user ON interaction.user_id=core_user.id
            INNER JOIN core_user_groups ON core_user_groups.user_id = core_user.id
            WHERE
                core_user_groups.group_id = 2
                AND module.id = 1
                AND interaction.creation >= :created
            GROUP BY 
                core_user.id
                , module.id
            ORDER BY 
                last_interaction DESC
            """
        )

        self.data = connection.execute(statement, created=self.date_limit)

    def transform(self):
        rows = []
        for (
            user_id,
            last_interaction,
            topic_duration,
            total_watched_time,
        ) in self.data:
            percentile_finished = total_watched_time / topic_duration
            percentile_finished = 1 if percentile_finished > 1 else percentile_finished
            row = [
                user_id,
                last_interaction,
                percentile_finished,
            ]
            rows.append(row)
        self.data = rows

    def load(self):
        from v2.database import session

        loaded_users_ids = [user_id for user_id, _, _ in self.data]
        log.info(
            f"UserProgress| Removendo {len(loaded_users_ids)} registros existentes..."
        )
        # session.query().filter(UserProgress.user_id.in_(loaded_users_ids)).delete()
        session.execute(
            UserProgress.__table__.delete().where(
                UserProgress.user_id.in_(loaded_users_ids)
            )
        )

        items_to_add = []
        for user_id, last_interaction, percentile_finished in self.data:
            items_to_add.append(
                UserProgress(
                    last_interaction=last_interaction,
                    user_id=user_id,
                    progress=percentile_finished,
                )
            )

        log.info(
            f"UserProgress| Inserindo {len(items_to_add)} novos registros no analytics..."
        )
        session.bulk_save_objects(items_to_add)
        session.commit()
