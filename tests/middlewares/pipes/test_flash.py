from horseman.mapping import RootNode
from knappe.pipeline import Pipeline
from knappe.middlewares.flash import flash
from knappe.middlewares.session import HTTPSession
from knappe.response import Response
from knappe.routing import Router
from knappe.request import RoutingRequest
from webtest import TestApp as WSGIApp


class Application(RootNode):

    def __init__(self, middlewares=()):
        self.router = Router()
        self.pipeline = Pipeline(middlewares)

    def resolve(self, path_info, environ):
        request = RoutingRequest(environ, app=self)
        request.endpoint = self.router.match(path_info, request.method)
        wrapped = self.pipeline(request.endpoint)
        return wrapped(request)


def test_session_middleware(http_session_store):
    store = http_session_store()
    app = Application(middlewares=(
        HTTPSession(store=store, secret='my secret'),
        flash,
    ))

    @app.router.register('/add')
    def add(request):
        request.context['flash'].add('This is a message')
        return Response(201)

    @app.router.register('/consume')
    def consume(request):
        messages = request.context['flash']
        return Response.to_json(201, body=[m.to_dict() for m in messages])

    @app.router.register('/consume_fail')
    def consume_fail(request):
        list(request.context['flash'])
        return Response(400)

    test = WSGIApp(app)
    response = test.get('/add')
    assert store.get('00000000-0000-0000-0000-000000000000') == {
        'flashmessages': [{'body': 'This is a message', 'type': 'info'}]
    }

    cookie = response.headers.get('Set-Cookie')
    response = test.get('/consume', headers={'Cookie': cookie})
    assert store.get('00000000-0000-0000-0000-000000000000') == {
        'flashmessages': []
    }

    response = test.get('/add', headers={'Cookie': cookie})
    cookie = response.headers.get('Set-Cookie')
    response = test.get('/consume_fail',
                        headers={'Cookie': cookie}, expect_errors=True)
    assert store.get('00000000-0000-0000-0000-000000000000') == {
        'flashmessages': [{'body': 'This is a message', 'type': 'info'}]
    }
