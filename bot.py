from database import engine
from sqlalchemy import text
import os

token = os.environ['TOKEN']

with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM users"))
    rows = result.fetchall()
    rows_as_dicts = [dict(row._asdict()) for row in rows]
    print(rows_as_dicts)

#####
