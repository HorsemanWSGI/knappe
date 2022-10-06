import ast
import typing as t
from chameleon.astutil import Symbol
from chameleon.codegen import template
from knappe.request import Request
from knappe.response import Response
from multimethod import multimethod


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
        if isinstance(result, Response):
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


class Layout:

    def __init__(self, template):
        self.template = template

    def accepts(self, content_type: str):
        return 'text/html' in content_type

    def __call__(self, body, **namespace):
        return self.template(content=body, layout=self, **namespace)


class UI:

    def __init__(self, templates, layout=None):
        self.layout = layout
        self.templates = templates
