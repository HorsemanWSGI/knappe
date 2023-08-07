import autoroutes
import typing as t
import inspect
from types import FunctionType
from http import HTTPStatus
from horseman.types import WSGICallable, HTTPMethod
from horseman.exceptions import HTTPError
from knappe.components.meta import Mapping
from knappe.views import APIView
from knappe.meta import Route, MatchedRoute
from plum import dispatch
from frozendict import frozendict


METHODS = frozenset(t.get_args(HTTPMethod))
HTTPMethods = t.Iterable[HTTPMethod]


@dispatch
def as_routable(view: APIView, methods: t.Optional[HTTPMethods]):
    inst = view()
    members = inspect.getmembers(
        inst, predicate=(lambda x: inspect.ismethod(x)
                         and x.__name__ in METHODS))
    for name, func in members:
        yield func, name


@dispatch
def as_routable(view: FunctionType, methods: t.Optional[HTTPMethods]):
    if methods is None:
        methods = ['GET']
    unknown = set(methods) - METHODS
    if unknown:
        raise ValueError(
            f"Unknown HTTP method(s): {', '.join(unknown)}")
    yield view, methods


class RouteStore(Mapping[t.Tuple[str, HTTPMethod], Route]):

    factory: t.Type[Route] = Route
    _names: t.Mapping[str, str]

    def __init__(self, *args, **kwargs):
        self._names = {}
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, route):
        if route.name:
            if existing := self._names.get(route.name):
                if existing != route.path:
                    raise NameError('Route already existing')
            else:
                self._names[route.name] = route.path
        super().__setitem__(key, route)

    def add(self, route: Route):
        self[(route.identifier, route.method)] = route

    def register(self,
                 identifier: str,
                 methods: t.Optional[t.Iterable[HTTPMethod]] = None,
                 **kwargs):
        def routing(value: WSGICallable | t.Type[APIView]):
            for endpoint, verbs in as_routable(value, methods):
                for method in verbs:
                    self.create(
                        endpoint, identifier, method=method, **kwargs)
            return value
        return routing

    def url_for(self, name: str, **params):
        path = self._names.get(name)
        if path is None:
            raise LookupError(f'Unknown route `{name}`.')
        try:
            # Raises a KeyError too if some param misses
            return path.format(**params)
        except KeyError:
            raise ValueError(
                f"No route found with name {name} and params {params}.")

    def get(self, path: str, **metadata):
        return self.register(path, methods=('GET',), **metadata)

    def post(self, path: str, **metadata):
        return self.register(path, methods=('POST',), **metadata)

    def put(self, path: str, **metadata):
        return self.register(path, methods=('PUT',), **metadata)

    def delete(self, path: str, **metadata):
        return self.register(path, methods=('DELETE',), **metadata)

    def options(self, path: str, **metadata):
        return self.register(path, methods=('OPTIONS',), **metadata)

    def head(self, path: str, **metadata):
        return self.register(path, methods=('HEAD',), **metadata)

    def patch(self, path: str, **metadata):
        return self.register(path, methods=('PATCH',), **metadata)

    def trace(self, path: str, **metadata):
        return self.register(path, methods=('TRACE',), **metadata)

    def connect(self, path: str, **metadata):
        return self.register(path, methods=('CONNECT',), **metadata)


class Router(RouteStore):

    routes = autoroutes.Routes

    def __init__(self, *args, **kwargs):
        self.routes = autoroutes.Routes()
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, route):
        super().__setitem__(key, route)
        self.routes.add(route.path, **{route.method: route})

    def match(self,
              path: str,
              method: HTTPMethod) -> t.Optional[MatchedRoute]:

        found, params = self.routes.match(path)
        if found is None:
            return None

        if route := found.get(method):
            return MatchedRoute(
                path=path,
                route=route,
                method=method,
                params=frozendict(params)
            )

        raise HTTPError(HTTPStatus.METHOD_NOT_ALLOWED)
