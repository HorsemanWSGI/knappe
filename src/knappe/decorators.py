import sys
import wrapt
import orjson
import functools
import typing as t
from horseman.exceptions import HTTPError
from knappe.response import Response, DecoratedResponse


@wrapt.decorator
def composed(wrapped, instance, args, kwargs):
    result = wrapped(*args, **kwargs)
    if isinstance(result, DecoratedResponse):
        result.layout = None
    return result


def html(
        template_name: str,
        response_class: t.Type[DecoratedResponse] = DecoratedResponse,
        default_template=None,
        code=200):
    @wrapt.decorator
    def renderer(wrapped, instance, args, kwargs):
        result = wrapped(*args, **kwargs)
        if isinstance(result, Response):
            return result
        request = args[0]
        ui = request.context.get('ui')
        if ui is None:
            layout = None
            template = default_template
        else:
            layout = ui.layout
            try:
                template = ui.templates[template_name]
            except ValueError:
                template = default_template
        if template is None:
            raise NotImplementedError('No template.')
        rendered = template.render(**result)
        response = response_class(
            code, body=rendered, layout=layout, headers={
                'Content-Type': 'text/html; charset=utf-8'
            }
        )
        response.bind(request)
        return response
    return renderer


def json(
        wrapped=None,
        *,
        response_class: t.Type[DecoratedResponse] = DecoratedResponse):
    if wrapped is None:
        return functools.partial(
            json, response_class=Response)

    @wrapt.decorator
    def renderer(wrapped, instance, args, kwargs):
        request = args[0]
        result = wrapped(request, **kwargs)
        if isinstance(result, Response):
            return result
        response = response_class(
            body=orjson.dumps(result),
            headers={'Content-Type': 'application/json'}
        )
        response.bind(request)
        return response
    return renderer(wrapped)


def context(factory):
    @wrapt.decorator
    def context_wrapper(wrapped, instance, args, kwargs):
        try:
            context = factory(*args, **kwargs)
        except LookupError:
            raise HTTPError(400)
        return wrapped(*args, context, **kwargs)
    return context_wrapper


def trigger(button):
    buttons = sys._getframe(1).f_locals.setdefault('_buttons', {})
    buttons[(button.name, button.value)] = button

    def trigger_wrapper(func):
        triggers = sys._getframe(1).f_locals.setdefault('_triggers', {})
        triggers[(button.name, button.value)] = func
        return func

    return trigger_wrapper
