import colander
import deform
import pathlib
import inspect
import typing as t
import http_session_file
from dataclasses import dataclass, field
from http import HTTPStatus
from horseman.types import Environ
from horseman.http import HTTPError
from kavallerie.pipes.session import HTTPSession
from kavallerie.testing import DictSource
from kavallerie.app import Application
from kavallerie.events import Event
from kavallerie.routes import Routes
from kavallerie.response import Response, Headers
from kavallerie.request import Request
from kavallerie.pipes import authentication as auth
from chameleon.zpt.loader import TemplateLoader as BaseLoader
from chameleon.zpt.template import PageTemplateFile
from horseman.meta import APIView
from knappe.decorators import context, html, json, composed
from knappe.ui import SlotExpr, slot, UI, Layout
from knappe.response import Response


class TemplateLoader(BaseLoader):

    def __init__(self, path, ext=".pt", **kwargs):
        path = pathlib.Path(path)
        if not path.is_absolute():
            callerframerecord = inspect.stack()[1]
            frame = callerframerecord[0]
            info = inspect.getframeinfo(frame)
            path = pathlib.Path(info.filename).parent / path
        super().__init__(str(path), ext, **kwargs)

    def get(self, filename, default=None):
        try:
            return self.load(filename)
        except ValueError:
            return default

    __getitem__ = BaseLoader.load


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


def unauthorized(exc, request):
    print('I am here')
    if request.user is None:
        return Response.redirect('/login')
    return Response(403)


class HTTPErrorCatcher(
        t.Dict[int, t.Callable[[Exception, Request], t.Optional[Response]]]):

    def __call__(self, handler, conf):
        def error_handler(request):
            try:
                response = handler(request)
            except HTTPError as exc:
                catcher = self.get(exc.status)
                if catcher is None:
                    raise exc
                response = catcher(exc, request)
                if response is None:
                    raise exc
            return response
        return error_handler


class RequestEvent(Event):

    def __init__(self, request):
        self.request = request


class RequestCreatedEvent(RequestEvent):
    pass


@dataclass
class Example(Application):
    routes: Routes = field(default_factory=Routes)

    def resolve(self, path: str, environ: Environ) -> Response:
        request = self.request_factory(path or '/', self, environ)
        self.subscribers.notify(RequestCreatedEvent(request))
        return self.pipeline.wrap(self.endpoint, self.config)(request)

    def endpoint(self, request) -> Response:
        route = self.routes.match_method(request.path, request.method)
        if route is None:
            raise HTTPError(404)
        request.route = route
        return route.endpoint(request, **route.params)



app = Example()
app.pipeline.add(HTTPErrorCatcher({401: unauthorized}))
app.pipeline.add(session, order=10)
app.pipeline.add(authentication, order=20)


@slot.register
@html('header')
def header(request: Request, view: t.Any, context: t.Any, name: t.Literal['header']):
    return {'title': 'This is a header'}


themeUI = UI(
    templates=TemplateLoader(".", ext=".pt"),
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


@app.routes.register('/private')
def never_see(request):
    raise HTTPError(401)


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
