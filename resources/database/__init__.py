import sqlalchemy as db
from sqlalchemy.orm import sessionmaker

from settings import PYTHONPRO_DATABASE_URL


engine = db.create_engine(PYTHONPRO_DATABASE_URL)
connection = engine.connect()

Session = sessionmaker()
Session.configure(bind=engine)

session = Session()
