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

        if items.get("utm_source") == "google-ads":
            items["utm_source"] = "rede-de-pesquisa"

            if items.get("utm_medium") == "search":
                items["utm_medium"] = "trafego-pago"

        if items.get("utm_medium") == "pago":
            items["utm_medium"] = "trafego-pago"

    return items


def _get_seven_days_ago():
    # return datetime(2020, 2, 10)
    return datetime(2020, 1, 1)
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
            AnalyticsPageview.id,
            AnalyticsPageview.created,
            AnalyticsPageview.meta,
            AnalyticsUsersession.uuid,
        )
        .filter(AnalyticsPageview.created >= _get_seven_days_ago())
        .join(
            AnalyticsUsersession,
            AnalyticsPageview.session_id == AnalyticsUsersession.id,
        )
        .order_by(AnalyticsUsersession.uuid, AnalyticsPageview.created)
    )
    return qs


def _prepare_created(date_joined):
    return date_joined.astimezone(TIME_ZONE).strftime("%Y-%m-%d %H:%M:%S")


def _prepare_visits_to_save_in_gsheets():
    rows = []
    ids = []

    last_uuid = ""
    last_utms = {}

    for id_, created, meta, uuid in _get_all_leads_from_database_until_now().all():
        if id_ in ids:
            continue

        is_to_proceed = False
        for item in (
            "curso-de-python-gratis",
            "curso-de-python-intermediario",
            "obrigado",
        ):
            if item in meta["RAW_URI"]:
                is_to_proceed = True
                break

        if not is_to_proceed:
            continue

        ids.append(id_)
        created = _prepare_created(created)

        utms = _fetch_query_string(meta.get("QUERY_STRING", ""))
        if last_uuid == uuid:
            utms = last_utms

        last_utms = utms
        last_uuid = uuid

        row = [id_, created, uuid, meta["PATH_INFO"]]
        row.append(utms.get("utm_source"))
        row.append(utms.get("utm_medium"))
        row.append(utms.get("utm_campaign"))
        row.append(utms.get("utm_term"))
        row.append(utms.get("utm_content"))
        rows.append(row)
    return rows


def _get_worksheet():
    from resources.gsheets import spreadsheet

    return spreadsheet.worksheet_by_title("Visitas")


def _get_gsheets_current_data():
    worksheet = _get_worksheet()
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
    worksheet = _get_worksheet()
    worksheet.update_values("A1", data)


def run():
    log.info("Iniciando carregamento de novas visitas...")

    log.info("Recuperando visitas da base de dados...")
    visits_from_database = _prepare_visits_to_save_in_gsheets()

    log.info("Recuperando visitas da planilha...")
    data_from_gsheets = _get_gsheets_current_data()

    log.info("Juntando visitas...")
    new_data = _generate_data_with_new_emails(visits_from_database, data_from_gsheets)

    log.info("Salvando novos visitas na planilha...")
    _save_new_data_in_gsheets(new_data)

    log.info("Fim da tarefa.")

