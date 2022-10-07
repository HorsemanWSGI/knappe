import pytest
import webtest
from unittest.mock import Mock
from http import HTTPStatus
from knappe.utils import file_iterator
from knappe.response import Response


def test_file_iterator(tmpdir):

    fpath = tmpdir / 'test.txt'
    with fpath.open('w+') as fd:
        fd.write('This is a sentence')

    fiter = file_iterator(fpath, chunk=3)
    chunks = list(fiter)
    assert chunks == [b'Thi', b's i', b's a', b' se', b'nte', b'nce']

    fiter = file_iterator(fpath)
    chunks = list(fiter)
    assert chunks == [b'This is a sentence']

    response = Response.from_file_iterator(
        'test.txt', file_iterator(fpath))
    assert response.status == 200
    assert list(response.headers.items()) == [
        ('Content-Disposition', 'attachment;filename=test.txt')
    ]
    assert list(response) == [b'This is a sentence']

    response = Response.from_file_iterator(
        'test.txt', file_iterator(fpath),
        headers={"Content-Type": "foo"}
    )
    assert list(response.headers.items()) == [
        ('Content-Type', 'foo'),
        ('Content-Disposition', 'attachment;filename=test.txt')
    ]

    response = Response.from_file_iterator(
        'test.txt', file_iterator(fpath),
        headers={"Content-Disposition": "foobar"}
    )
    assert list(response.headers.items()) == [
        ('Content-Disposition', 'foobar')
    ]


def test_json_response_headers():
    response = Response.from_json(body="{}")
    assert list(response.headers.items()) == [
        ('Content-Type', 'application/json')
    ]

    response = Response.from_json(
        body="{}", headers={"Content-Type": "text/html"})
    assert list(response.headers.items()) == [
        ('Content-Type', 'application/json')
    ]


def test_html_response():

    response = Response.html(body="<html></html>")
    assert list(response.headers.items()) == [
        ('Content-Type', 'text/html; charset=utf-8')
    ]

    response = Response.html(
        body="{}", headers={"Content-Type": "text/plain"})
    assert list(response.headers.items()) == [
        ('Content-Type', 'text/html; charset=utf-8')
    ]


def test_json_response():
    structure = {
        'Horseman': 'headless',
        'python3.8': True,
        'version': 0.1
    }

    app = webtest.TestApp(
        Response.to_json(body=structure)
    )
    response = app.get('/')
    assert response.status_int == 200
    assert response.body == (
        b'{"Horseman":"headless","python3.8":true,"version":0.1}')
    assert list(response.headers.items()) == [
        ('Content-Type', 'application/json'),
        ('Content-Length', '54')
    ]

    app = webtest.TestApp(
        Response.to_json(
            body=structure, headers={'Custom-Header': 'Test'}))
    response = app.get('/')
    assert response.status_int == 200
    assert response.body == (
        b'{"Horseman":"headless","python3.8":true,"version":0.1}')
    assert list(response.headers.items()) == [
        ('Custom-Header', 'Test'),
        ('Content-Type', 'application/json'),
        ('Content-Length', '54')
    ]

    app = webtest.TestApp(
        Response.to_json(
            HTTPStatus.ACCEPTED, body=structure,
            headers={'Custom-Header': 'Test'})
    )
    response = app.get('/')
    assert response.status_int == 202
    assert response.body == (
        b'{"Horseman":"headless","python3.8":true,"version":0.1}')
    assert list(response.headers.items()) == [
        ('Custom-Header', 'Test'),
        ('Content-Type', 'application/json'),
        ('Content-Length', '54')
    ]

    app = webtest.TestApp(
        Response.to_json(
            HTTPStatus.ACCEPTED, body=structure,
            headers={'Content-Type': 'wrong/content'})
    )
    response = app.get('/')
    assert response.status_int == 202
    assert response.body == (
        b'{"Horseman":"headless","python3.8":true,"version":0.1}')
    assert list(response.headers.items()) == [
        ('Content-Type', 'application/json'),
        ('Content-Length', '54')
    ]

    app = webtest.TestApp(
        Response.to_json(
            HTTPStatus.ACCEPTED, body=structure,
            headers={})
    )
    response = app.get('/')
    assert response.status_int == 202
    assert response.body == (
        b'{"Horseman":"headless","python3.8":true,"version":0.1}')
    assert list(response.headers.items()) == [
        ('Content-Type', 'application/json'),
        ('Content-Length', '54')
    ]


def test_json_errors():
    with pytest.raises(TypeError):
        Response.to_json(body=object())


def test_redirect():
    response = Response.redirect('/test')
    assert list(response.headers.items()) == [('Location', '/test')]
    assert response.body is None
    assert response.status == 303
    assert webtest.TestApp(response).get('/').body == (
        b'Object moved -- see Method and URL list')

    response = Response.redirect('/test', code=301)
    assert list(response.headers.items()) == [('Location', '/test')]
    assert response.body is None
    assert response.status == 301
    assert webtest.TestApp(response).get('/').body == (
        b'Object moved permanently -- see URI list'
    )

    response = Response.redirect(
        '/test', code=301, headers={"Location": "/outside"})
    assert list(response.headers.items()) == [('Location', '/test')]
    assert response.body is None
    assert response.status == 301
    assert webtest.TestApp(response).get('/').body == (
        b'Object moved permanently -- see URI list'
    )


def test_invalid_redirect():
    with pytest.raises(ValueError) as exc:
        Response.redirect('/test', code=400)
    assert str(exc.value) == '400: unknown redirection code.'
