import typing as t
from knappe.response import Response
from knappe.request import WSGIRequest
from knappe.auth import Source, Authenticator
from knappe.types import RqT, RsT, Handler, Middleware, Request


Filter = t.Callable[[Handler, RqT], t.Optional[RsT]]


class Authentication(t.Generic[RqT, RsT]):

    def __init__(self,
                 authenticator: Authenticator,
                 filters: t.Optional[t.Sequence[Filter]] = None):
        self.filters = filters
        self.authenticator = authenticator

    def __call__(self,
                 handler: Handler[RqT, RsT],
                 globalconf: t.Optional[t.Mapping] = None):

        def authentication_middleware(request: RqT):
            request.context['authentication'] = self.authenticator
            try:
                _ = self.authenticator.identify(request)
                if self.filters:
                    for filter in self.filters:
                        if (resp := filter(handler, request)) is not None:
                            return resp
                return handler(request)
            finally:
                del request.context['authentication']
        return authentication_middleware


def security_bypass(*urls: str) -> Filter:
    unprotected: t.FrozenSet[str] = frozenset(*urls)

    def _filter(caller: Handler[WSGIRequest, Response], request: WSGIRequest):
        if request.environ.path in unprotected:
            return caller(request)

    return _filter


def secured(path: str) -> Filter:

    def _filter(caller: Handler[WSGIRequest, Response], request: WSGIRequest):
        if request.context.get('user') is None:
            return Response.redirect(request.environ.script_name + path)

    return _filter


def TwoFA(path: str, checker: t.Callable[[WSGIRequest], bool]) -> Filter:

    def _filter(caller: Handler[WSGIRequest, Response], request: WSGIRequest):
        if request.environ.path == path:
            return caller(request)
        if not checker(request):
            return Response.redirect(request.environ.script_name + path)

    return _filter
