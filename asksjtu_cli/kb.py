"""
Knowledge Base Management
"""

import click
import rich
from typing import List
from tinydb.table import Document

from askadmin.manager import KBManager
from asksjtu_cli.base import asksjtu

manager = KBManager()


@asksjtu.group()
def kb():
    pass


def display_kb(kbs: List[Document]):
    table = rich.table.Table(title="Knowledge Base")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Slug")
    for kb in kbs:
        table.add_row(str(kb.doc_id), kb.get("name"), kb.get("slug"))
    return table


@kb.command()
def sync():
    from server.knowledge_base.kb_api import list_kbs_from_db

    # get unsync kbs
    kb_names = set(list_kbs_from_db())
    existing_kb = manager.list()
    existing_kb_names = set([kb.get("name") for kb in existing_kb])
    delta = kb_names - existing_kb_names
    # sync
    doc_ids = []
    for name in delta:
        doc_id = manager.create(name=name)
        doc_ids.append(doc_id)
    # display result
    rich.print(f"同步完成，共同步 {len(kb_names)} 个知识库，新建 {len(doc_ids)} 个")
    sync_kbs = manager.get(kb_pk__in=doc_ids)
    if sync_kbs:
        kbs_table = display_kb(sync_kbs)
        rich.print(kbs_table)
