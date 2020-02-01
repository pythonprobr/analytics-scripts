from datetime import datetime, timedelta

from resources.pagarme import pagarme


def _get_seven_days_ago():
    return datetime.now() - timedelta(days=7)


def _get_pagarme_filters(page_count):
    return {
        "page": page_count,
        "count": 100,
        "date_created": f">={_get_seven_days_ago():%Y-%m-%d}",
    }


def _get_transactions_from_pagarme():
    page_count = 0
    while True:
        page_count += 1
        transactions = pagarme.transaction.find_by(_get_pagarme_filters(page_count))
        if not transactions:
            break

        for item in transactions:
            yield item

