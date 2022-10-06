import typing as t
import logging
from http_session.session import Session
from knappe.request import WSGIRequest
from knappe.response import Response
from knappe.types import Config, Handler


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

    def add(self, body: str, type: str = "info"):
        if self.key in self.session:
            messages = self.session[self.key]
        else:
            messages = self.session[self.key] = []
        messages.append({"type": type, "body": body})
        self.session.save()


def flash(handler: Handler[WSGIRequest, Response],
          conf: t.Optional[Config] = None
          ) -> Handler[WSGIRequest, Response]:

    def request_flasher(request: WSGIRequest) -> Response:
        if (session := request.context.get('http_session')) is not None:
            request.context['flash'] = SessionMessages(session)
        else:
            logging.warning(
                'FlashMessages can only be used if a session'
                'is already present'
            )
        return handler(request)

    return request_flasher
