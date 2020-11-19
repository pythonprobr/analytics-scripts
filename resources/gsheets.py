import pygsheets

from settings import SPREADSHEET_KEY

gc = pygsheets.authorize(outh_file="client_secret.json")

spreadsheet = gc.open_by_key(SPREADSHEET_KEY)
