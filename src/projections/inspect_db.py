import pandas as pd
from sqlalchemy import create_engine, inspect

DATABASE_URL = "sqlite:///src/projections/nba_db/nba.sqlite"
engine = create_engine(DATABASE_URL)

inspector = inspect(engine)
print(inspector.get_table_names())
