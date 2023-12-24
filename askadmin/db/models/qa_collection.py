from playhouse.signals import Model, pre_init
import peewee as pw

from askadmin.db.base import db
from askadmin.utils import kb_name_to_hash


class QACollection(Model):
    """
    A QA collection is a model with related QA records
    """
    # name of KnowledgeBase in langchain-chatchat
    name = pw.CharField(max_length=255)
    slug = pw.CharField(max_length=255, unique=True)
    # TODO: display `display_name` instead of name in webui
    display_name = pw.CharField(max_length=255, default="")

    class Meta:
        database = db


@pre_init(sender=QACollection)
def on_init(model_class, instance: QACollection):
    if (instance.slug == "" or instance.slug is None) and (
        instance.name != None and instance.name != ""
    ):
        instance.slug = kb_name_to_hash(instance.name)


class QA(Model):
    """
    A single question and its answer, with keywords and alias
    """
    doc_id = pw.CharField(max_length=255, unique=True, null=True)
    collection = pw.ForeignKeyField(QACollection, backref="questions", on_delete="CASCADE")
    source = pw.TextField()
    question = pw.TextField()
    answer = pw.TextField()
    alias = pw.TextField(default="")
    vectorized = pw.BooleanField(default=False)

    class Meta:
        database = db


class QAAnalytics(Model):
    qa = pw.ForeignKeyField(QA, backref="analytics")
    query = pw.TextField()  # user's query
    rank = pw.IntegerField()  # rank of this QA in the search result
    top_k = pw.IntegerField()  # top_k used in the search
    score = pw.FloatField()  # score of this QA in the search result
    timestamp = pw.DateTimeField()  # timestamp of this query

    class Meta:
        database = db
