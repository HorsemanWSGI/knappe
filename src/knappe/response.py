import typing as t
import orjson
from http import HTTPStatus
from horseman.types import HTTPCode
from horseman.response import BODYLESS, Headers, Response as BaseResponse
from knappe.request import WSGIRequest


REDIRECT = frozenset((
    HTTPStatus.MULTIPLE_CHOICES,
    HTTPStatus.MOVED_PERMANENTLY,
    HTTPStatus.FOUND,
    HTTPStatus.SEE_OTHER,
    HTTPStatus.NOT_MODIFIED,
    HTTPStatus.USE_PROXY,
    HTTPStatus.TEMPORARY_REDIRECT,
    HTTPStatus.PERMANENT_REDIRECT
))


class Response(BaseResponse):

    @classmethod
    def redirect(cls, location, code: HTTPCode = 303,
                 body: t.Optional[t.Iterable] = None,
                 headers: t.Optional[Headers] = None) -> 'Response':
        if code not in REDIRECT:
            raise ValueError(f"{code}: unknown redirection code.")
        if not headers:
            headers = {'Location': location}
        else:
            headers['Location'] = location
        return cls(code, body, headers)

    @classmethod
    def from_file_iterator(cls, filename: str, body: t.Iterable[bytes],
                           headers: t.Optional[Headers] = None):
        if headers is None:
            headers = {
                "Content-Disposition": f"attachment;filename={filename}"}
        elif "Content-Disposition" not in headers:
            headers["Content-Disposition"] = (
                f"attachment;filename={filename}")
        return cls(200, body, headers)

    @classmethod
    def to_json(cls, code: HTTPCode = 200, body: t.Optional[t.Any] = None,
                headers: t.Optional[Headers] = None):
        data = orjson.dumps(body)
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        else:
            headers['Content-Type'] = 'application/json'
        return cls(code, data, headers)

    @classmethod
    def from_json(cls, code: HTTPCode = 200, body: t.AnyStr = '',
                  headers: t.Optional[Headers] = None):
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        else:
            headers['Content-Type'] = 'application/json'
        return cls(code, body, headers)

    @classmethod
    def html(cls, code: HTTPCode = 200, body: t.AnyStr = '',
             headers: t.Optional[Headers] = None):
        if headers is None:
            headers = {'Content-Type': 'text/html; charset=utf-8'}
        else:
            headers['Content-Type'] = 'text/html; charset=utf-8'
        return cls(code, body, headers)


class DecoratedResponse(Response):

    namespace: t.Mapping[str, t.Any]
    layout: t.Optional[t.Callable[[str], str]]
    _request: t.Optional[WSGIRequest]

    def __init__(self, *args, layout=None, namespace=None, **kwargs):
        self.layout = layout
        self.namespace = namespace or {}
        self._request = None
        super().__init__(*args, **kwargs)

    def bind(self, request):
        self._request = request

    @property
    def request(self):
        return self._request

    @property
    def content_type(self):
        return self.headers.get('Content-Type')

    @content_type.setter
    def content_type(self, ctype):
        self.headers['Content-Type'] = ctype

    def render(self):
        if self.layout is not None:
            return self.layout(
                self.request, self.body, **self.namespace)
        return self.body

    def __iter__(self):
        if self.status not in BODYLESS:
            if self.body is None:
                yield self.status.description.encode()
                return

            body = self.render()
            if isinstance(body, bytes):
                yield body
            elif isinstance(body, str):
                yield body.encode()
            elif isinstance(body, (t.Generator, t.Iterable)):
                yield from body
            else:
                raise TypeError(
                    f'Body of type {type(self.body)!r} is not supported.'
                )


__all__ = ('Response', 'DecoratedResponse')
