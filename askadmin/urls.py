from django.contrib import admin
from django.urls import path, include
from ninja_extra import NinjaExtraAPI, api_controller
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.controller import NinjaJWTDefaultController

from askadmin.apps.askkb.views import router as askKBRouter
from askadmin.apps.askauth.views import router as askAuthRouter


api = NinjaExtraAPI(auth=JWTAuth())
api.register_controllers(
    api_controller("/auth/token", tags=["auth"], auth=None)(NinjaJWTDefaultController)
)
api.add_router("/kb/", askKBRouter)
api.add_router("/auth/", askAuthRouter)

urlpatterns = [
    path("", api.urls),
    path("admin/", admin.site.urls),
]
