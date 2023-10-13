"""
User Management CLI Module
"""

import click
import rich
from rich.table import Table
from rich.prompt import Prompt

from typing import Optional, List, Dict
from asksjtu_cli.base import asksjtu
from askadmin.manager import UserManager, KBManager

manager = UserManager()
kb_manager = KBManager()


@asksjtu.group()
def user():
    pass


def display_user(users: List[Dict], title: str = "User Info"):
    with_password = any("password" in u for u in users)
    table = Table(title=title)
    # add columns
    table.add_column("Username")
    table.add_column("Name")
    if with_password:
        table.add_column("Password (hashed)")
    # add rows
    for u in users:
        if with_password:
            table.add_row(
                u.get("username", ""), u.get("name", ""), u.get("password", "")
            )
        else:
            table.add_row(u.get("username", ""), u.get("name", ""))
    return table


@user.command()
@click.option("--with-password", is_flag=True, default=False)
def list(with_password: bool = False):
    users = manager.list()
    for user in users:
        if not with_password:
            del user["password"]
    # create table with rich
    table = display_user(users)
    rich.print(table)


@user.command()
@click.option("--username", type=str, required=True)
@click.option("--name", type=str)
@click.option(
    "--role",
    type=click.Choice(
        (UserManager.ROLE_ADMIN, UserManager.ROLE_USER), case_sensitive=False
    ),
    default=UserManager.ROLE_USER,
)
def create(
    username: str,
    name: Optional[str] = None,
    role: Optional[str] = UserManager.ROLE_USER,
):
    if not username:
        username = Prompt.ask("Enter your username", password=True)
        return
    if username in [u["username"] for u in manager.list()]:
        rich.print("[red]username already exists[/red]")
        return
    password = Prompt.ask("Enter your password", password=True)
    confirm_password = Prompt.ask("Confirm your password", password=True)
    if password != confirm_password:
        rich.print("[red]password not match[/red]")
        return
    ret = manager.create(username, password, name, role)
    if ret is None:
        rich.print("[red]Failed[/red]")
        return
    else:
        rich.print("[green]Success[/green]")
        return


@user.command()
@click.option("--username", type=str, required=True)
def reset_password(username: str):
    user = manager.get(username=username)
    if not user:
        rich.print("[red]user not found[/red]")
        return
    password = Prompt.ask("Enter your password", password=True)
    confirm_password = Prompt.ask("Confirm your password", password=True)
    if password != confirm_password:
        rich.print("[red]password not match[/red]")
        return


@user.command()
@click.option("--username", type=str, required=True)
@click.option("--name", type=str)
@click.option(
    "--role",
    type=click.Choice(
        (UserManager.ROLE_ADMIN, UserManager.ROLE_USER), case_sensitive=False
    ),
)
def update(username: str, name: Optional[str] = None, role: Optional[str] = None):
    user = manager.get(username=username)
    if not user:
        rich.print("[red]user not found[/red]")
        return
    if name is not None:
        user.update(name=name)
    if role is not None:
        user.update(role=role)


@user.command()
@click.option("--username", type=str, required=True)
@click.option("--kb-name", type=str, required=True)
def add_kb(username: str, kb_name: str):
    user = manager.get(username=username)
    if not user:
        rich.print("[red]user not found[/red]")
        return
    kb = kb_manager.get(name=kb_name)
    if not kb:
        rich.print("[red]knowledge base not found[/red]")
        return
    manager.add_kb(user_pk=user.doc_id, kb_pk=kb.doc_id)


@user.command()
@click.option("--username", type=str, required=True)
@click.option("--kb-name", type=str, required=True)
def remove_kb(username: str, kb_name: str):
    user = manager.get(username=username)
    if not user:
        rich.print("[red]user not found[/red]")
        return
    kb = kb_manager.get(name=kb_name)
    if not kb:
        rich.print("[red]knowledge base not found[/red]")
        return
    manager.remove_kb(user_pk=user.doc_id, kb_pk=kb.doc_id)
