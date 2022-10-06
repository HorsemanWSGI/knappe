import uuid
import pytest
from io import BytesIO
from copy import deepcopy
from frozendict import frozendict
from http_session.meta import Store
from unittest.mock import Mock, patch
from transaction import TransactionManager


class DummyTransactionManager(TransactionManager):
    _resources = []

    def __init__(self, doomed=False, retryable=False):
        self.doomed = doomed
        self.began = 0
        self.committed = 0
        self.aborted = 0
        self.active = False

    def get(self):
        return self

    def isDoomed(self):
        return self.doomed

    def begin(self):
        self.began += 1
        self.active = True
        return self

    def commit(self):
        self.committed += 1

    def abort(self):
        self.active = False
        self.aborted += 1

    def note(self, value):
        self._note = value


class SessionMemoryStore(Store):

    def __init__(self, TTL=None):
        self.data = {}
        self.touch = Mock()
        self.TTL = TTL

    def __iter__(self):
        return iter(self.data.keys())

    def get(self, sid):
        """We return a copy, to avoid mutability by reference.
        """
        data = self.data.get(sid)
        if data is not None:
            return deepcopy(data)
        return data

    def set(self, sid, session):
        self.data[sid] = session

    def clear(self, sid):
        if sid in self.data:
            self.data[sid].clear()

    def delete(self, sid):
        del self.data[sid]


@pytest.fixture
def transaction_manager():
    return DummyTransactionManager


@pytest.fixture
def http_session_store():

    def uuid_generator(count=0):
        while True:
            yield uuid.UUID(int=count)
            count += 1

    def mock_uuid(generator):
        def uuid_patch():
            return next(generator)
        return uuid_patch

    with patch('uuid.uuid4', mock_uuid(uuid_generator())):
        yield SessionMemoryStore


@pytest.fixture(scope="session")
def environ():
    return frozendict({
        'REQUEST_METHOD': 'GET',
        'SCRIPT_NAME': '',
        'PATH_INFO': '/',
        'QUERY_STRING': '',
        'SERVER_NAME': 'test_domain.com',
        'SERVER_PORT': '80',
        'HTTP_HOST': 'test_domain.com:80',
        'SERVER_PROTOCOL': 'HTTP/1.0',
        'wsgi.url_scheme': 'http',
        'wsgi.version': (1, 0),
        'wsgi.run_once': 0,
        'wsgi.multithread': 0,
        'wsgi.multiprocess': 0,
        'wsgi.input': BytesIO(b""),
        'wsgi.errors': BytesIO()
    })


@pytest.fixture(scope="session")
def json_post_environ(environ):
    return frozendict({
        **environ,
        'REQUEST_METHOD': 'POST',
        'SCRIPT_NAME': '/app',
        'PATH_INFO': '/login',
        'CONTENT_TYPE': "application/json",
        'QUERY_STRING': 'action=login&token=abcdef',
        'wsgi.input': BytesIO(
            b'''{"username": "test", "password": "test"}'''
        ),
    })
