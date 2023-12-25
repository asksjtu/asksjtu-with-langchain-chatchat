from playhouse.migrate import SqliteMigrator, migrate as db_migrate
import peewee as pw

from askadmin.db.base import db as database

migrator = SqliteMigrator(database)


def migrate():
    with database.atomic():
        db_migrate(
            migrator.add_column(
                "qa",
                "popular",
                pw.BooleanField(default=False),
            ),
            migrator.add_column(
                "qa",
                "popular_rank",
                pw.IntegerField(default=0),
            ),
        )


def rollback():
    with database.atomic():
        db_migrate(
            migrator.drop_column("qa", "popular_rank"),
            migrator.drop_column("qa", "popular"),
        )
