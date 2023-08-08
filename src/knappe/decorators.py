import sys
import wrapt
import orjson
import functools
import typing as t
import collections.abc
from chameleon.zpt.template import PageTemplate
from horseman.exceptions import HTTPError
from knappe.response import Response, DecoratedResponse


DEFAULT = ""
Default = t.Literal[DEFAULT]


@wrapt.decorator
def composed(wrapped, instance, args, kwargs):
    result = wrapped(*args, **kwargs)
    if isinstance(result, DecoratedResponse):
        result.layout = None
    return result


def template(
        template_name: str,
        default_template: t.Optional[PageTemplate] = None):

    @wrapt.decorator
    def renderer(wrapped, instance, args, kwargs):
        result = wrapped(*args, **kwargs)
        if not isinstance(result, collections.abc.Mapping):
            raise NotImplementedError(
                'Template rendering requires a namespace mapping.')

        request = args[0]
        if ui := request.context.get('ui'):
            template = ui.templates.get(template_name, default_template)
            namespace = {
                **result,
                'ui': ui,
                'macro': ui.macros.macro,
                'view': instance or wrapped
            }
        else:
            template = default_template
            namespace = {
                **result,
                'view': instance or wrapped
            }
        if template is None:
            raise NotImplementedError('No template.')
        return template.render(**namespace)

    return renderer


def html(
        template_name: str,
        response_class: t.Type[DecoratedResponse] = DecoratedResponse,
        default_template: t.Optional[PageTemplate] = None,
        layout_name: t.Optional[str | Default] = DEFAULT,
        code=200):

    @wrapt.decorator
    def renderer(wrapped, instance, args, kwargs):
        result = wrapped(*args, **kwargs)
        if isinstance(result, Response):
            return result

        request = args[0]
        if ui := request.context.get('ui'):
            layout = ui.layouts.find_one(request, name=layout_name).value
            try:
                template = ui.templates[template_name]
            except ValueError:
                template = default_template
        else:
            layout = None
            template = default_template

        if template is None:
            raise NotImplementedError('No template.')

        namespace = {
            'ui': ui,
            'macro': ui.macros.macro,
        }
        rendered = template.render(**(result | namespace))
        response = response_class(
            code, body=rendered, layout=layout, namespace=namespace,
            headers={
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
