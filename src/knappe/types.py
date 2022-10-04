import typing as t
from horseman.types import HTTPMethod


Config = t.Mapping[str, t.Any]
HTTPMethods = t.Iterable[HTTPMethod]
METHODS = frozenset(t.get_args(HTTPMethod))
Handler = t.Callable[..., t.Any]
Middleware = t.Callable[[str, Handler, t.Optional[Config]], Handler]
