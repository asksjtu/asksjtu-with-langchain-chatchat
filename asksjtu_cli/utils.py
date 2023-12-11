from server.knowledge_base.kb_service.base import KBServiceFactory


def remove_kb(kb_name: str):
    """
    Post a delete request to langchain-chatchat FastAPI backend to remove kb
    in the system.
    """
    kb = KBServiceFactory.get_service_by_name(kb_name)
    if not kb:
        raise ValueError(f"Knowledge Base with name `{kb_name}` does not exist in system db")
    return kb.drop_kb()
