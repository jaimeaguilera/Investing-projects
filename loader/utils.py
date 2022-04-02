import io

import sqlalchemy

from utilities.logger import logger
from utilites.engine import create_db_engine
from utlities.environ import db_url


def to_sql(df, db_url, table, schema, if_exists, sep="\t"):
    engine = sqlalchemy.create_engine(
        db_url, connect_args={"options": f"-csearch_path={schema}"}
    )

    # Create Table
    df[:0].to_sql(
        table,
        con=engine,
        schema=schema,
        if_exists=if_exists,
        index=False,
        method="multi",
    )

    # Prepare data
    output = io.StringIO()
    df.to_csv(output, sep=sep, header=False, index=False)
    output.seek(0)

    # Insert data
    conn = engine.raw_connection()
    cursor = conn.cursor()
    cursor.copy_from(output, table, sep=sep, null="")
    conn.commit()
    cursor.close()
    
def df_to_table(
    df,
    table_name,
    engine=None,
    schema=None,
    chunksize=5000,
    if_exists="replace",
):
    """Saves a pandas DataFrame into a table inside the database

    Args:
      df: pandas dataframe that is going to be saved (pd.DataFrame)
      table_name: name of the table in the database (String)
      engine: engine used to connect to the DB (sqlalchemy.engine)
      schema: schema of the DB in which the table is located (String)
      chunksize: size of the chunks of data (Integer)
      if_exists: action to take if the table already exists in the DB ['replace' or 'append'] (String)

    Returns:
      df: same pandas DataFrame as the input (pd.DataFrame)
    """
    if engine is None:
        engine = create_db_engine()
    if "." in table_name:
        schema, table_name = table_name.split(".")
    if schema is None:
        logger.error(f"table schema for {table_name} is not specified")

    record_num = df.shape[0]

    if (record_num < chunksize) or (schema in ["param"]):
        df.to_sql(
            table_name,
            con=engine,
            schema=schema,
            index=False,
            if_exists=if_exists,
            method="multi",
        )
    else:
        to_sql(
            df=df,
            db_url=db_url(),
            table=table_name,
            schema=schema,
            if_exists=if_exists,
        )
    logger.info(
        f"{record_num} records were written into table: {schema}.{table_name}"
    )

    return df