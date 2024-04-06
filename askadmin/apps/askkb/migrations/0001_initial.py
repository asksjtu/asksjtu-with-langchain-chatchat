# Generated by Django 5.0.4 on 2024-04-05 18:21

import askadmin.apps.askkb.models
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="KnowledgeBase",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=255, verbose_name="名称")),
                (
                    "slug",
                    models.CharField(
                        default=askadmin.apps.askkb.models.default_slug,
                        max_length=255,
                        unique=True,
                        verbose_name="标记",
                    ),
                ),
                (
                    "welcome_message",
                    models.TextField(blank=True, default="", verbose_name="欢迎消息"),
                ),
                ("prompt", models.TextField(verbose_name="语言模型指令")),
                ("policy", models.TextField(verbose_name="使用政策")),
                (
                    "category",
                    models.CharField(
                        choices=[("kb", "知识库"), ("qa", "问答库")],
                        default="kb",
                        max_length=255,
                        verbose_name="类型",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="管理者",
                    ),
                ),
            ],
            options={
                "verbose_name": "知识库",
                "verbose_name_plural": "知识库",
            },
        ),
        migrations.CreateModel(
            name="KnowledgeBaseSnippet",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "source",
                    models.CharField(blank=True, max_length=511, verbose_name="片段来源"),
                ),
                (
                    "doc_id",
                    models.CharField(
                        max_length=255, null=True, unique=True, verbose_name="向量库片段 ID"
                    ),
                ),
                (
                    "category",
                    models.CharField(
                        choices=[("raw", "知识片段"), ("qa", "问答对")],
                        max_length=255,
                        verbose_name="类别",
                    ),
                ),
                ("raw_content", models.TextField(verbose_name="原始内容")),
                (
                    "kb",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="snippets",
                        to="askkb.knowledgebase",
                    ),
                ),
            ],
            options={
                "verbose_name": "知识库片段",
                "verbose_name_plural": "知识库片段",
            },
        ),
    ]
