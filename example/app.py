from typing import Any
from knappe.components.meta import Registry, NamedRegistry
from horseman.mapping import RootNode
from knappe.pipeline import Pipeline
from knappe.response import Response
from knappe.routing import Router
from knappe.decorators import html
from knappe.ui import UI
from knappe.ui.slot import SlotExpr
from knappe.ui.templates import Templates, EXPRESSION_TYPES
from knappe.ui.layout import Layout
from knappe.request import WSGIRequest, RoutingRequest
from knappe.middlewares.session import HTTPSession
import http_session_file
import pathlib



EXPRESSION_TYPES['slot'] = SlotExpr


class Actions(NamedRegistry):
    pass


class Events(Registry):

    def match_all(self, *args):
        found = list(super().match_all(*args))

        def sorting_key(handler):
            return handler.identifier, handler.metadata.get('order', 1000)

        return sorted(found, key=sorting_key)


class Application(RootNode):

    def __init__(self, middlewares=()):
        self.router = Router()
        self.ui = UI()
        self.pipeline = Pipeline(middlewares)

    def resolve(self, path_info, environ):
        request = RoutingRequest(
            environ,
            app=self,
            context={'ui': self.ui}
        )
        request.endpoint = self.router.match(path_info, request.method)
        wrapped = self.pipeline(request.endpoint)
        return wrapped(request)


app = Application((
    HTTPSession(
        store=http_session_file.FileStore(
            pathlib.Path('./sessions'),
            300
        ),
        secret='my secret',
        salt="ABCDEF",
        cookie_name="mycookie",
        secure=False,
        TTL=300
    ),
))

app.ui.templates |= Templates('./templates')



app.ui.layouts.register([RoutingRequest], name='')(Layout(app.ui.templates['layout']))

@app.ui.slots.register((RoutingRequest, Any, Any), name='header')
class Header:

    def render(self, slots, *args):
        return "<br />".join(slot(self, *args) for slot in slots)


@app.ui.slots.register((Header, RoutingRequest, Any, Any), name='example')
def example_slot(manager, request, view, context):
    return "This is some slot"


@app.ui.slots.register((Header, RoutingRequest, Any, Any), name='titi')
def example_slot2(manager, request, view, context):
    return "This is some other slot"


@app.router.register('/')
@html('views/index')
def index(request):
    return {
        'message': 'foobar'
    }
