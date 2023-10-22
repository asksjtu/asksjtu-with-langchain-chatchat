from asksjtu_cli.base import asksjtu
from glob import glob
from pathlib import Path
import os
import rich
import click


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
@click.argument("migration_id", type=int)
@click.option("--rollback", is_flag=True, default=False, help="Rollback")
def migrate(migration_id: int, rollback: bool):
    """Migrate database"""
    migration_id = str(migration_id).zfill(4)
    ASKSJTU_ROOT = Path(os.path.realpath(__file__)).parent.parent
    MNIGRATION_DIR = "askadmin/db/migrations"
    MIGREATION_MODULE = "askadmin.db.migrations"
    import importlib

    # find file
    matched_files = glob(str(ASKSJTU_ROOT / MNIGRATION_DIR / f"{migration_id}_*.py"))
    if len(matched_files) > 1:
        rich.print(f"[red]Found multiple migration files for ID {migration_id}[/red]")
        return
    elif len(matched_files) == 0:
        rich.print(f"[red]Found no migration files for ID {migration_id}[/red]")
        return
    migration_file = Path(matched_files[0]).name

    # import the file, [:-3] is to remove .py
    migration_module = importlib.import_module(
        f"{MIGREATION_MODULE}.{migration_file[:-3]}"
    )
    # reload to avoid cache
    importlib.reload(migration_module)

    if not hasattr(migration_module, "migrate"):
        raise ValueError(f"Migration file {migration_file} has no migrate function")
    if not hasattr(migration_module, "rollback"):
        raise ValueError(f"Migration file {migration_file} has no rollback function")

    if rollback:
        migration_module.rollback()
        rich.print(f"[yellow]Rollback migration {migration_id} done[/yellow]")
    else:
        migration_module.migrate()
        rich.print(f"[green]Migration {migration_id} done[/green]")

