from datetime import datetime, timedelta

from settings import TIME_ZONE
from utils import log


def _get_created():
    # return datetime(2019, 12, 1)
    return datetime.now() - timedelta(days=7)


def _get_all_progress_from_database_until_now():
    import sqlalchemy as db
    from resources.database import connection

    statement = db.sql.text(
        """
        SELECT
            core_user.id as id
            , MAX(interaction.creation) as last_interaction
            , MAX(core_user.email) email
            , MAX(module.title) module
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

    return connection.execute(statement, created=_get_created())


def _prepare_date(date_to_prepare):
    return date_to_prepare.astimezone(TIME_ZONE).strftime("%Y-%m-%d %H:%M:%S")


def _prepare_activations_to_save_in_gsheets():
    rows = []
    for (
        id_,
        last_interaction,
        email,
        module,
        topic_duration,
        total_watched_time,
    ) in _get_all_progress_from_database_until_now():

        last_interaction = _prepare_date(last_interaction)
        is_finished = total_watched_time >= topic_duration
        percentile_finished = (
            (total_watched_time / topic_duration) if not is_finished else 1
        )

        row = [
            str(id_),
            last_interaction,
            email,
            module,
            is_finished,
            percentile_finished,
        ]
        rows.append(row)
    return rows


def _get_worksheet():
    from resources.gsheets import spreadsheet

    return spreadsheet.worksheet_by_title("PA | Progressos")


def _get_gsheets_current_data():
    worksheet = _get_worksheet()
    return worksheet.get_all_values(include_tailing_empty_rows=False)


def _generate_data_with_new_data(rows_from_database, rows_from_sheets):
    rows_from_database = {item[0]: item for item in rows_from_database}
    rows_from_sheets = {item[0]: item for item in rows_from_sheets}

    for id_, value in rows_from_database.items():
        rows_from_sheets[id_] = value

    return list(rows_from_sheets.values())


def _save_new_data_in_gsheets(data):
    worksheet = _get_worksheet()
    worksheet.update_values("A1", data)


def run():
    log.info("Iniciando carregamento de novos progressos...")

    log.info("Recuperando progressos da base de dados...")
    leads_from_database = _prepare_activations_to_save_in_gsheets()

    log.info("Recuperando progressos da planilha...")
    data_from_gsheets = _get_gsheets_current_data()

    log.info("Juntando progressos...")
    new_data = _generate_data_with_new_data(leads_from_database, data_from_gsheets)

    log.info("Salvando novos progressos na planilha...")
    _save_new_data_in_gsheets(new_data)

    log.info("Fim da tarefa.")
