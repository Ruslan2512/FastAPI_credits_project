from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQL_DB_URL = "mysql+pymysql://root:1234@localhost:3306/credits_db"

engine = create_engine(SQL_DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#docker run --name my-mysql-db -e MYSQL_ROOT_PASSWORD=1234 -e MYSQL_DATABASE=credits_db -p 3306:3306 -d mysql:latest