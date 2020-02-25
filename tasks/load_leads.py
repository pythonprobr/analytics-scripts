from datetime import datetime, timedelta

from settings import TIME_ZONE
from utils import log
from tasks.load_visits import _fetch_query_string


def _get_seven_days_ago():
    # return datetime(2019, 12, 1)
    return datetime.now() - timedelta(days=7)


def _get_all_leads_from_database_until_now():
    import sqlalchemy as db

    from resources.database.models import (
        CoreUser,
        AnalyticsPageview,
        AnalyticsUsersession,
    )
    from resources.database import session

    qs = (
        session.query(
            CoreUser.date_joined, CoreUser.email, CoreUser.id, AnalyticsPageview.meta
        )
        .filter(CoreUser.date_joined >= _get_seven_days_ago())
        .join(AnalyticsUsersession, AnalyticsUsersession.user_id == CoreUser.id)
        .join(
            AnalyticsPageview, AnalyticsPageview.session_id == AnalyticsUsersession.id
        )
        .filter(
            AnalyticsPageview.meta["RAW_URI"]
            .astext.cast(db.types.Unicode)
            .like("%curso-de-python-gratis%")
        )
        .order_by(AnalyticsPageview.created)
    )

    return qs


def _prepare_date_joined(date_joined):
    return date_joined.astimezone(TIME_ZONE).strftime("%Y-%m-%d %H:%M:%S")


def _prepare_leads_to_save_in_gsheets():
    rows = []
    emails = []
    for date_joined, email, id_, meta in _get_all_leads_from_database_until_now().all():
        if email in emails:
            continue

        emails.append(email)
        date_joined = _prepare_date_joined(date_joined)

        row = [id_, date_joined, email]

        utms = _fetch_query_string(meta["QUERY_STRING"])
        row.append(utms.get("utm_source"))
        row.append(utms.get("utm_medium"))
        row.append(utms.get("utm_campaign"))
        row.append(utms.get("utm_term"))
        row.append(utms.get("utm_content"))

        rows.append(row)
    return rows


def _get_leads_worksheet():
    from resources.gsheets import spreadsheet

    return spreadsheet.worksheet_by_title("Leads")


def _get_gsheets_current_data():
    worksheet = _get_leads_worksheet()
    return worksheet.get_all_values(include_tailing_empty_rows=False)


def _generate_data_with_new_emails(leads_from_database, data_from_gsheets):
    current_ids = [item[0] for item in data_from_gsheets]
    for lead in leads_from_database:
        id_ = str(lead[0])
        if id_ in current_ids:
            continue

        lead[6] = "'" + lead[6]
        data_from_gsheets.append(lead)

    return data_from_gsheets


def _save_new_data_in_gsheets(data):
    worksheet = _get_leads_worksheet()
    worksheet.update_values("A1", data)


def run():
    log.info("Iniciando carregamento de novos leads...")

    log.info("Recuperando leads da base de dados...")
    leads_from_database = _prepare_leads_to_save_in_gsheets()

    log.info("Recuperando leads da planilha...")
    data_from_gsheets = _get_gsheets_current_data()

    log.info("Juntando leads...")
    new_data = _generate_data_with_new_emails(leads_from_database, data_from_gsheets)

    log.info("Salvando novos leads na planilha...")
    _save_new_data_in_gsheets(new_data)

    log.info("Fim da tarefa.")
