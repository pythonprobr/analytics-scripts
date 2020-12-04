import requests

from settings import PROVI_USERNAME, PROVI_PASSWORD


def get_transactions():
    client = requests.Session()
    response = client.post(
        "https://ms-checkout.provi.com.br/sessions/login",
        json={"email": PROVI_USERNAME, "password": PROVI_PASSWORD},
    )

    client.headers["authorization"] = response.json()["token"]
    response = client.post(
        "https://ms-checkout.provi.com.br/v3/checkouts?page=1&quantity=10000000",
        json={"status": ["made_effective"], "productTypes": ["CourseFinancing"]},
    )

    return response.json()
