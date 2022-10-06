import typing as t
from abc import ABC


class Request(ABC):
    context: t.MutableMapping[str, t.Any]


RqT = t.TypeVar('RqT', bound=Request, covariant=True)
RsT = t.TypeVar('RsT', covariant=True)
Config = t.Mapping[str, t.Any]
Handler = t.Callable[[RqT], RsT]
Middleware = t.Callable[[str, Handler, t.Optional[Config]], Handler]
