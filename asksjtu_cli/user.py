"""
User Management CLI Module
"""

import click
import rich
import uuid
from rich.table import Table
from rich.prompt import Prompt

from typing import Optional, List
from asksjtu_cli.base import asksjtu
from askadmin.db.models import User, KnowledgeBase


@asksjtu.group()
def user():
    pass


def display_user(
    users: List[User], title: str = "User Info", with_password: bool = False
):
    table = Table(title=title)
    # add columns
    table.add_column("Username")
    table.add_column("Name")
    table.add_column("Role")
    table.add_column("Knowledge Base")
    if with_password:
        table.add_column("Password (hashed)")
    # add rows
    for u in users:
        kb_names = ",".join([kb.name for kb in u.kbs]) or "(None)"
        row = [u.username, u.name, u.role, kb_names]
        if with_password:
            table.add_row(*row, u.password)
        else:
            table.add_row(*row)
    return table


@user.command()
@click.option("--with-password", is_flag=True, default=False)
def list(with_password: bool = False):
    users = [u for u in User.select()]
    # create table with rich
    table = display_user(users, with_password=with_password)
    rich.print(table)


@user.command()
@click.option("--username", type=str)
@click.option("--name", type=str)
@click.option(
    "--role",
    type=click.Choice((User.ROLE_ADMIN, User.ROLE_USER), case_sensitive=False),
    default=User.ROLE_USER,
)
@click.option(
    "--random-password",
    is_flag=True,
    default=False,
    help="Generate random password for user",
)
def create(
    username: str,
    name: Optional[str] = None,
    role: Optional[str] = User.ROLE_USER,
    random_password: bool = False,
):
    # check username
    if not username:
        username = Prompt.ask("Enter your username")
    if User.get_or_none(User.username == username):
        rich.print("[red]username already exists[/red]")
        return
    # check password
    if random_password:
        password = str(uuid.uuid4())
        # rich print bold password
        rich.print(f"[yellow]Your password is [b]{password}[/b][/yellow]")
    else:
        password = Prompt.ask("Enter your password", password=True)
        confirm_password = Prompt.ask("Confirm your password", password=True)
        if password != confirm_password:
            rich.print("[red]password not match[/red]")
            return
    # create user
    user = User.create(
        username=username, password=User.hash_password(password), name=name, role=role
    )
    if user is None:
        rich.print("[red]Failed[/red]")
        return
    else:
        rich.print("[green]Success[/green]")
        display_user([user], title="Created User Info", with_password=True)
        return


@user.command()
@click.option("--username", type=str, required=True)
def reset_password(username: str):
    user = User.get_or_none(User.username == username)
    if not user:
        rich.print("[red]user not found[/red]")
        return
    # get new password
    password = Prompt.ask("Enter your password", password=True)
    confirm_password = Prompt.ask("Confirm your password", password=True)
    if password != confirm_password:
        rich.print("[red]password not match[/red]")
        return
    # reset and print out result
    user.password = User.hash_password(password)
    user.save()
    display_user([user], title="Updated User Info", with_password=True)


@user.command()
@click.option("--username", type=str, required=True)
@click.option("--name", type=str)
@click.option(
    "--role",
    type=click.Choice((User.ROLE_ADMIN, User.ROLE_USER), case_sensitive=False),
)
def update(username: str, name: Optional[str] = None, role: Optional[str] = None):
    user = User.get_or_none(User.username == username)
    if not user:
        rich.print("[red]user not found[/red]")
        return
    if name is not None:
        user.name = name
    if role is not None:
        user.role = role
    user.save()
    # display updated info
    display_user([user], title="Updated User Info")


@user.command()
@click.option("--username", type=str, required=True)
@click.option("--kb-name", type=str, required=True)
def add_kb(username: str, kb_name: str):
    user = User.get_or_none(User.username == username)
    if not user:
        rich.print("[red]user not found[/red]")
        return
    kb = KnowledgeBase.get_or_none(KnowledgeBase.name == kb_name)
    if not kb:
        rich.print("[red]knowledge base not found[/red]")
        return
    user.kbs.add(kb)


@user.command()
@click.option("--username", type=str, required=True)
@click.option("--kb-name", type=str, required=True)
def remove_kb(username: str, kb_name: str):
    # get user
    user = User.get_or_none(User.username == username)
    if not user:
        rich.print("[red]user not found[/red]")
        return
    # get kb
    kb = KnowledgeBase.get_or_none(KnowledgeBase.name == kb_name)
    if not kb:
        rich.print("[red]knowledge base not found[/red]")
        return
    user.kbs.remove(kb)
