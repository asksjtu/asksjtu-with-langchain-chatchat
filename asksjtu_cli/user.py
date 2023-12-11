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
from asksjtu_cli.kb import display_kb
from asksjtu_cli.qa import display_qa_collection
from askadmin.db.models import User, KnowledgeBase, QACollection


@asksjtu.group()
def user():
    pass


def display_user(user: User, with_password: bool = False) -> Table:
    table = Table(title=user.name)
    table.add_column("Field")
    table.add_column("Value")
    # add rows
    table.add_row("Username", user.username)
    table.add_row("Name", user.name)
    table.add_row("Role", user.role)

    # show managed kbs
    if len(user.kbs) > 0:
        table.add_row("Knowledge Base", "")
        table.add_row("", display_kb(user.kbs))

    # show managed qas
    if len(user.qas) > 0:
        table.add_row("Q&A Collection", "")
        table.add_row("", display_qa_collection(user.qas))

    return table


def display_users(
    users: List[User], title: str = "User Info", with_password: bool = False
):
    table = Table(title=title)
    # add columns
    table.add_column("Username")
    table.add_column("Name")
    table.add_column("Role")
    if with_password:
        table.add_column("Password (hashed)")
    # add rows
    for u in users:
        row = [u.username, u.name, u.role]
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
    table = display_users(users, with_password=with_password)
    rich.print(table)


@user.command()
@click.argument("username", type=str)
def show(username: str):
    user = User.get_or_none(User.name == username)
    if not user:
        rich.print("[red]user not found[/red]")
        return
    table = display_user(user)
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
        display_users([user], title="Created User Info", with_password=True)
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
    display_users([user], title="Updated User Info", with_password=True)


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
    display_user(user)


@user.command()
@click.option("--username", type=str, required=True)
@click.option("--kb-name", type=str, required=True)
def add_kb(username: str, kb_name: str):
    """
    Add user as the manager of the knowledge base
    """
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
    """
    Remove user from managers of the knowledge base
    """
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


@user.command()
@click.option("--username", type=str, required=True)
@click.option("--qa-name", type=str, required=True)
def add_qa(username: str, qa_name: str):
    """
    Add user as the manager of the QA collection
    """
    user = User.get_or_none(User.username == username)
    if not user:
        rich.print("[red]user not found[/red]")
        return
    qa = QACollection.get_or_none(QACollection.name == qa_name)
    if not qa:
        rich.print("[red]knowledge base not found[/red]")
        return
    user.qas.add(qa)


@user.command()
@click.option("--username", type=str, required=True)
@click.option("--qa-name", type=str, required=True)
def remove_qa(username: str, qa_name: str):
    """
    Remove user from managers of the QA collection
    """
    # get user
    user = User.get_or_none(User.username == username)
    if not user:
        rich.print("[red]user not found[/red]")
        return
    # get qa
    qa = QACollection.get_or_none(QACollection.name == qa_name)
    if not qa:
        rich.print("[red]knowledge base not found[/red]")
        return
    user.qas.remove(qa)
