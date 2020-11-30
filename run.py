from etl.transactions import Transactions
from etl.leads import Leads
from etl.bot import run as bot_run

Transactions().run()
Leads().run()
bot_run()
