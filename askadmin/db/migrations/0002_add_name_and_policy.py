from playhouse.migrate import SqliteMigrator, migrate as db_migrate
import peewee as pw

from askadmin.db.base import db as database

migrator = SqliteMigrator(database)


def migrate():
    with database.atomic():
        db_migrate(
            migrator.add_column(
                "knowledgebase",
                "display_name",
                pw.CharField(max_length=255, default="交大智讯"),
            ),
            migrator.add_column(
                "knowledgebase",
                "policy",
                pw.TextField(default=""),
            ),
        )


def rollback():
    with database.atomic():
        db_migrate(
            migrator.drop_column("knowledgebase", "display_name"),
            migrator.drop_column("knowledgebase", "policy"),
        )
