from datetime import datetime, timedelta

from settings import TIME_ZONE
from utils import log


def _fetch_query_string(query_string):
    items = {}
    if "&" in query_string and "=" in query_string:
        for item in query_string.split("&"):
            key, value = item.split("=") if "utm_" in item else (None, None)
            if key and value:
                items[key] = value
    return items


def _get_seven_days_ago():
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
        session.query(CoreUser.date_joined, CoreUser.email, AnalyticsPageview.meta)
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
        .all()
    )

    return qs


def _prepare_leads_to_save_in_gsheets():
    rows = []
    emails = []
    for date_joined, email, meta in _get_all_leads_from_database_until_now():
        if email in emails:
            continue

        emails.append(email)
        date_joined = date_joined.astimezone(TIME_ZONE)

        row = [date_joined.strftime("%Y-%m-%d %H:%M:%S"), email]

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
    current_emails = [item[1] for item in data_from_gsheets]
    for lead in leads_from_database:
        email = lead[1]
        if email in current_emails:
            continue

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
