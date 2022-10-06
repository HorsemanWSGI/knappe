import typing as t
from abc import ABC


UserId = t.Union[str, int]


class User(ABC):
    id: UserId


class Request(ABC):
    context: t.MutableMapping[str, t.Any]


RqT = t.TypeVar('RqT', bound=Request)
RsT = t.TypeVar('RsT', covariant=True)
Config = t.Mapping[str, t.Any]
Handler = t.Callable[[RqT], RsT]
Middleware = t.Callable[[Handler, t.Optional[Config]], Handler]
