from ninja.orm import create_schema
from ninja_extra import NinjaExtraAPI
from ninja_jwt.controller import NinjaJWTDefaultController
from ninja_jwt.authentication import JWTAuth
from .models import User

api = NinjaExtraAPI()
api.register_controllers(NinjaJWTDefaultController)


UserSchema = create_schema(User, fields=["username", "name", "is_superuser"])

@api.get("/me", tags=["auth"], auth=JWTAuth())
def me(request):
    return UserSchema.from_orm(request.auth)
