from knappe.response import Response
from knappe.request import WSGIRequest
from knappe.fixtures.auth import DictSource, UserObject
from knappe.auth import WSGISessionAuthenticator
from knappe.middlewares.session import HTTPSession
from knappe.middlewares.auth import (
    Authentication, security_bypass, secured, TwoFA)


def test_auth(environ, http_session_store):

    def handler(request):
        return Response(201)

    request = WSGIRequest(environ)
    authentication: Authentication[WSGIRequest, Response] = Authentication(
        authenticator=WSGISessionAuthenticator([
            DictSource({'admin': 'admin'})
        ])
    )
    store = http_session_store()
    session = HTTPSession(store=store, secret='my secret')

    pipeline = session(authentication(handler))
    assert pipeline(request)
    assert list(store) == []

    user = authentication.authenticator.from_credentials(request, {
        'username': 'admin',
        'password': 'admin'
    })
    assert user.id == 'admin'

    authentication.authenticator.remember(request, user)
    pipeline = session(authentication(handler))
    assert pipeline(request)
    assert list(store) == ['00000000-0000-0000-0000-000000000000']
    assert store.get('00000000-0000-0000-0000-000000000000') == {
        'user': 'admin'
    }

    authentication.authenticator.forget(request)
    pipeline = session(authentication(handler))
    assert pipeline(request)
    assert list(store) == ['00000000-0000-0000-0000-000000000000']
    assert store.get('00000000-0000-0000-0000-000000000000') == {}


def test_filter(environ):

    def handler(request):
        return Response(201)

    def admin_filter(caller, request):
        if request.user.id != 'admin':
            return Response(403)


    authentication: Authentication[WSGIRequest, Response] = Authentication(
        authenticator=WSGISessionAuthenticator([
            DictSource({'admin': 'admin'}),
            DictSource({'test': 'test'}),
        ]),
        filters=[admin_filter]
    )

    request = WSGIRequest(environ=environ)
    request.user = authentication.authenticator.from_credentials(request, {
        'username': 'admin',
        'password': 'admin'
    })
    response = authentication(handler)(request)
    assert response.status == 201

    request.user = authentication.authenticator.from_credentials(request, {
        'username': 'test',
        'password': 'test'
    })
    response = authentication(handler)(request)
    assert response.status == 403


def test_secured_filter(environ):

    def handler(request):
        return Response(201)

    request = WSGIRequest(environ)
    response = secured('/login')(handler, request)
    assert response.status == 303
    assert response.headers['Location'] == '/login'

    response = secured('/login')(handler, request)
    assert response.status == 303
    assert response.headers['Location'] == '/login'

    user = UserObject("test")
    request.context['user'] = user
    response = secured('/login')(handler, request)
    assert response is None


def test_security_bypass_filter(environ):

    def handler(request):
        return Response(201)

    request = WSGIRequest(environ)
    response = security_bypass('/login')(handler, request)
    assert response.status == 201

    request = WSGIRequest({**environ, 'PATH_INFO': '/test'})
    response = security_bypass('/login')(handler, request)
    assert response is None


def test_twoFA_filter(environ):

    def twofa_checker(request):
        return request.context.get('twoFA', False)

    def handler(request):
        return Response(201)

    request = WSGIRequest({**environ, 'PATH_INFO': '/index'})
    response = TwoFA('/sms_qr_code', twofa_checker)(handler, request)
    assert response.status == 303
    assert response.headers['Location'] == '/sms_qr_code'

    request = WSGIRequest({**environ, 'PATH_INFO': '/sms_qr_code'})
    response = TwoFA('/sms_qr_code', twofa_checker)(handler, request)
    assert response.status == 201

    request = WSGIRequest({**environ, 'PATH_INFO': '/index'})
    request.context['twoFA'] = True
    response = TwoFA('/sms_qr_code', twofa_checker)(handler, request)
    assert response is None
