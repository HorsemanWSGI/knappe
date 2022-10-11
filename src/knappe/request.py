import typing as t
from horseman.environ import WSGIEnvironWrapper
from horseman.types import Environ
from knappe.types import Request, Application
from knappe.datastructures import MatchedEndpoint


class WSGIRequest(Request, WSGIEnvironWrapper):

    __slots__ = ('app', 'context')

    def __init__(self,
                 environ: Environ,
                 app: t.Optional[Application] = None,
                 context: t.MutableMapping[str, t.Any] = None):
        WSGIEnvironWrapper.__init__(self, environ)
        self.app = app
        self.context = context if context is not None else {}


class RoutingRequest(WSGIRequest):

    __slots__ = ('app', 'context', 'endpoint')

    endpoint: t.Optional[MatchedEndpoint]

    def __init__(self,
                 environ: Environ,
                 app: t.Optional[Application] = None,
                 endpoint: t.Optional[MatchedEndpoint] = None,
                 context: t.MutableMapping[str, t.Any] = None):
        WSGIEnvironWrapper.__init__(self, environ)
        self.app = app
        self.environ = WSGIEnvironWrapper(environ)
        self.context = context if context is not None else {}
        self.endpoint = endpoint

    @property
    def params(self) -> t.Optional[t.Mapping[str, t.Any]]:
        if self.endpoint:
            return self.endpoint.params
        return None
