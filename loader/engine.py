from sqlalchemy import create_engine

from loader.environ import db_url

def create_db_engine():
    """Create the connection to the database

    Returns:
        DBAPI connection
    """
    return create_engine(db_url())

engine = create_db_engine()
