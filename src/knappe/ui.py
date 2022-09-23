import ast
import typing as t
from kavallerie.request import Request
from multimethod import multimethod
from chameleon.codegen import template
from chameleon.astutil import Symbol
from knappe.result import Result


Slot = t.Callable[[Request, str, t.Any], str]


@multimethod
def slot(request: Request, view: t.Any, context: t.Any, name: None):
    raise NotImplementedError('No slot.')


def query_slot(econtext, name):
    """Compute the result of a slot expression
    """
    request = econtext.get('request')
    view = econtext.get('view', object())
    context = econtext.get('context', object())
    try:
        result = slot(request, view, context, name)
        if isinstance(result, Result):
            assert isinstance(result.body, str)
            return result.body
        if isinstance(result, str):
            return result
        raise NotImplementedError('Slot returns unknow type.')
    except LookupError:
        # No slot found. We don't render anything.
        return None


class SlotExpr:
    """
    This is the interpreter of a slot: expression
    """
    def __init__(self, expression):
        self.expression = expression

    def __call__(self, target, engine):
        slot_name = self.expression.strip()
        value = template(
            "query_slot(econtext, name)",
            query_slot=Symbol(query_slot),  # ast of query_slot
            name=ast.Str(s=slot_name),  # our name parameter to query_slot
            mode="eval"
        )
        return [ast.Assign(targets=[target], value=value)]
