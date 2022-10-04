import typing as t
from knappe.types import HTTPMethod, Handler


class MatchedEndpoint(t.NamedTuple):
    uri: str
    handler: Handler
    params: t.Mapping[str, str]


class EndpointDefinition(t.NamedTuple):
    handler: Handler
    metadata: t.Optional[t.Mapping[t.Any, t.Any]] = None

    def matched(self, path, params):
        return MatchedEndpoint(
            uri=path, handler=self.handler, params=params)
