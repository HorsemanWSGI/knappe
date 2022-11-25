import typing as t
from http import HTTPStatus
from frozendict import frozendict
from autoroutes import Routes
from horseman.exceptions import HTTPError
from horseman.types import HTTPMethod, HTTPMethods
from knappe.meta import HTTPEndpointMeta
from knappe.datastructures import MatchedEndpoint, EndpointDefinition


class Router(Routes):

    __slots__ = ('_names')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._names = {}

    def __iter__(self):
        def route_iterator(edges):
            if edges:
                for edge in edges:
                    if edge.child.path:
                        yield edge.child.path, edge.child.payload
                    yield from route_iterator(edge.child.edges)
        yield from route_iterator(self.root.edges)

    def has_route(self, name: str):
        return name in self._names

    def add(self,
            path: str,
            route_definition: t.Mapping[HTTPMethod, EndpointDefinition],
            name: t.Optional[str] = None,
            ):
        if name:
            if found := self._names.get(name):
                if path != found:
                    raise NameError(
                        f"Route {name!r} already exists for path {found!r}.")
            else:
                self._names[name] = path
        return super().add(path, **route_definition)

    def register(self,
                 path: str,
                 methods: t.Optional[HTTPMethods] = None,
                 **metadata):

        name = metadata.pop("name", None)
        metadata = frozendict(metadata)
        def routing(routable: t.Callable):
            if isinstance(routable, HTTPEndpointMeta):
                route_definition = routable.as_endpoint(
                    methods=methods,
                    metadata=metadata
                )
            elif callable(routable):
                route_definition = {
                    verb: EndpointDefinition(
                        handler=routable,
                        metadata=metadata
                    ) for verb in (methods or ('GET',))
                }
            else:
                raise NotImplementedError(
                    f"Unknown type of routable: {routable!r}"
                )
            self.add(path, route_definition, name=name)
            return routable

        return routing

    def match_method(self,
                     path_info: str,
                     method: HTTPMethod) -> MatchedEndpoint:
        found, params = self.match(path_info)
        if found is None:
            raise HTTPError(HTTPStatus.NOT_FOUND)

        endpoint = found.get(method)
        if endpoint is None:
            raise HTTPError(HTTPStatus.METHOD_NOT_ALLOWED)

        return endpoint.matched(path_info, frozendict(params))

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
