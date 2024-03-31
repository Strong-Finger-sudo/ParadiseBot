from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER, TEST_DB_HOST, TEST_DB_NAME, TEST_DB_PASS, TEST_DB_PORT,\
				   TEST_DB_USER

DATABASE_URL = f"postgresql+psycopg2://{TEST_DB_USER}:{TEST_DB_PASS}@{TEST_DB_HOST}:{TEST_DB_PORT}/{TEST_DB_NAME}"
Base = declarative_base()

metadata = MetaData()

engine = create_engine(DATABASE_URL)
Session = sessionmaker(engine, expire_on_commit=False)