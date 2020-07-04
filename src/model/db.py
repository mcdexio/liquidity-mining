from sqlalchemy import create_engine

engine = None

def connect_db(db_conf):
    global engine
    engine = create_engine(db_conf["url"], echo=db_conf["echo"])