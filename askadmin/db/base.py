from peewee import SqliteDatabase
from configs.asksjtu_config import ADMIN_DB

db = SqliteDatabase(ADMIN_DB)
