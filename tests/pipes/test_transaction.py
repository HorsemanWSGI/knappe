import pytest
from knappe.middlewares.transaction import Transaction
from knappe.types import Request


class DummyRequest(Request):

    def __init__(self):
        self.context = {}


def test_exception(environ, transaction_manager):

    def handler(request: Request):
        raise NotImplementedError

    manager = transaction_manager()
    request = DummyRequest()
    request.context['transaction_manager'] = manager
    middleware = Transaction()(handler)

    with pytest.raises(NotImplementedError):
        middleware(request)

    assert manager.began
    assert manager.aborted
    assert not manager.committed
