import pytest

from tasks.load_transactions import _get_transactions_from_pagarme, _get_pagarme_filters


@pytest.fixture
def mocked_pagarme(mocker):
    return mocker.patch("tasks.load_transactions.pagarme")


def test_should_get_transactions_from_pagarme(mocked_pagarme):
    _get_transactions_from_pagarme()
    assert mocked_pagarme.transaction.find_by.called_with(_get_pagarme_filters(1))


def test_should_prepare_data_to_be_loaded():
    assert False


def test_should_return_get_gsheets_current_data():
    assert False


def test_should_generate_data_with_new_transactions():
    assert False


def test_should_save_new_data_in_gsheets():
    assert False


def test_should_run_ok():
    assert False
