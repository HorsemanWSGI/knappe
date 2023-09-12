import wrapt
import typing as t
from chameleon.zpt.template import PageTemplate
from knappe.response import Response


DEFAULT = ""
Default = t.Literal[DEFAULT]


class BoundHTMLWrapper(wrapt.BoundFunctionWrapper):

    def bare(self, *args, **kwargs):
        super().bare(*args, **kwargs)

    def without_layout(self, request):
        super().without_layout(request)

    def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


class HTMLWrapper(wrapt.FunctionWrapper):

    __bound_function_wrapper__ = BoundHTMLWrapper

    def __init__(self,
                 wrapped,
                 template_name: str | None,
                 response_class: t.Type[Response],
                 default_template: PageTemplate | None,
                 layout_name: str | Default | None,
                 code: int):
        super().__init__(wrapped, self.with_layout)
        self.template_name = template_name
        self.response_class = response_class
        self.default_template = default_template
        self.layout_name = layout_name
        self.code = code

    def render(self, request, result, layout_name: str | None = None):
        ui = request.context.get('ui')
        namespace = {
            'ui': ui,
            'request': request,
            'macro': ui is not None and ui.macros.macro or None,
        }

        if not self.template_name:
            if not isinstance(result, str):
                raise TypeError('Template is missing')
            else:
                rendered = result
        elif ui is None:
            if self.default_template is None:
                raise NotImplementedError('No template.')
            rendered = self.default_template.render(**(result | namespace))
        else:
            template = ui.templates.get(
                self.template_name, self.default_template
            )
            if template is None:
                raise NotImplementedError('No template.')
            rendered = template.render(**(result | namespace))
            if layout_name is not None:
                layout = ui.layouts.find_one(
                    request, name=layout_name).value
                rendered = layout(request, rendered, namespace)
        return rendered

    def bare(self, request):
        result = self.__wrapped__(request)
        return self.render(
            request, result, layout_name=None)

    def without_layout(self, request):
        result = self.__wrapped__(request)
        if isinstance(result, Response):
            return result
        rendered = self.render(
            request, result, layout_name=None)
        return self.response_class.html(body=rendered)

    def with_layout(self, wrapped, instance, args, kwargs):
        result = wrapped(*args, **kwargs)
        if isinstance(result, Response):
            return result
        request = args[0]
        rendered = self.render(
            request, result, layout_name=self.layout_name)
        return self.response_class.html(body=rendered)


class HTMLRenderer:

    def __init__(self,
                 template_name: str | None = None,
                 response_class: t.Type[Response] = Response,
                 default_template: PageTemplate | None = None,
                 layout_name: str | Default | None = DEFAULT,
                 code=200):
        self.template_name = template_name
        self.response_class = response_class
        self.default_template = default_template
        self.layout_name = layout_name
        self.code = code

    def __call__(self, func):
        return HTMLWrapper(
            func,
            self.template_name,
            self.response_class,
            self.default_template,
            self.layout_name,
            self.code
        )


html = HTMLRenderer
