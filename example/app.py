import pathlib
import colander
import deform
import http_session_file
from typing import Any
from horseman.mapping import RootNode
from knappe.auth import WSGISessionAuthenticator
from knappe.components import Registry, NamedRegistry
from knappe.decorators import context
from knappe.middlewares.auth import Authentication
from knappe.middlewares.flash import flash
from knappe.middlewares.session import HTTPSession
from knappe.pipeline import Pipeline
from knappe.renderers import html, template
from knappe.request import WSGIRequest, RoutingRequest
from knappe.response import Response
from knappe.routing import Router
from knappe.testing import DictSource
from knappe.types import User
from knappe.ui import UI
from knappe.ui.slot import SlotExpr
from knappe.ui.templates import Templates, EXPRESSION_TYPES
from knappe.views import APIView
from prejudice.errors import ConstraintError


#Any = object
EXPRESSION_TYPES['slot'] = SlotExpr


class Events(Registry):

    def find_all(self, *args):
        found = list(super().find_all(*args))

        def sorting_key(handler):
            return handler.identifier, handler.metadata.get('order', 1000)

        return sorted(found, key=sorting_key)

    def notify(self, *args):
        for handler in self.find_all(*args):
            handler(*args)


class Application(RootNode):

    def __init__(self, middlewares=()):
        self.router = Router()
        self.ui = UI()
        self.actions = NamedRegistry()
        self.pipeline = Pipeline(middlewares)
        self.subscribers = Events()

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
    Authentication(
        WSGISessionAuthenticator(
            sources=(
                DictSource({
                    'user': 'password'
                }),
            )
        )
    ),
    flash
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
    return '/login'


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


@app.ui.slots.register((Header, RoutingRequest, Any, Any), name='messages')
@template('slots/messages')
def messages(request, manager, view, context):
    return {
        'messages': [m for m in request.context['flash']]
    }



@app.router.register('/')
@html('views/index')
def index(request):
    return {
        'message': 'foobar'
    }


@app.router.register('/composed')
@html('composed')
def composed(request):
    return {
        'pages': {
            'The Index': index.bare(request),
        }
    }


@app.subscribers.register((RoutingRequest, User))
def logged_in(request, user):
    print(request, user)


class LoginSchema(colander.Schema):

    username = colander.SchemaNode(
        colander.String(),
        title="Name"
    )

    password = colander.SchemaNode(
        colander.String(),
        title="password"
    )


def login_form(request):
    schema = LoginSchema().bind(request=request)
    process_btn = deform.form.Button(name='process', title="Process")
    return deform.form.Form(schema, buttons=(process_btn,))


@app.router.register('/login')
class Login(APIView):

    @html('views/form')
    @context(login_form)
    def GET(self, request, form):
        return {
            "rendered_form": form.render()
        }

    @html('views/form')
    @context(login_form)
    def POST(self, request, form):
        if ('process', 'process') not in request.data.form:
            raise NotImplementedError('No action found.')

        try:
            appstruct = form.validate(request.data.form)
        except deform.exception.ValidationFailure as e:
            return {
                "rendered_form": e.render()
            }

        user = request.context['authentication'].from_credentials(
            request, appstruct
        )
        if user is not None:
            request.context['authentication'].remember(
                request, user
            )
            app.subscribers.notify(request, user)
            request.context['flash'].add('Successfully logged in.')
            return Response.redirect("/")

        # Login failed.
        request.context['flash'].add('Login failed.')
        return {
            "rendered_form": form.render()
        }
