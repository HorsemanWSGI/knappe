import typing as t
from abc import ABC
from uuid import UUID
from horseman.types import HTTPMethod, HTTPCode, Environ, WSGICallable


HTTPMethods = t.Iterable[HTTPMethod]
UserId = str | int | bytes | UUID


class User(ABC):
    id: UserId


class Request(ABC):
    context: t.MutableMapping[str, t.Any]


RqT = t.TypeVar('RqT', bound=Request)  # Request type
RsT = t.TypeVar('RsT', covariant=True)  # Response type

Config = t.Mapping[str, t.Any]
Handler = t.Callable[[RqT], RsT]
Middleware = t.Callable[[Handler, t.Optional[Config]], Handler]
Application = WSGICallable


__all__ = [
    'HTTPMethod', 'HTTPCode', 'Environ', 'WSGICallable',  # Horseman
    'User', 'Request', 'Config', 'Handler', 'Middleware',
    'RsT', 'RqT', 'UserId', 'HTTPMethods'
]
