import typing as t
from knappe.auth import Source
from knappe.types import Request, User, UserId


class Credentials(t.TypedDict):
    username: str
    password: str


class UserObject(User):

    def __init__(self, userid: UserId):
        self.id = userid


class DictSource(Source[Request, Credentials]):

    def __init__(self, users: t.Mapping[str, str]):
        self.users = users

    def find(self, credentials: Credentials, request: Request
             ) -> t.Optional[User]:
        username = credentials['username']
        password = credentials['password']
        if username in self.users:
            if self.users[username] == password:
                return UserObject(username)
        return None

    def fetch(self, uid, request) -> t.Optional[User]:
        if uid in self.users:
            return UserObject(uid)
        return None
