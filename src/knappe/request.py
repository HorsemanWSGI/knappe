import typing as t
from abc import ABC
from horseman.environ import WSGIEnvironWrapper
from horseman.types import Environ, WSGICallable
from knappe.datastructures import MatchedEndpoint


class Request(ABC):
    pass


class WSGIRequest(Request, t.Dict[str, t.Any]):

    __slots__ = ('app', 'environ', 'params')

    environ: WSGIEnvironWrapper
    app: t.Optional[WSGICallable]
    params: t.Optional[t.Mapping[str, t.Any]]

    def __init__(self,
                 environ: Environ,
                 app: t.Optional[WSGICallable] = None,
                 params: t.Optional[t.Mapping[str, t.Any]] = None):
        self.app = app
        self.environ = WSGIEnvironWrapper(environ)
        if params is None:
            params = {}
        self.params = params


class RoutingRequest(WSGIRequest):

    __slots__ = ('app', 'environ', 'endpoint')

    endpoint: t.Optional[MatchedEndpoint]

    def __init__(self,
                 environ: Environ,
                 app: t.Optional[WSGICallable] = None,
                 endpoint: t.Optional[MatchedEndpoint] = None):
        self.endpoint = endpoint

    @property
    def params(self) -> t.Optional[t.Mapping[str, t.Any]]:
        if self.endpoint:
            return self.endpoint.params
