from sqlalchemy import create_engine

engine = None

def init_db(db_conf):
    global engine
    engine = create_engine(db_conf["url"], echo=db_conf["echo"])