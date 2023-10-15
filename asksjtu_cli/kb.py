"""
Knowledge Base Management
"""

import click
import rich
from typing import List, Optional

from askadmin.db.models import KnowledgeBase
from asksjtu_cli.base import asksjtu


@asksjtu.group()
def kb():
    pass


def display_kb(kbs: List[KnowledgeBase]):
    table = rich.table.Table(title="Knowledge Base")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Slug")
    table.add_column("Managers")
    for kb in kbs:
        user_names = (
            ", ".join([u.name for u in kb.users]) or "(None)"
        )
        table.add_row(str(kb.id), kb.name, kb.slug, user_names)
    return table


@kb.command()
def sync():
    from server.knowledge_base.kb_api import list_kbs_from_db

    # get unsync kbs
    kb_names = set(list_kbs_from_db())
    existing_kb = [kb for kb in KnowledgeBase.select()]
    existing_kb_names = set([kb.name for kb in existing_kb])
    delta = kb_names - existing_kb_names
    # sync
    new_kbs = []
    for name in delta:
        new_kbs.append(KnowledgeBase.create(name=name))
    # display result
    rich.print(f"同步完成，共同步 {len(kb_names)} 个知识库，新建 {len(new_kbs)} 个")
    if len(new_kbs) > 0:
        kbs_table = display_kb(new_kbs)
        rich.print(kbs_table)


@kb.command()
def list():
    kbs = [kb for kb in KnowledgeBase.select()]
    kbs_table = display_kb(kbs)
    rich.print(kbs_table)


@kb.command()
@click.option("--name", type=str, required=True)
@click.option("--slug", type=str, required=True)
def update(name: str, slug: str):
    if name is None:
        rich.print("[red]请指定知识库名称[/red]")
        return
    kb = KnowledgeBase.get_or_none(name=name)
    if kb is None:
        rich.print("[red]未找到指定知识库[/red]")
        return
    if len(slug) == 0:
        rich.print("[red]Slug 不能为空[/red]")
        return
    if slug is not None:
        kb.slug = slug
    kb.save()
    rich.print("[green]更新成功[/green]")
    kbs_table = display_kb([kb])
    rich.print(kbs_table)
