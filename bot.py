from database import engine
from sqlalchemy import text
import os
from datetime import date

token = os.environ['TOKEN']

with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM users"))
    rows = result.fetchall()
    rows_as_dicts = [dict(row._asdict()) for row in rows]

    for row in rows_as_dicts:
        expiration_date = row['expiration_date']
        if expiration_date < date.today():
            user_id = row['user_id']
            conn.execute(
                text("UPDATE users SET active = 0 WHERE user_id = :user_id"),
                {'user_id': user_id}
            )

    result = conn.execute(text("SELECT * FROM users"))
    rows = result.fetchall()
    rows_as_dicts = [dict(row._asdict()) for row in rows]
    print(rows_as_dicts)
  
#####
