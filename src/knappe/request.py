import typing as t
from horseman.environ import WSGIEnvironWrapper
from horseman.types import Environ, WSGICallable
from knappe.types import Request
from knappe.datastructures import MatchedEndpoint


class WSGIRequest(Request):

    __slots__ = ('app', 'environ', 'params', 'context')

    environ: WSGIEnvironWrapper
    app: t.Optional[WSGICallable]
    params: t.Optional[t.Mapping[str, t.Any]]

    def __init__(self,
                 environ: Environ,
                 app: t.Optional[WSGICallable] = None,
                 context: t.MutableMapping[str, t.Any] = None):
        self.app = app
        self.environ = WSGIEnvironWrapper(environ)
        self.context = context if context is not None else {}
        self.params = {}


class RoutingRequest(WSGIRequest):

    __slots__ = ('app', 'environ', 'endpoint', 'context')

    endpoint: t.Optional[MatchedEndpoint]

    def __init__(self,
                 environ: Environ,
                 app: t.Optional[WSGICallable] = None,
                 endpoint: t.Optional[MatchedEndpoint] = None,
                 context: t.MutableMapping[str, t.Any] = None):
        self.app = app
        self.environ = WSGIEnvironWrapper(environ)
        self.context = context if context is not None else {}
        self.endpoint = endpoint

    @property
    def params(self):
        if self.endpoint:
            return self.endpoint.params
        return None
