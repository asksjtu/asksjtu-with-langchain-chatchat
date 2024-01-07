from playhouse.signals import Model, pre_init
import peewee as pw

from askadmin.db.base import db
from askadmin.utils import kb_name_to_hash


class KnowledgeBase(Model):
    name = pw.CharField(max_length=255, unique=True)
    slug = pw.CharField(max_length=255, unique=True)
    welcome_message = pw.TextField(default="")
    prompt = pw.TextField(default="")
    display_name = pw.CharField(max_length=255, default="北师大小助手")
    policy = pw.TextField(default="")

    class Meta:
        database = db


@pre_init(sender=KnowledgeBase)
def on_init(model_class, instance: KnowledgeBase):
    if (instance.slug == "" or instance.slug is None) and (
        instance.name != None and instance.name != ""
    ):
        instance.slug = kb_name_to_hash(instance.name)