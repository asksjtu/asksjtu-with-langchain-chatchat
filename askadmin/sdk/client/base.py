from httpx import Client as HttpxClient
import session

Session = session.Session


class BaseClient:
    _session: Session
    base_url: str

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
        self._session = Session(base_url=base_url)

    def get(self, *args, **kwargs):
        return self._session.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        return self._session.post(*args, **kwargs)

    def login(self, username: str, password: str):
        return self._session.login(username=username, password=password)

    @property
    def session(self):
        return self._session


if __name__ == '__main__':
    client = BaseClient('http://127.0.0.1:8000/')
    resp = client.login('admin', 'password')
    print(resp)
    print('==> requesting /me')
    resp = client.get('/auth/me')
    print(resp)
    print(resp.content)