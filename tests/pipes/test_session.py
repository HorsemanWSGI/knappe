from knappe.pipeline import Pipeline
from knappe.middlewares.session import HTTPSession
from knappe.request import WSGIRequest, RoutingRequest
from knappe.response import Response
from knappe.routing import Router
from horseman.mapping import RootNode
from webtest import TestApp as WSGIApp
from knappe.pipeline import Pipeline


class Application(RootNode):

    def __init__(self, middlewares=()):
        self.router = Router()
        self.pipeline = Pipeline(middlewares)

    def resolve(self, path_info, environ):
        request = RoutingRequest(environ, app=self)
        request.endpoint = self.router.match_method(
            path_info, request.method)
        wrapped = self.pipeline(request.endpoint.handler)
        return wrapped(request)


def test_session(environ, http_session_store):

    def handler(request):
        request.context['http_session']['test'] = 1
        return Response(201)

    request = WSGIRequest(app=None, environ=environ)
    store = http_session_store()
    middleware = HTTPSession(store=store, secret='my secret')(handler)
    assert middleware(request)
    assert list(store) == ['00000000-0000-0000-0000-000000000000']
    assert store.get('00000000-0000-0000-0000-000000000000') == {
        'test': 1
    }


def test_session_middleware(http_session_store):
    store = http_session_store()
    app = Application(
        middlewares=[HTTPSession(store=store, secret='my secret')]
    )

    @app.router.register('/add')
    def add(request):
        request.context['http_session']['value'] = 1
        return Response(201)

    @app.router.register('/change')
    def change(request):
        request.context['http_session']['value'] = 42
        return Response(201)

    @app.router.register('/fail')
    def failer(request):
        request.context['http_session']['value'] = 666
        return Response(400)

    @app.router.register('/except')
    def exception(request):
        request.context['http_session']['value'] = 666
        raise NotImplementedError()

    test = WSGIApp(app)
    response = test.get('/add')
    assert store.get('00000000-0000-0000-0000-000000000000') == {
        'value': 1
    }

    cookie = response.headers.get('Set-Cookie')
    response = test.get('/change', headers={'Cookie': cookie})
    assert store.get('00000000-0000-0000-0000-000000000000') == {
        'value': 42
    }

    cookie = response.headers.get('Set-Cookie')
    response = test.get(
        '/fail', headers={'Cookie': cookie}, expect_errors=True)
    assert response.status_code == 400
    assert store.get('00000000-0000-0000-0000-000000000000') == {
        'value': 42
    }
