import argparse


from server.knowledge_base.kb_api import list_kbs
from asksjtu_cli.update_xstz import update_xstz


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--kb-name', default='常用数据库')
    return parser.parse_args()


def update_xstz_handler(kb_name: str):
    kbs = list_kbs().data
    print(kbs)
    if kb_name not in kbs:
        raise ValueError(f"知识库 {kb_name} 不存在")
    return update_xstz(kb_name=kb_name)


if __name__ == '__main__':
    args = parse_args()
    update_xstz_handler(args.kb_name)
