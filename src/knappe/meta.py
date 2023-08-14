import typing as t
from dataclasses import dataclass
from horseman.types import WSGICallable, HTTPMethod, Environ
from knappe.components import Component


@dataclass
class Route(Component[str, WSGICallable]):

    method: HTTPMethod = 'GET'

    @property
    def path(self) -> str:
        return self.identifier

    def __call__(self, request: Environ, **kwargs):
        if self.conditions:
            if errors := self.evaluate(request, **kwargs):
                raise errors
        return self.value(request, **kwargs)


class MatchedRoute(t.NamedTuple):
    path: str
    route: Route
    method: HTTPMethod
    params: t.Mapping[str, t.Any]

    def __call__(self, request: Environ):
        return self.route(request, **self.params)

    def __hash__(self):
        return hash((self.path, self.method, self.params))
