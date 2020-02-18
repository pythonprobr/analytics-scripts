from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qsl

from settings import TIME_ZONE
from utils import log


def _get_created():
    # return datetime(2020, 1, 1)
    return datetime.now() - timedelta(days=1)


def _extract_domain(uri):
    if not uri:
        return ""

    uri = urlparse(uri)
    return uri.netloc


def _fetch_query_string(query_string):
    PAID_SOURCES = (
        "rede-de-pesquisa",
        "youtube-ads",
        "facebook-ads",
    )

    MAP_SOURCES = {"google-ads": "rede-de-pesquisa"}

    MAP_MEDIUM = {
        "pago": "trafego-pago",
        "search": "trafego-pago",
    }

    items = dict(parse_qsl(query_string))

    for key, value in MAP_SOURCES.items():
        if key == items.get("utm_source"):
            items["utm_source"] = value

    for key, value in MAP_MEDIUM.items():
        if key == items.get("utm_medium"):
            items["utm_medium"] = value

    items["utm_medium"] = "trafego-organico"
    if items.get("utm_source") in PAID_SOURCES:
        items["utm_medium"] = "trafego-pago"

    if "utm_term" in items:
        items["utm_term"] = "'" + items["utm_term"]

    return items


def _email_is_valid(email):
    for search in ["@python.pro.br", "moa.moda@gmail.com"]:
        if search in email:
            return False
    return True


def _get_all_leads_from_database_until_now():
    import sqlalchemy as db
    from resources.database import connection

    statement = db.sql.text(
        """
        SELECT
            p1.id
            , p1.session_id
            , u.email
            , u.id
            , p1.created
            , p1.meta
            , 1 as visited_landing_page
            , CASE WHEN p2.created IS NOT NULL THEN 1 ELSE 0 END as visited_oto
            , CASE WHEN p3.created IS NOT NULL THEN 1 ELSE 0 END as subscribed
            , CASE WHEN p4.created IS NOT NULL THEN 1 ELSE 0 END as bought
            , CASE WHEN p5.created IS NOT NULL THEN 1 ELSE 0 END as activated
        FROM
            analytics_pageview p1

        LEFT JOIN analytics_usersession s ON p1.session_id = s.id
        LEFT JOIN core_user u ON s.user_id = u.id

        LEFT OUTER JOIN LATERAL (
            SELECT created FROM analytics_pageview p2
            WHERE
                p2.session_id = p1.session_id
                AND u.email IS NOT NULL
                AND p2.meta->>'PATH_INFO' = '/pagamento/curso-de-python-intermediario-oto'
            ORDER BY 1
            LIMIT 1
        ) as p2 ON TRUE

        LEFT OUTER JOIN LATERAL (
            SELECT created FROM analytics_pageview p3
            WHERE
                p3.session_id = p1.session_id
                AND u.email IS NOT NULL
                AND p3.meta->>'PATH_INFO' = '/obrigado'
            ORDER BY 1
            LIMIT 1
        ) as p3 ON TRUE

        LEFT OUTER JOIN LATERAL (
            SELECT created FROM analytics_pageview p4
            WHERE
                p4.session_id = p1.session_id
                AND u.email IS NOT NULL
                AND (
                    p4.meta->>'PATH_INFO' = '/pagamento/pytools/obrigado/'
                    OR p4.meta->>'PATH_INFO' = '/pagamento/pytools/obrigado'
                    OR p4.meta->>'PATH_INFO' = '/pagamento/pytools/boleto/'
                    OR p4.meta->>'PATH_INFO' = '/pagamento/pytools/boleto'
                )
            ORDER BY 1
            LIMIT 1
        ) as p4 ON TRUE

        LEFT OUTER JOIN LATERAL (
            SELECT created FROM analytics_pageview p5
            WHERE
                p5.session_id = p1.session_id
                AND u.email IS NOT NULL
                AND p5.meta->>'PATH_INFO' = '/modulos/python-birds/topicos/python-birds-motivacao'
            ORDER BY 1
            LIMIT 1
        ) as p5 ON TRUE

        WHERE
            (
                p1.meta->>'PATH_INFO' LIKE '%curso-de-python-gratis%'
                OR p1.meta->>'PATH_INFO' = '/'
            )
            AND p1.created >= :created

        ORDER BY p1.session_id, p1.created ASC
        ;
    """
    )

    return connection.execute(statement, created=_get_created())


def _prepare_created(date_joined):
    return date_joined.astimezone(TIME_ZONE).strftime("%Y-%m-%d %H:%M:%S")


def _prepare_visits_to_save_in_gsheets():
    rows = []
    user_ids = []
    last_PATH_INFO = ""
    last_session_id = 0
    duplicated = 0

    for (
        id_,
        session_id,
        email,
        user_id,
        created,
        meta,
        visited_landing_page,
        visited_oto,
        subscribed,
        bought,
        activated,
    ) in _get_all_leads_from_database_until_now():

        is_invalid_email = email is not None and _email_is_valid(email) is False
        is_invalid_visit = meta["PATH_INFO"] == "/" and visited_oto == 0
        if is_invalid_email or is_invalid_visit:
            continue

        current_PATH_INFO = meta.get("PATH_INFO")
        current_session_id = session_id
        if (
            current_PATH_INFO == last_PATH_INFO
            and current_session_id == last_session_id
        ):
            duplicated += 1
            continue

        if user_id in user_ids:
            duplicated += 1
            continue

        user_ids.append(user_id)
        last_PATH_INFO = current_PATH_INFO
        last_session_id = current_session_id

        created = _prepare_created(created)

        query_string = meta.get("QUERY_STRING") if meta.get("QUERY_STRING") else ""
        utms = _fetch_query_string(query_string)

        row = [
            id_,
            created,
            user_id,
            email,
            current_PATH_INFO,
            visited_landing_page,
            visited_oto,
            subscribed,
            bought,
            activated,
        ]
        row.append(utms.get("utm_source"))
        row.append(utms.get("utm_medium"))
        row.append(utms.get("utm_campaign"))
        row.append(utms.get("utm_term"))
        row.append(utms.get("utm_content"))
        row.append(_extract_domain(meta.get("HTTP_REFERER")))
        rows.append(row)

    log.debug(f"{duplicated} duplicados removidos.")
    return rows


def _get_worksheet():
    from resources.gsheets import spreadsheet

    return spreadsheet.worksheet_by_title("Visitas")


def _get_gsheets_current_data():
    worksheet = _get_worksheet()
    return worksheet.get_all_values(include_tailing_empty_rows=False)


def _generate_data_with_new_infos(items_from_database, data_from_gsheets):
    current_infos = [item[0] for item in data_from_gsheets]
    for item in items_from_database:
        id_ = str(item[0])
        if id_ in current_infos:
            continue

        data_from_gsheets.append(item)

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
    new_data = _generate_data_with_new_infos(visits_from_database, data_from_gsheets)

    log.info("Salvando novos visitas na planilha...")
    _save_new_data_in_gsheets(new_data)

    log.info("Fim da tarefa.")
