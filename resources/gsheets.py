import pygsheets

from settings import GOOGLE_ADS_SPREADSHEET_KEY

gc = pygsheets.authorize(outh_file="client_secret.json")

spreadsheet = gc.open_by_key(GOOGLE_ADS_SPREADSHEET_KEY)
worksheet = spreadsheet.worksheet_by_title("Leads")


# def load_all_leads_until_now():
#     leads = get_all_leads_until_now()

#     print("--> downloading current information from sheets...")
#     current_data = worksheet.get_all_values(include_tailing_empty_rows=False)
#     current_emails = [item[1] for item in current_data]

#     print("--> inserting new emails...")
#     for lead in leads:
#         if lead["email"] not in current_emails:
#             current_data.append(list(lead.values()))

#     print("--> saving new info in sheets...")
#     worksheet.update_values("A1", current_data)

