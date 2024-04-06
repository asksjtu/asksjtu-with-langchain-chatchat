from django.db import models
from django.contrib.auth import get_user_model
from typing import Union, Dict
import uuid
import json


def default_slug():
    return str(uuid.uuid4())


class KnowledgeBase(models.Model):
    CAT_KB = "kb"
    CAT_QA = "qa"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name="名称")
    slug = models.CharField(
        max_length=255,
        unique=True,
        default=default_slug,
        verbose_name="标记",
    )
    owner = models.ForeignKey(
        get_user_model(), null=True, on_delete=models.SET_NULL, verbose_name="管理者"
    )
    # kb configurations
    welcome_message = models.TextField(default="", blank=True, verbose_name="欢迎消息")
    prompt = models.TextField(verbose_name="语言模型指令")
    policy = models.TextField(verbose_name="使用政策")
    category = models.CharField(
        max_length=255,
        choices=[
            (CAT_KB, "知识库"),
            (CAT_QA, "问答库"),
        ],
        default="kb",
        verbose_name="类型",
    )

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{self.name} ({self.pk})"

    class Meta:
        verbose_name = "知识库"
        verbose_name_plural = "知识库"


class KnowledgeBaseSnippet(models.Model):
    CAT_RAW = "raw"
    CAT_QA = "qa"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kb = models.ForeignKey(
        KnowledgeBase, related_name="snippets", on_delete=models.CASCADE
    )
    # source is the name of file the snippet is from
    source = models.CharField(max_length=511, blank=True, verbose_name='片段来源')
    # doc_id is the id in vector store
    doc_id = models.CharField(max_length=255, unique=True, null=True, verbose_name='向量库片段 ID')
    # category
    category = models.CharField(
        max_length=255,
        choices=[
            (CAT_RAW, "知识片段"),
            (CAT_QA, "问答对"),
        ],
        verbose_name='类别'
    )
    # content
    raw_content = models.TextField('原始内容')

    @property
    def content(self):
        if self.category == self.CAT_RAW:
            return self.raw_content
        else:
            return json.loads(self.raw_content)

    @content.setter
    def content(self, new_content: Union[str, Dict]):
        if self.category == self.CAT_RAW:
            self.content = new_content
        else:
            self.content = json.dumps(new_content)
        return self.content

    class Meta:
        verbose_name = "知识库片段"
        verbose_name_plural = "知识库片段"
