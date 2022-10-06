import typing as t
from functools import reduce
from knappe.types import RqT, RsT, Config, Handler, Middleware


class Pipeline(t.Generic[RqT, RsT], t.Collection[Middleware]):

    config: t.Optional[Config] = None
    _middlewares: t.Sequence[Middleware]
    _cached: t.Dict[Handler[RqT, RsT], Handler[RqT, RsT]]

    def __init__(self,
                 middlewares: t.Iterable[Middleware],
                 config: t.Optional[Config] = None):
        self.config = config
        self._middlewares = tuple(middlewares)  # Freeze.
        self._cached = {}

    def __iter__(self):
        return iter(self._middlewares)

    def __contains__(self, item):
        return item in self._middlewares

    def __len__(self):
        return len(self._middlewares)

    def wrap(self, handler: Handler[RqT, RsT]) -> Handler[RqT, RsT]:
        if not self._middlewares:
            return handler
        if handler not in self._cached:
            self._cached[handler] = reduce(
                lambda x, y: y(x, self.config),
                reversed(self._middlewares),
                handler
            )
        return self._cached[handler]

    def __call__(self, func):
        if not self._middlewares:
            return func
        return self.wrap(func)
