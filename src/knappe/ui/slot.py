import ast
from horseman.types import Environ
from typing import Callable, Any
from chameleon.codegen import template
from chameleon.astutil import Symbol


Slot = Callable[[Environ, str, Any], str]


def query_slot(econtext, name):
    """Compute the result of a slot expression
    """
    ui = econtext.get('ui', None)
    if ui is None:
        return None
    request = econtext.get('request')
    view = econtext.get('view', object())
    context = econtext.get('context', object())
    try:
        manager = ui.slots.find_one(request, view, context, name=name)()
    except LookupError:
        # No slot found. We don't render anything.
        return None

    slots = ui.slots.find_all(manager, request, view, context)
    return manager(request, view, context, list(slots))


def SlotExpr(name):
    name = name.strip()
    def render_slot(target, engine):
        value = template(
            "query_slot(econtext, name)",
            query_slot=Symbol(query_slot),  # ast of query_slot
            name=ast.Str(s=name),  # our name parameter to query_slot
            mode="eval"
        )
        return [ast.Assign(targets=[target], value=value)]

    return render_slot
