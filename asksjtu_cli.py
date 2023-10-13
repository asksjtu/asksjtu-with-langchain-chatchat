import click

from asksjtu_cli.base import asksjtu

# CLI Module
from asksjtu_cli.user import *  # handles `user` subcommand
from asksjtu_cli.kb import *  # handles `kb` subcommand


@asksjtu.command()
@click.option("--kb-name", type=str, required=True, default="常用知识库")
def update_stu_noti_handler(kb_name: str):
    from server.knowledge_base.kb_api import list_kbs
    from asksjtu_cli.update_stu_noti import update_stu_noti

    kbs = list_kbs().data
    if kb_name not in kbs:
        kbs_str = ", ".join(kbs)
        raise ValueError(f"知识库 {kb_name} 不存在，可用知识库：{kbs_str}")
    return update_stu_noti(kb_name=kb_name)


if __name__ == "__main__":
    asksjtu()
