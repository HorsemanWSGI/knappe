import typing as t
import logging
from http_session.session import Session
from knappe.types import Handler, Config
from knappe.request import Request
from knappe.response import BaseResponse
from knappe.types import Handler, Middleware


class Message(t.NamedTuple):
    body: str
    type: str = "info"

    def to_dict(self):
        return self._asdict()


class SessionMessages:

    def __init__(self, session: Session, key: str = "flashmessages"):
        self.key = key
        self.session = session

    def __iter__(self) -> t.Iterable[Message]:
        if self.key in self.session:
            while self.session[self.key]:
                yield Message(**self.session[self.key].pop(0))
                self.session.save()

    def add(self, body: str, type: str = "info") -> t.NoReturn:
        if self.key in self.session:
            messages = self.session[self.key]
        else:
            messages = self.session[self.key] = []
        messages.append({"type": type, "body": body})
        self.session.save()


def flash(handler: Handler[Request, Response],
          conf: t.Optional[Config] = None) -> Handler[Request, Response]:
    def request_flasher(request: Request) -> BaseResponse:
        if (session := request.get('http_session')) is not None:
            request['flash'] = SessionMessages(session)
        else:
            logging.warning(
                'FlashMessages can only be used if a session'
                'is already present'
            )
        return handler(request)
    return request_flasher
