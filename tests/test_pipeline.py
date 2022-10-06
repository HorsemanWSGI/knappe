from knappe.types import Request
from knappe.pipeline import Pipeline


class DummyRequest(Request):

    def __init__(self):
        self.context = {}


def handler(request: DummyRequest) -> str:
    return 'This is my view'


def capitalize(app, config):
    def capitalize_middleware(request: DummyRequest) -> str:
        response = app(request)
        return response.upper()
    return capitalize_middleware


def suffix(app, config):
    def suffix_middleware(request: DummyRequest) -> str:
        response = app(request)
        response += ' my suffix'
        return response
    return suffix_middleware


def test_middleware():

    request = DummyRequest()

    pipeline: Pipeline[DummyRequest, str] = Pipeline([])
    response = pipeline(handler)(request)
    assert response == 'This is my view'

    pipeline: Pipeline[DummyRequest, str] = Pipeline([capitalize])
    response = pipeline(handler)(request)
    assert response == 'THIS IS MY VIEW'

    pipeline: Pipeline[DummyRequest, str] = Pipeline((suffix, capitalize))
    assert list(pipeline) == [suffix, capitalize]
    response = pipeline(handler)(request)
    assert response == 'THIS IS MY VIEW my suffix'
