import colander
import deform
import pathlib
import typing as t
import http_session_file
from horseman.types import Environ
from kavallerie.pipes.session import HTTPSession
from kavallerie.testing import DictSource
from kavallerie.app import RoutingApplication
from kavallerie.events import Event
from kavallerie.response import Response
from kavallerie.request import Request
from kavallerie.pipes import authentication as auth
from chameleon.zpt.template import PageTemplateFile
from horseman.meta import APIView
from knappe.decorators import context, html, json, composed
from knappe.ui import SlotExpr, slot, UI, Layout
from knappe.response import Response


PageTemplateFile.expression_types['slot'] = SlotExpr


authentication = auth.Authentication(
    sources=[DictSource({"admin": "admin"})],
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


class RequestEvent(Event):

    def __init__(self, request):
        self.request = request


class RequestCreatedEvent(RequestEvent):
    pass


class Example(RoutingApplication):

    def resolve(self, path: str, environ: Environ) -> Response:
        request = self.request_factory(path or '/', self, environ)
        self.subscribers.notify(RequestCreatedEvent(request))
        return self.pipeline.wrap(self.endpoint, self.config)(request)


app = Example()
app.pipeline.add(session, order=10)
app.pipeline.add(authentication, order=20)


@slot.register
@html('header')
def header(request: Request, view: t.Any, context: t.Any, name: t.Literal['header']):
    return {'title': 'This is a header'}


themeUI = UI(
    templates={
        'form': PageTemplateFile('form.pt'),
        'index': PageTemplateFile('index.pt'),
        'header': PageTemplateFile('header.pt'),
        'composed': PageTemplateFile('composed.pt'),
    },
    layout=Layout(PageTemplateFile('master.pt')),
)


@app.subscribers.subscribe(RequestCreatedEvent)
def theme(event):
    event.request.utilities['ui'] = themeUI


class LoginForm(colander.Schema):

    username = colander.SchemaNode(
        colander.String(),
        title="Login")

    password = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.PasswordWidget(),
        title="Password",
        description="Your password")


def get_document(request, docid):
    if docid == '1':
        return {
            'id': 1,
            'name': 'test',
            'data': 'some data'
        }
    raise LookupError('Could not find the document.')


def someview(request):
    return Response(body='some stuff')


@app.routes.register('/test')
class Test(APIView):

    @json
    def GET(self, request):
        return {'test': 1}


@app.routes.register('/doc/{docid}')
class DocumentView(APIView):

    @json
    @context(get_document)
    def GET(self, document, request, **params):
        return document


@app.routes.register('/')
class Index(APIView):

    @html('index')
    def GET(self, request):
        return {}


class SubComposed(APIView):

    pages = {
        'sub': someview,
    }

    @html('composed')
    def GET(self, request):
        name = request.route.params['name']
        page = self.pages.get(name)
        if page is None:
            raise NotImplementedError()
        return {
            'rendered_page': composed(page)(request).render()
        }


@app.routes.register('/composed/{name:alpha}')
class Composed(APIView):

    pages = {
        'index': Index(),
        'sub': SubComposed(),
    }

    @html('composed')
    def GET(self, request, name: str):
        page = self.pages.get(name)
        if page is None:
            raise NotImplementedError()
        return {
            'rendered_page': composed(page)(request).render()
        }


@app.routes.register('/login')
class Login(APIView):

    def get_form(self, request):
        schema = LoginForm().bind(request=request)
        process_btn = deform.form.Button(name='process', title="Process")
        return deform.form.Form(schema, buttons=(process_btn,))

    @html('form')
    def GET(self, request):
        form = self.get_form(request)
        return {
            "rendered_form": form.render()
        }

    @html('form')
    def POST(self, request):
        form = self.get_form(request)
        data = request.extract()
        if ('process', 'process') in data.form:
            try:
                appstruct = form.validate(data.form)
                auth = request.utilities['authentication']
                user = auth.from_credentials(request, appstruct)
                if user is not None:
                    auth.remember(request, user)
                    return Response.redirect("/")
                return Response.redirect("/login")
            except deform.exception.ValidationFailure as e:
                return {
                    "rendered_form": e.render()
                }
        return Response(400)


if __name__ == "__main__":
    import bjoern
    bjoern.run(app, "127.0.0.1", 8000)
