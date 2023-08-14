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