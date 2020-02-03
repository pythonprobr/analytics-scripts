from datetime import datetime

import pytest

from tasks.load_transactions import (
    _get_transactions_from_pagarme,
    _get_pagarme_filters,
    _get_gsheets_current_data,
    _prepare_data_to_be_loaded,
    _generate_data_with_new_transactions,
    _save_new_data_in_gsheets,
    run,
)


@pytest.fixture
def mocked_pagarme(mocker):
    return mocker.patch("tasks.load_transactions.pagarme")


def test_should_get_transactions_from_pagarme(mocked_pagarme):
    _get_transactions_from_pagarme(datetime.now())
    assert mocked_pagarme.transaction.find_by.called_with(
        _get_pagarme_filters(1, datetime.now())
    )


@pytest.fixture
def transaction():
    return {
        "object": "transaction",
        "customer": {"object": "customer", "documents": [{"object": "document",}],},
        "billing": {"object": "billing", "address": {"object": "address",},},
        "items": [{"object": "item",}],
        "card": {"object": "card",},
    }


@pytest.fixture
def mocked_get_transactions_from_pagarme(mocker, transaction):
    return mocker.patch(
        "tasks.load_transactions._get_transactions_from_pagarme",
        return_value=[transaction],
    )


def test_should_prepare_data_to_be_loaded(
    mocked_get_transactions_from_pagarme, transaction
):
    assert _prepare_data_to_be_loaded() == [
        {
            "billing_address_object": "address",
            "billing_object": "billing",
            "card_object": "card",
            "customer_documents_0_object": "document",
            "customer_object": "customer",
            "items_0_object": "item",
            "object": "transaction",
        },
    ]


@pytest.fixture
def mocked_worksheet(mocker):
    return mocker.patch("tasks.load_transactions._get_transactions_worksheet")


def test_should_return_get_gsheets_current_data(mocked_worksheet):
    _get_gsheets_current_data()
    assert mocked_worksheet.called


def test_should_generate_data_with_new_transactions():
    assert False


def test_should_save_new_data_in_gsheets(mocked_worksheet):
    _save_new_data_in_gsheets(1)
    assert mocked_worksheet.update_values.called_with("A1", 1)


def test_should_run_ok(mocker):
    m1 = mocker.patch("tasks.load_transactions._prepare_data_to_be_loaded")
    m2 = mocker.patch("tasks.load_transactions._get_gsheets_current_data")
    m3 = mocker.patch(
        "tasks.load_transactions._generate_data_with_new_transactions", return_value=1
    )
    m4 = mocker.patch("tasks.load_transactions._save_new_data_in_gsheets")
    run()

    assert m1.called
    assert m2.called
    assert m3.called
    assert m4.called

