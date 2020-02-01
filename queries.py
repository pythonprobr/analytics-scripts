from datetime import datetime, timedelta

import psycopg2
from decouple import config

from settings import (
    PYTHONPRO_DATABASE_NAME,
    PYTHONPRO_DATABASE_USER,
    PYTHONPRO_DATABASE_PASSWORD,
    PYTHONPRO_DATABASE_HOST,
    PYTHONPRO_DATABASE_PORT,
)


conn = psycopg2.connect(
    dbname=PYTHONPRO_DATABASE_NAME,
    user=PYTHONPRO_DATABASE_USER,
    password=PYTHONPRO_DATABASE_PASSWORD,
    host=PYTHONPRO_DATABASE_HOST,
    port=PYTHONPRO_DATABASE_PORT,
)

cursor = conn.cursor()


def _remove_duplicated_emails(cursor):
    emails = []

    print("--> iterating over all info...")
    for email, meta, created in cursor:
        if email in emails:
            continue

        emails.append(email)
        yield email, meta, created


def _get_all_leads_from_database_until_now():
    now = datetime.now()
    seven_days_ago = datetime.now() - timedelta(days=7)

    seven_days_ago = seven_days_ago.strftime("%Y-%m-%d")
    now = now.strftime("%Y-%m-%d")

    cursor.execute(
        f"""
        select 
            u.email, meta, u.date_joined
        from core_user u
        left join analytics_usersession s on s.user_id = u.id
        left join analytics_pageview p on p.session_id = s.id
        where 
            p.meta->>'RAW_URI' LIKE '%curso-de-python-gratis%'
            and u.date_joined >= '{seven_days_ago}'
        order by p.created
        ;
    """
    )

    return cursor


def get_all_leads_until_now():
    print("--> getting info from database...")
    cursor = _get_all_leads_from_database_until_now()

    rows = []
    for email, meta, created in _remove_duplicated_emails(cursor):
        utms = _fetch_query_string(meta.get("QUERY_STRING", ""))

        row = {"created": created.strftime("%Y-%m-%d %H:%M:%S"), "email": email}
        row["utm_source"] = utms.get("utm_source")
        row["utm_medium"] = utms.get("utm_medium")
        row["utm_campaign"] = utms.get("utm_campaign")
        row["utm_term"] = utms.get("utm_term")
        row["utm_content"] = utms.get("utm_content")
        rows.append(row)

    return rows
