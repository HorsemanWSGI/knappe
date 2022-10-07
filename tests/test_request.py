from webtest.app import TestRequest as Request
from knappe.request import RoutingRequest
from knappe.datastructures import MatchedEndpoint


def some_handler(request: RoutingRequest):
    return None


def test_routing_request():

    matched = MatchedEndpoint(
        uri='/', handler=some_handler, params={'test': 1}
    )

    environ = Request.blank('/?key=1', method='GET').environ
    request = RoutingRequest(environ)
    assert request.params is None
    request.endpoint = matched
    assert request.params == {'test': 1}
