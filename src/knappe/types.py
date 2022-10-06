import typing as t
from abc import ABC
from collections.abc import Callable


class Request(ABC):
    context: t.MutableMapping[str, t.Any]


RqT = t.TypeVar('RqT', bound=Request, covariant=True)
RsT = t.TypeVar('RsT', covariant=True)
Config = t.Mapping[str, t.Any]
Handler = Callable[[RqT], RsT]
Middleware = Callable[[Handler, t.Optional[Config]], Handler]
