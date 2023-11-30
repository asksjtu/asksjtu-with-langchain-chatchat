from playhouse.signals import Model, pre_init
import peewee as pw

from askadmin.db.base import db
from askadmin.db.models.knowledge_base import KnowledgeBase


class QACollection(Model):
    """
    A collection is QAs from a single CSV file
    """
    source = pw.TextField()
    name = pw.CharField(max_length=255)
    kb = pw.ForeignKeyField(KnowledgeBase, backref="collections")

    class Meta:
        database = db


class QA(Model):
    """
    A single question and its answer, with keywords and alias
    """
    collection_id = pw.ForeignKeyField(QACollection, backref="questions")
    question = pw.TextField()
    answer = pw.TextField()
    alias = pw.TextField(default="")
    vectorized = pw.BooleanField(default=False)

    class Meta:
        database = db
