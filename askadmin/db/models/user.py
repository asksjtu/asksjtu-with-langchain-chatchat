from peewee import ManyToManyField
from playhouse.signals import Model, pre_init
from typing import Optional
import secrets
import peewee as pw
import hashlib

from askadmin.db.base import db
from askadmin.db.models.knowledge_base import KnowledgeBase


class User(Model):
    ROLE_USER = "user"
    ROLE_ADMIN = "admin"

    name = pw.CharField(max_length=255, unique=True)
    username = pw.CharField(max_length=255, unique=True)
    password = pw.CharField(max_length=255)
    role = pw.CharField(
        max_length=255, default=ROLE_USER, choices=(ROLE_USER, ROLE_ADMIN)
    )
    kbs = ManyToManyField(KnowledgeBase, backref="users")

    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None):
        salt = salt or secrets.token_hex(16)
        hashed = hashlib.sha512(((salt or "") + password).encode()).hexdigest()
        return f"{salt}.{hashed}"

    def check_password(self, password: str) -> bool:
        chunks = self.password.split(".")
        if len(chunks) != 2:
            return False
        salt, _ = chunks
        return self.hash_password(password, salt) == self.password

    class Meta:
        database = db


@pre_init(sender=User)
def on_init(model_class, instance: User):
    if instance.name is None or instance.name == "":
        instance.name = instance.username