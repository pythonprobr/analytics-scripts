import pygsheets

from settings import GOOGLE_ADS_SPREADSHEET_KEY

gc = pygsheets.authorize(outh_file="client_secret.json")

spreadsheet = gc.open_by_key(GOOGLE_ADS_SPREADSHEET_KEY)
worksheet = spreadsheet.worksheet_by_title("Leads")
