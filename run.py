from etl.transactions import Transactions
from etl.leads import Leads
from etl.loans import Loans
from etl.bot import run as bot_run

Transactions().run()
Leads().run()
Loans().run()
bot_run()
