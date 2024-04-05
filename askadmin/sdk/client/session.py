import httpx

from typing import Dict, List, Union, Optional, Literal

PostDataType = Union[Dict, List]


class BaseSession:

    def get(self, url, *args, **kwargs):
        pass

    def post(self, url, *args, **kwargs):
        pass


class Session(BaseSession):

    _client: httpx.Client
    _token: Dict[Literal['access', 'refresh'], str] = {
        'access': '',
        'refresh': '',
    }

    def __init__(self, base_url: str) -> None:
        super().__init__()
        self._client = httpx.Client(base_url=base_url)
        self._base_url = base_url

    def request(
        self, method: str, url: str, *, with_credentials: bool = True, **kwargs
    ):
        headers = {}
        if self._token['access'] and with_credentials:
            headers['Authorization'] = f'Bearer {self._token["access"]}'

        headers = {**headers, **kwargs.get('headers', {})}
        resp = self._client.request(method, url, headers=headers, **kwargs)
        resp.raise_for_status()
        return resp

    def get(self, url: str, *, with_credentials: bool = True, **kwargs):
        return self.request("GET", url, with_credentials=with_credentials, **kwargs)

    def post(
        self,
        url: str,
        data: Optional[PostDataType] = None,
        *,
        with_credentials: bool = True,
        **kwargs
    ):
        return self.request(
            "POST", url, with_credentials=with_credentials, json=data, **kwargs
        )

    def login(self, username: str, password: str):
        resp = self.post('/auth/token/pair', {
            'username': username,
            'password': password,
        }, with_credentials=False)
        # resp
        data: Dict[Literal['username', 'access', 'refresh'], str] = resp.json()
        self._token['access'] = data['access']
        self._token['refresh'] = data['refresh']
        return data

    def refresh(self):
        resp = self.post('/auth/token/refresh', {
            'refresh': self._token['refresh'],
        }, with_credentials=False)
        # resp
        data: Dict[Literal['access', 'refresh'], str] = resp.json()
        self._token['access'] = data['access']
        self._token['refresh'] = data['refresh']
        return data

    def logout(self):
        self._token['access'] = ''
        self._token['refresh'] = ''

    @property
    def base_url(self):
        return self._client.base_url
