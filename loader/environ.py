import os

def db_url():
    return os.getenv(
        "db_url",
        "postgresql+psycopg2://postgres:Welcome2Postgres!@localhost/investing",
    )
