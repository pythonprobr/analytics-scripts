from datetime import datetime, timedelta

from settings import TIME_ZONE
from utils import log


def _get_seven_days_ago():
    return datetime.now() - timedelta(days=7)


def _get_all_activations_from_database_until_now():
    from resources.database.models import DashboardTopicinteraction, CoreUser
    from resources.database import session

    qs = (
        session.query(DashboardTopicinteraction.creation, CoreUser.email)
        # .filter(CoreUser.date_joined >= datetime(2019, 12, 1))
        .filter(CoreUser.date_joined >= _get_seven_days_ago())
        .join(CoreUser, DashboardTopicinteraction.user_id == CoreUser.id)
        .filter(DashboardTopicinteraction.max_watched_time > 0)
        .order_by(DashboardTopicinteraction.creation)
    )
    return qs


def _prepare_creation(creation):
    return creation.astimezone(TIME_ZONE).strftime("%Y-%m-%d %H:%M:%S")


def _prepare_activations_to_save_in_gsheets():
    rows = []
    emails = []
    count = 1
    for creation, email in _get_all_activations_from_database_until_now().all():
        if email in emails:
            continue

        emails.append(email)
        creation = _prepare_creation(creation)

        row = [count, creation, email]
        rows.append(row)
        count += 1
    return rows


def _get_worksheet():
    from resources.gsheets import spreadsheet

    return spreadsheet.worksheet_by_title("Ativações")


def _get_gsheets_current_data():
    worksheet = _get_worksheet()
    return worksheet.get_all_values(include_tailing_empty_rows=False)


def _generate_data_with_new_data(leads_from_database, data_from_gsheets):
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
    log.info("Iniciando carregamento de novas ativações...")

    log.info("Recuperando ativações da base de dados...")
    leads_from_database = _prepare_activations_to_save_in_gsheets()

    log.info("Recuperando ativações da planilha...")
    data_from_gsheets = _get_gsheets_current_data()

    log.info("Juntando ativações...")
    new_data = _generate_data_with_new_data(leads_from_database, data_from_gsheets)

    log.info("Salvando novos ativações na planilha...")
    _save_new_data_in_gsheets(new_data)

    log.info("Fim da tarefa.")
