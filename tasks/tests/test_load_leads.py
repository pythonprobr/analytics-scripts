import pytest

from resources.database.models import CoreUser
from tasks.load_leads import (
    _fetch_query_string,
    _get_all_leads_from_database_until_now,
    _get_gsheets_current_data,
    _prepare_leads_to_save_in_gsheets,
    _generate_data_with_new_emails,
    _save_new_data_in_gsheets,
    run,
)


def test_should_fetch_query_string():
    assert _fetch_query_string(
        "utm_source=google-ads&utm_medium=pago&utm_campaign=rede-de-pesquisa&"
        "utm_content=voce-nao-precisa-de-faculdade"
    ) == {
        "utm_campaign": "rede-de-pesquisa",
        "utm_content": "voce-nao-precisa-de-faculdade",
        "utm_medium": "pago",
        "utm_source": "google-ads",
    }


def test_should_ignore_non_utm_parameters():
    assert _fetch_query_string(
        "utm_source=google-ads&utm_medium=pago&utm_campaign=rede-de-pesquisa&"
        "utm_content=voce-nao-precisa-de-faculdade&foo=bar"
    ) == {
        "utm_campaign": "rede-de-pesquisa",
        "utm_content": "voce-nao-precisa-de-faculdade",
        "utm_medium": "pago",
        "utm_source": "google-ads",
    }


def test_should_ignore_string_without_ampersand():
    assert (
        _fetch_query_string(
            "utm_source=google-adsutm_medium=pagoutm_campaign=rede-de-pesquisa"
            "utm_content=voce-nao-precisa-de-faculdadefoo=bar"
        )
        == {}
    )


def test_should_ignore_string_without_equals():
    assert (
        _fetch_query_string(
            "utm_sourcegoogle-ads&utm_mediumpago&utm_campaignrede-de-pesquisa&"
            "utm_contentvoce-nao-precisa-de-faculdade&foobar"
        )
        == {}
    )


def test_should_retrieve_all_leads_from_database_until_now(mocker):
    mocked_session = mocker.patch("tasks.load_leads.session")

    _get_all_leads_from_database_until_now()
    assert mocked_session.query.called


def test_should_prepare_data_to_be_loaded(mocker):
    mocker.patch(
        "tasks.load_leads._get_all_leads_from_database_until_now",
        return_value=[
            (
                "2020-02-01",
                "moa.moda@gmail.com",
                {"RAW_URI": "/curso-de-python-gratis", "QUERY_STRING": ""},
            ),
            (
                "2020-02-01",
                "renzo@python.pro.br",
                {
                    "QUERY_STRING": "utm_source=google-ads&utm_medium=pago&utm_campaign=rede-de"
                    "-pesquisa&utm_content=voce-nao-precisa-de-faculdade",
                },
            ),
        ],
    )
    assert _prepare_leads_to_save_in_gsheets() == [
        ["2020-02-01", "moa.moda@gmail.com", None, None, None, None, None],
        [
            "2020-02-01",
            "renzo@python.pro.br",
            "google-ads",
            "pago",
            "rede-de-pesquisa",
            None,
            "voce-nao-precisa-de-faculdade",
        ],
    ]


@pytest.fixture
def mocked_worksheet(mocker):
    return mocker.patch("tasks.load_leads.worksheet")


def test_should_return_get_gsheets_current_data(mocked_worksheet):
    _get_gsheets_current_data()
    assert mocked_worksheet.gel_all_values.called_with(include_tailing_empty_rows=False)


@pytest.fixture
def data_from_gsheets():
    return [
        [
            "2020-02-01 18:07:00",
            "francisconunesnl@gmail.com",
            "rede-de-pesquisa",
            "trafego-pago",
            "leads-python-birds-antiga",
            "curso%20de%20programa%C3%A7%C3%A3o",
        ],
        [
            "2020-02-01 18:07:45",
            "paulo.henrique10@outlook.com",
            "rede-de-pesquisa",
            "trafego-pago",
            "leads-python-birds-aprender-python",
            "%2Baprender%20%2Bpython",
        ],
        ["2020-02-01 19:03:23", "testeboleto2@python.pro.br", "", "", "", "",],
    ]


@pytest.fixture
def leads_from_database():
    return [
        ["2020-02-01", "moa.moda@gmail.com", None, None, None, None, None],
        [
            "2020-02-01",
            "renzo@python.pro.br",
            "google-ads",
            "pago",
            "rede-de-pesquisa",
            None,
            "voce-nao-precisa-de-faculdade",
        ],
    ]


def test_should_generate_data_with_new_emails(data_from_gsheets, leads_from_database):
    assert _generate_data_with_new_emails(leads_from_database, data_from_gsheets) == [
        [
            "2020-02-01 18:07:00",
            "francisconunesnl@gmail.com",
            "rede-de-pesquisa",
            "trafego-pago",
            "leads-python-birds-antiga",
            "curso%20de%20programa%C3%A7%C3%A3o",
        ],
        [
            "2020-02-01 18:07:45",
            "paulo.henrique10@outlook.com",
            "rede-de-pesquisa",
            "trafego-pago",
            "leads-python-birds-aprender-python",
            "%2Baprender%20%2Bpython",
        ],
        ["2020-02-01 19:03:23", "testeboleto2@python.pro.br", "", "", "", "",],
        ["2020-02-01", "moa.moda@gmail.com", None, None, None, None, None],
        [
            "2020-02-01",
            "renzo@python.pro.br",
            "google-ads",
            "pago",
            "rede-de-pesquisa",
            None,
            "voce-nao-precisa-de-faculdade",
        ],
    ]


def test_should_save_new_data_in_gsheets(mocked_worksheet):
    _save_new_data_in_gsheets(1)

    assert mocked_worksheet.update_values.called_with("A1", 1)


def test_should_run_ok(mocker):
    m1 = mocker.patch("tasks.load_leads._prepare_leads_to_save_in_gsheets")
    m2 = mocker.patch("tasks.load_leads._get_gsheets_current_data")
    m3 = mocker.patch("tasks.load_leads._generate_data_with_new_emails", return_value=1)
    m4 = mocker.patch("tasks.load_leads._save_new_data_in_gsheets")
    run()

    assert m1.called
    assert m2.called
    assert m3.called
    assert m4.called

