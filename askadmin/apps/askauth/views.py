from ninja.orm import create_schema
from ninja_extra import Router
from ninja_jwt.authentication import JWTAuth
from .models import User

router = Router()


UserSchema = create_schema(User, fields=["username", "name", "is_superuser"])

@router.get("/me", tags=["auth"], auth=JWTAuth())
def me(request):
    return UserSchema.from_orm(request.auth)
