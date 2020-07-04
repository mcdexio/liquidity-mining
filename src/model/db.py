from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import config

db_engine = create_engine(config.DB_URL, echo=config.DB_ECHO)
DBSession = sessionmaker(bind=db_engine)
