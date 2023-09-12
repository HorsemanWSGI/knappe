import typing as t
from transaction import TransactionManager
from prejudice import resolve_constraints
from prejudice.errors import ConstraintError
from prejudice.types import Predicates
from knappe.response import Response
from knappe.types import Handler


def bad_response(request, response):
    if isinstance(response, Response) and response.status >= 400:
        raise ConstraintError('Response is doomed.')


class Transaction:

    class Configuration(t.NamedTuple):
        veto: Predicates = (bad_response,)
        factory: t.Callable[[], TransactionManager] = (
            lambda: TransactionManager(explicit=True)
        )

    def __init__(self, *args, **kwargs):
        self.config = self.Configuration(*args, **kwargs)

    def __call__(self,
                 handler: Handler,
                 globalconf: t.Optional[t.Mapping] = None) -> Handler:

        def transaction_middleware(request):
            manager = request.context.get('transaction_manager')
            if manager is None:
                manager = self.config.factory()
                request.context['transaction_manager'] = manager

            txn = manager.begin()
            try:
                response = handler(request)
                if txn.isDoomed():
                    txn.abort()
                elif errors := resolve_constraints(
                        self.config.veto, request, response):
                    raise errors
                else:
                    txn.commit()
                return response
            except Exception:
                txn.abort()
                raise

        return transaction_middleware
