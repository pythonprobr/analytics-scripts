import sys
from datetime import datetime

sys.path.append("./")


from v2.etl.user import ETLUser
from v2.etl.session import ETLSession
from v2.etl.lead import ETLLead
from v2.etl.progress import ETLProgress
from v2.etl.pageview import ETLPageView

date_until = datetime(2020, 3, 21)
if "--full" in sys.argv:
    date_until = datetime(2019, 12, 1)

user = ETLUser(date_until)
session = ETLSession(date_until)
lead = ETLLead(date_until)
progress = ETLProgress(date_until)
pageview = ETLPageView(date_until)

user.run()
session.run()
pageview.run()
# lead.run()
# progress.run()
