import colander
import deform
import typing as t
import pathlib
import http_session_file
from chameleon.zpt.loader import TemplateLoader
from chameleon.zpt.template import PageTemplateFile
from horseman.mapping import RootNode
from knappe.decorators import context, html, json, composed, trigger
from knappe.response import Response
from knappe.auth import WSGISessionAuthenticator
from knappe.request import RoutingRequest as Request
from knappe.routing import Router
from knappe.middlewares import auth
from knappe.middlewares.session import HTTPSession
from knappe.ui import SlotExpr, slot, UI, Layout
from knappe.meta import HTTPMethodEndpointMeta


authentication = auth.Authentication(
    authenticator=WSGISessionAuthenticator([
        DictSource({"admin": "admin"})
    ]),
    filters=(
        auth.security_bypass({"/login"}),
        auth.secured(path="/login")
    )
)

session = HTTPSession(
    store=http_session_file.FileStore(pathlib.Path('./session'), 300),
    secret='secret',
    salt='salt',
    cookie_name='session',
    secure=False,
    TTL=300
)


PageTemplateFile.expression_types['slot'] = SlotExpr


@slot.register
@html('header')
def header(request: Request, view: t.Any, context: t.Any, name: t.Literal['header']):
    return {'title': 'This is a header'}


themeUI = UI(
    templates=TemplateLoader(".", ext=".pt"),
    layout=Layout(PageTemplateFile('master.pt')),
)


class Application(RootNode):

    def __init__(self, middlewares=(), config=None):
        self.config = config
        self.router = Router()
        pipeline: Pipeline[Request, Response] = Pipeline(middlewares)

    def resolve(self, path_info, environ):
        request = Request(environ, app=self)
        endpoint = self.router.match_method(request.path, request.method)
        request.context['ui'] = themeUI
        return endpoint.handler(request)


app = Application()


class LoginForm(colander.Schema):

    username = colander.SchemaNode(
        colander.String(),
        title="Login")

    password = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.PasswordWidget(),
        title="Password",
        description="Your password")


def get_document(request):
    if request.params['docid'] == '1':
        return {
            'id': 1,
            'name': 'test',
            'data': 'some data'
        }
    raise LookupError('Could not find the document.')


@app.router.register('/doc/{docid}')
class DocumentView(metaclass=HTTPMethodEndpointMeta):

    @json
    @context(get_document)
    def GET(self, request: Request, document: dict) -> dict:
        return document


@app.router.register('/')
@html('index', default_template=PageTemplateFile('index.pt'))
def index(request):
    return {}


if __name__ == "__main__":
    import bjoern
    bjoern.run(app, "127.0.0.1", 8000)
