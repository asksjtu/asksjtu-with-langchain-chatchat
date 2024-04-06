from ninja.orm import ModelSchema
from typing import List, Optional
from pydantic import Field
from .models import KnowledgeBase, KnowledgeBaseSnippet


class KnowledgeBaseSnippetSchema(ModelSchema):
    content: str

    class Meta:
        model = KnowledgeBaseSnippet
        fields = ["id", "kb", "source", "doc_id", "category"]

    @staticmethod
    def resolve_content(obj: KnowledgeBaseSnippet):
        return obj.content


class KnowledgeBaseSchema(ModelSchema):
    snippets: List[KnowledgeBaseSnippetSchema]

    class Meta:
        model = KnowledgeBase
        fields = [
            "id",
            "name",
            "slug",
            "owner",
            "welcome_message",
            "prompt",
            "policy",
            "category",
        ]

    @staticmethod
    def resolve_snippets(obj: KnowledgeBase):
        return obj.snippets


class KnowledgeBaseCreateSchema(ModelSchema):
    slug: Optional[str] = Field(None, max_length=255)
    class Meta:
        model = KnowledgeBase
        fields = ['name', 'welcome_message', 'prompt', 'policy', 'category']
        fields_optional = ['slug', 'welcome_message', 'prompt', 'policy', 'category']


class KnowledgeBaseUpdateSchema(ModelSchema):
    slug: Optional[str] = Field(None, max_length=255)
    class Meta:
        model = KnowledgeBase
        fields = ['name', 'welcome_message', 'prompt', 'policy', 'category']
        fields_optional = '__all__' 
