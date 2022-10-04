import typing as t
from functools import reduce
from knappe.types import Config, Handler, Middleware


class Pipeline:

    middlewares: t.Collection[t.Tuple[str, Middleware]]
    _cached: t.Mapping[Handler, Handler]
    config: t.Optional[Config] = None

    def __init__(self,
                 middlewares: t.Collection[t.Tuple[str, Middleware]],
                 config: t.Optional[Config] = None):
        self.config = config
        self.middlewares = tuple(middlewares)  # Freeze.
        self._cached = {}

    def wrap(self, handler: Handler) -> Handler:
        if not self.middlewares:
            return handler
        if handler not in self._cached:
            self._cached[handler] = reduce(
                lambda x, y: y[1](y[0], x, self.config),
                reversed(self.middlewares),  #  t.Tuple[name, Middleware]
                handler
            )
        return self._cached[handler]

    def __call__(self, func):
        if not self.middlewares:
            return func
        return self.wrap(func)
