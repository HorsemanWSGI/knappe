import typing as t
from horseman.environ import WSGIEnvironWrapper
from horseman.types import Environ
from knappe.types import Request, Application
from knappe.meta import MatchedRoute


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

    endpoint: t.Optional[MatchedRoute]

    def __init__(self,
                 environ: Environ,
                 app: t.Optional[Application] = None,
                 endpoint: t.Optional[MatchedRoute] = None,
                 context: t.MutableMapping[str, t.Any] = None):
        super().__init__(environ, app, context)
        self.endpoint = endpoint

    @property
    def params(self) -> t.Optional[t.Mapping[str, t.Any]]:
        if self.endpoint:
            return self.endpoint.params
        return None
