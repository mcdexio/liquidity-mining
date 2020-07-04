from sqlalchemy import create_engine


def connect_db(db_conf):
    return create_engine(db_conf["url"], echo=db_conf["echo"])