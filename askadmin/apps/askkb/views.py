from typing import List
from django.shortcuts import get_object_or_404
from django.http.response import HttpResponseForbidden, HttpResponse
from ninja_extra import Router

from .models import KnowledgeBase
from .schema import (
    KnowledgeBaseSchema,
    KnowledgeBaseCreateSchema,
    KnowledgeBaseUpdateSchema,
)

router = Router()


@router.get("", response=List[KnowledgeBaseSchema])
def list_kb(request):
    return KnowledgeBase.objects.filter(owner=request.auth)


@router.get(
    "/{pk}",
    response=KnowledgeBaseSchema,
    tags=["kb"],
)
def get_kb(request, pk: str):
    qs = KnowledgeBase.objects.filter(owner=request.auth)
    return get_object_or_404(qs, pk=pk)


@router.post(
    "",
    response=KnowledgeBaseSchema,
    tags=["kb"],
)
def create_kb(request, new_kb: KnowledgeBaseCreateSchema):
    # only superuser can create knowledge base
    if (not request.auth) or (not request.auth.is_superuser):
        return HttpResponseForbidden("只有超级管理员可以创建新知识库")
    return KnowledgeBase.objects.create(**new_kb.dict(), owner=request.auth)


@router.delete("/{pk}")
def delete_kb(request, pk: str):
    if (not request.auth) or (not request.auth.is_superuser):
        return HttpResponseForbidden("只有超级管理员可以删除知识库")
    kb = get_object_or_404(KnowledgeBase, pk=pk)
    kb.delete()
    # return 204 no content
    return HttpResponse(status=204)


@router.put("/{pk}", response=KnowledgeBaseSchema)
def update_kb(request, pk: str, updated_kb: KnowledgeBaseUpdateSchema):
    kb = get_object_or_404(KnowledgeBase, pk=pk)
    if not request.auth.is_superuser and kb.owner != request.auth:
        return HttpResponseForbidden("只有知识库管理员可以修改知识库")

    normal_user_readonly_fields = ["name", "slug", "owner", "category"]
    if not request.auth.is_superuser:
        disallowed_fields = []
        for field in normal_user_readonly_fields:
            if getattr(updated_kb, field) != None:
                disallowed_fields.append(field)
        if len(disallowed_fields) != 0:
            return HttpResponseForbidden(
                f"{','.join(disallowed_fields)} 字段只能由超级管理员修改"
            )

    print(updated_kb.dict())

    for k, v in updated_kb.dict().items():
        if v is None:
            continue
        setattr(kb, k, v)
    kb.save()

    return kb
