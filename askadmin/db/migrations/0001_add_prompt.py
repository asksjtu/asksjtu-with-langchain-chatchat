from playhouse.migrate import SqliteMigrator, migrate as db_migrate
import peewee as pw

from askadmin.db.base import db as database

migrator = SqliteMigrator(database)


def migrate():
    with database.atomic():
        db_migrate(
            migrator.add_column(
                "knowledgebase",
                "prompt",
                pw.TextField(default=""),
            )
        )


def rollback():
    with database.atomic():
        db_migrate(migrator.drop_column("knowledgebase", "prompt"))
