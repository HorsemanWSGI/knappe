import typing as t
from http import HTTPStatus
from frozendict import frozendict
from autoroutes import Routes
from horseman.exceptions import HTTPError
from horseman.types import HTTPMethod, HTTPMethods
from knappe.meta import HTTPEndpointMeta
from knappe.datastructures import MatchedEndpoint, EndpointDefinition


class Router(Routes):

    def add(self,
            path: str,
            route_definition: t.Mapping[HTTPMethod, EndpointDefinition]):
        return super().add(path, **route_definition)

    def register(self,
                 path: str,
                 methods: t.Optional[HTTPMethods] = None,
                 **metadata):
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
            self.add(path, route_definition)
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
