from datetime import datetime


class ETL:
    def __init__(self, date_limit=datetime(2019, 11, 1), *args, **kwargs):
        self.date_limit = date_limit

    def extract(self):
        raise NotImplementedError

    def transform(self):
        raise NotImplementedError

    def load(self):
        raise NotImplementedError

    def run(self):
        self.extract()
        self.transform()
        self.load()

