from typing import Optional
import hashlib

from configs.asksjtu_config import SALT


def kb_name_to_hash(name: str, salt: Optional[str] = None):
    """
    hash (name + salt) and return the hash value in hex
    """
    if salt is None:
        salt = SALT
    return hashlib.sha256((name + salt).encode()).hexdigest()
