"""
Knowledge Base Management
"""

import click
import rich
from typing import List, Optional

from askadmin.db.models import KnowledgeBase, QACollection, QA
from asksjtu_cli.base import asksjtu


@asksjtu.group()
def qa():
    pass


def display_qa_collection(collections: List[QACollection]):
    table = rich.table.Table(title="Knowledge Base")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Display Name")
    table.add_column("Slug")
    table.add_column("Managers")
    for c in collections:
        managers = (
            ", ".join([u.name for u in c.users]) or "(None)"
        )
        table.add_row(str(c.id), c.name, c.display_name, c.slug, managers)
    return table


@qa.command()
def list():
    collections = [collection for collection in QACollection.select()]
    table = display_qa_collection(collections)
    rich.print(table)


@qa.command()
@click.option("--name", type=str, required=True)
@click.option("--slug", type=str, required=True)
def update(name: str, slug: str):
    if name is None:
        rich.print("[red]请指定问答库名称[/red]")
        return
    collection = QACollection.get_or_none(name=name)
    if collection is None:
        rich.print("[red]未找到指定问答库[/red]")
        return
    if len(slug) == 0:
        rich.print("[red]Slug 不能为空[/red]")
        return
    if slug is not None:
        collection.slug = slug
    collection.save()
    rich.print("[green]更新成功[/green]")
    table = display_qa_collection([collection])
    rich.print(table)
