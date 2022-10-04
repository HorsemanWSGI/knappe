import typing as t
from chameleon.zpt.loader import TemplateLoader
from chameleon.zpt.template import PageTemplateFile
from knappe.decorators import context, html, json, composed, trigger
from knappe.response import Response
from knappe.request import RoutingRequest as Request
from knappe.routing import Router
from knappe.ui import SlotExpr, slot, UI, Layout
from knappe.meta import HTTPMethodEndpointMeta
from horseman.mapping import RootNode
from horseman.environ import WSGIEnvironWrapper


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

    def __init__(self, config=None):
        self.config = config
        self.router = Router()

    def resolve(self, path_info, environ):
        environ = WSGIEnvironWrapper(environ)
        endpoint = self.router.match_method(
            path_info, environ.get('REQUEST_METHOD', 'GET').upper())
        request = Request(environ, app=self, endpoint=endpoint)
        import pdb
        pdb.set_trace()
        return endpoint.handler(request)


app = Application()


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
    def GET(self, request: Request, document) -> dict:
        return document


@app.router.register('/')
@html('index', default_template=PageTemplateFile('index.pt'))
def index(request):
    return {}


if __name__ == "__main__":
    import bjoern
    bjoern.run(app, "127.0.0.1", 8000)
