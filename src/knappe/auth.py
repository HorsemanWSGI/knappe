import abc
import typing as t
from knappe.types import RqT, User, UserId
from knappe.request import WSGIRequest


Credentials = t.TypeVar('Credentials')


class Source(t.Generic[RqT, Credentials], abc.ABC):

    @abc.abstractmethod
    def find(self,
             credentials: Credentials, request: RqT) -> t.Optional[User]:
        pass

    @abc.abstractmethod
    def fetch(self, uid: UserId, request: RqT) -> t.Optional[User]:
        pass


class Authenticator(t.Generic[RqT, Credentials], abc.ABC):

    sources: t.Iterable[Source[RqT, Credentials]]

    def __init__(self, sources: t.Iterable[Source[RqT, Credentials]]):
        self.sources = sources

    def from_credentials(self,request: RqT, credentials: Credentials
                         ) -> t.Optional[User]:
        for source in self.sources:
            user = source.find(credentials, request)
            if user is not None:
                return user
        return None

    @abc.abstractmethod
    def identify(self, request: RqT) -> t.Optional[User]:
        pass

    @abc.abstractmethod
    def forget(self, request: RqT):
        pass

    @abc.abstractmethod
    def remember(self, request: RqT, user: User):
        pass


class WSGISessionAuthenticator(
        Authenticator[WSGIRequest, t.Union[t.Mapping, str, bytes]]):

    sources: t.Iterable[
        Source[WSGIRequest, t.Union[t.Mapping, str, bytes]]
    ]

    def __init__(self, sources,
                 context_key: str = 'user',
                 session_key: str = 'user'):
        self.context_key = context_key
        self.session_key = session_key
        self.sources = sources

    def identify(self, request: WSGIRequest) -> t.Optional[User]:
        if (user := request.context.get(self.context_key)) is not None:
            return user

        if (session := request.context.get('http_session')) is not None:
            userid: UserId
            if (userid := session.get(self.session_key, None)) is not None:
                for source in self.sources:
                    user = source.fetch(userid, request)
                    if user is not None:
                        request.context[self.context_key] = user
                        return user

        return None

    def forget(self, request: WSGIRequest):
        if (session := request.context.get('http_session')) is not None:
            session.clear()
        request.context[self.context_key] = None

    def remember(self, request: WSGIRequest, user: User):
        if (session := request.context.get('http_session')) is not None:
            session[self.session_key] = user.id
        request.context[self.context_key] = user
