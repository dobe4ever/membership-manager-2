from sqlalchemy import create_engine
import os

db = os.environ['DB_CONNECTION_STRING']

engine = create_engine(db, connect_args={
  "ssl": {
    "ssl_ca": "/etc/ssl/cert.pem"
  }
})


