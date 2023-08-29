from knappe.request import WSGIRequest
from knappe.auth import WSGISessionAuthenticator
from knappe.fixtures.auth import DictSource


def test_source(environ):
    request = WSGIRequest(environ)
    authenticator = WSGISessionAuthenticator([
        DictSource({'admin': 'admin'})
    ])

    user = authenticator.from_credentials(request, {
        'username': 'john',
        'password': 'test'
    })
    assert user is None

    user = authenticator.from_credentials(request, {
        'username': 'admin',
        'password': 'admin'
    })
    assert user.id == 'admin'


def test_several_sources(environ):
    request = WSGIRequest(environ)
    authenticator = WSGISessionAuthenticator([
        DictSource({'admin': 'admin'}),
        DictSource({'test': 'test'}),
        DictSource({'john': 'doe'}),
    ])

    user = authenticator.from_credentials(request, {
        'username': 'john',
        'password': 'test'
    })
    assert user is None

    user = authenticator.from_credentials(request, {
        'username': 'test',
        'password': 'test'
    })
    assert user.id == 'test'
