from sqlalchemy import create_engine

from kalanfa.core.content.utils.sqlalchemybridge import get_default_db_string
from kalanfa.core.content.utils.sqlalchemybridge import SharingPool


def django_connection_engine():
    if get_default_db_string().startswith("sqlite"):
        return create_engine(get_default_db_string(), poolclass=SharingPool)
    return create_engine(get_default_db_string(), pool_pre_ping=True)
