from typing import Dict
from askadmin.sdk.client.base import BaseClient


class KBMixin(BaseClient):

    def list_kb(self):
        resp = self._session.get("/kb/")
        return resp.json()

    def get_kb(self, pk: str):
        resp = self._session.get(f"/kb/{pk}")
        return resp.json()

    def create_kb(self, data: Dict):
        resp = self._session.post("/kb/", data=data)
        return resp.json()

    def delete_kb(self, pk: str):
        resp = self._session.request("DELETE", f"/kb/{pk}")
        return resp.content

    def update_kb(self, pk: str, updated_kb: Dict):
        resp = self._session.request("PUT", f"/kb/{pk}", json=updated_kb)
        return resp.json()
