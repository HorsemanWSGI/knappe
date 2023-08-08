from typing import Any
from knappe.components import Registry, NamedRegistry
from horseman.mapping import RootNode
from knappe.pipeline import Pipeline
from knappe.response import Response
from knappe.routing import Router
from knappe.decorators import html, template
from knappe.ui import UI
from knappe.ui.slot import SlotExpr
from knappe.ui.templates import Templates, EXPRESSION_TYPES
from prejudice.errors import ConstraintError
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
        self.actions = NamedRegistry()
        self.pipeline = Pipeline(middlewares)

    def resolve(self, path_info, environ):
        request = RoutingRequest(
            environ,
            app=self,
            context={'ui': self.ui}
        )
        if endpoint := self.router.match(path_info, request.method):
            request.endpoint = endpoint
            wrapped = self.pipeline(request.endpoint)
            return wrapped(request)
        return Response(404)


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


def not_anonymous(action, request, view, context):
    if request.context.get('user') is None:
        raise ConstraintError('Request not anonymous.')


def anonymous(action, request, view, context):
    if request.context.get('user') is not None:
        raise ConstraintError('Request is not anonymous.')


@app.ui.layouts.register(
    [RoutingRequest], name='', metadata={'content_types': ('text/html',)})
@template('layout')
def basic_bootstrap_layout(request, body, **namespace):
    return {
        **namespace,
        "request": request,
        "content": body,
    }


@app.actions.register((RoutingRequest, Any, Any), name='login', title='Login', description='Login action', conditions=(anonymous,))
def login(request, view, item):
    return 'some url'


@app.actions.register((RoutingRequest, Any, Any), name='logout', title='Logout', description='Logout action', conditions=(not_anonymous,))
def logout(request, view, item):
    return 'some url'


@app.ui.slots.register((RoutingRequest, Any, Any), name='header')
class Header:

    @template('slots/header')
    def __call__(self, request, view, context, slots):
        return {
            "slots": {
                slot.identifier: slot(request, self, view, context)
                for slot in slots
            }
        }


@app.ui.slots.register((Header, RoutingRequest, Any, Any), name='topmenu')
@template('slots/topmenu')
def top_menu(request, manager, view, context):
    return {}


@app.ui.slots.register((Header, RoutingRequest, Any, Any), name='search')
@template('slots/search')
def search(request, manager, view, context):
    return {
        "actions": [
            (action, action(request, view, context))
            for action in request.app.actions.find_all(
                    request, view, context
            ) if action.check(request, view, context)
        ]
    }


@app.router.register('/')
@html('views/index')
def index(request):
    return {
        'message': 'foobar'
    }
