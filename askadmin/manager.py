from typing import Optional, List
from tinydb import Query
import hashlib

from askadmin import db
from configs.asksjtu_config import SALT

__all__ = ["UserManager", "KBManager"]


class KBManager:
    """
    class KB:
        - name: kb_name
        - slug: kb_slug
    """

    def list(self):
        return db.kb.all()

    def create(self, name: str, slug: Optional[str] = None):
        if slug is None:
            slug = self.name_to_hash(name)
        return db.kb.insert(dict(name=name, slug=slug))

    def get(
        self,
        kb_pk: Optional[int] = None,
        kb_pk__in: Optional[List[int]] = None,
        name: Optional[str] = None,
        slug: Optional[str] = None,
    ):
        if kb_pk:
            return db.kb.get(doc_id=kb_pk)
        if kb_pk__in:
            return db.kb.get(doc_ids=kb_pk__in)
        return db.kb.get(Query().name == name) or db.kb.get(Query().slug == slug)

    @staticmethod
    def name_to_hash(name: str, salt: Optional[str] = None):
        if salt is None:
            salt = SALT
        return hashlib.sha256((name + salt).encode("utf-8")).hexdigest()


class UserManager:
    """
    class User:
        - username: username
        - password: hashed password
        - kbs: id of managaed kbs
        - name: the display name of user
    """

    ROLE_ADMIN = "admin"
    ROLE_USER = "user"

    def create(
        self,
        username: str,
        password: str,
        name: Optional[str] = None,
        role: Optional[str] = ROLE_USER,
    ):
        password = self.hash_password(password)
        if not name:
            name = username
        return db.user.insert(
            dict(username=username, password=password, name=name, role=role, kbs=[])
        )

    def check_password(self, username: str, password: str):
        """
        Check if the given password and the password in database is matched
        """
        user = db.user.get(Query().username == username)
        return user.get("password") == self.hash_password(password)

    def list(self):
        return db.user.all()

    def get(
        self,
        pk: Optional[int] = None,
        username: Optional[str] = None,
    ):
        """
        Return first of user found
        """
        if username:
            return db.user.get(Query().username == username, doc_id=pk)
        else:
            return db.user.get(doc_id=pk)

    def add_kb(self, user_pk: int, kb_pk: int, skip_check: bool = False):
        """
        Add knowledge management permission to user

        - The existance of kb_pk will be verified if skip_check is False
        """
        # check the existance of kb_pk
        if not skip_check:
            kbs = KBManager().list()
            if kb_pk not in [kb.get("id") for kb in kbs]:
                raise ValueError("Knowledge Base not found")
        # do update
        user = self.get(pk=user_pk)
        user_kbs = user.get("kbs") or []
        return db.user.update(dict(kbs=user_kbs + [kb_pk]))

    def remove_kb(self, user_pk: int, kb_pk: int, skip_check: bool = False):
        """
        Remove knowledge management permission from user
        """
        user = self.get(pk=user_pk)
        user_kbs = user.get("kbs") or []
        if not skip_check and kb_pk not in user_kbs:
            raise ValueError("Knowledge Base not found")
        user_kbs.remove(kb_pk)
        return db.user.update(dict(kbs=user_kbs))

    def has_kb_permission(self, user_pk: int, kb_pk: int):
        user = self.get(pk=user_pk)
        if user.get("role") == self.ROLE_ADMIN:
            return True
        user_kbs = user.get("kbs") or []
        return kb_pk in user_kbs

    @staticmethod
    def hash_password(password: str):
        return hashlib.sha256(password.encode("utf-8")).hexdigest()
