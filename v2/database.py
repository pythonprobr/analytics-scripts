import sys

sys.path.append("./")

import sqlalchemy as db
from sqlalchemy.orm import sessionmaker

from settings import ANALYTICS_DATABASE_URL


engine = db.create_engine(ANALYTICS_DATABASE_URL)

# from v2.models import Base

# Base.metadata.create_all(engine)

connection = engine.connect()

Session = sessionmaker()
Session.configure(bind=engine)

session = Session()
