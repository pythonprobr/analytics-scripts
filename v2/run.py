import sys

sys.path.append("./")


from v2.etl.user import ETLUser
from v2.etl.session import ETLSession
from v2.etl.lead import ETLLead
from v2.etl.progress import ETLProgress

user = ETLUser()
session = ETLSession()
lead = ETLLead()
progress = ETLProgress()

user.run()
lead.run()
session.run()
progress.run()
