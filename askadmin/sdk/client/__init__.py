from askadmin.sdk.client.base import BaseClient
from askadmin.sdk.client.kb import KBMixin
# from .kb import KBMixin


class Client(KBMixin):
    pass


if __name__ == "__main__":
    client = Client("http://127.0.0.1:8000/")
    print("==> Logging in...")
    resp = client.login("admin", "password")
    print("=== DONE.")

    print("==> requesting /me")
    resp = client.get("/auth/me")
    print(resp.content)
    print("=== DONE.")

    print("==> creating kb")
    kb = client.create_kb(dict(name="testkb"))
    print(kb)
    print("=== DONE.")

    print("==> listing kb")
    kbs = client.list_kb()
    print(kbs)
    print("=== DONE.")

    print("==> update kb")
    resp = client.update_kb(kb["id"], dict(name='testtest', slug='testtestt'))
    print(resp)
    print("=== DONE.")

    print("==> delete kb")
    resp = client.delete_kb(pk=kb["id"])
    print(resp)
    print("=== DONE.")

    print("==> listing kb")
    resp = client.list_kb()
    print(resp)
    print("=== DONE.")
