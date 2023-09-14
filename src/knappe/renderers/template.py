import collections.abc
import wrapt
from chameleon.zpt.template import PageTemplate


def template(
        template_name: str,
        default_template: PageTemplate | None = None):

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
                'ui': ui,
                'macro': ui.macros.macro,
                'view': instance or wrapped,
                'request': request,
                **result
            }
        else:
            template = default_template
            namespace = {
                'view': instance or wrapped,
                **result
            }
        if template is None:
            raise NotImplementedError('No template.')
        return template.render(**namespace)

    return renderer
