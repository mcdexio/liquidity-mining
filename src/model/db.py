from sqlalchemy import create_engine
import config

db_engine = create_engine(config.DB_URL, echo=config.DB_ECHO)
DB_SESSION = sessionmaker(bind=db_engine)
