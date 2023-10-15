from asksjtu_cli.base import asksjtu
import rich


@asksjtu.group()
def db():
    """Database related commands."""
    pass


@db.command()
def create():
    """Create database."""
    from askadmin.db import models
    from askadmin.db.base import db as database

    UserKnowledgeBase = models.User.kbs.get_through_model()
    database.create_tables(
        [
            models.User,
            models.KnowledgeBase,
            UserKnowledgeBase,
        ]
    )


@db.command()
def migrate():
    """Migrate database"""
    rich.print("[red]Not implemented yet.[/red]")
