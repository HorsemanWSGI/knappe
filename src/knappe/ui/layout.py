from chameleon.zpt import template


class Layout:

    def __init__(self, template: template.PageTemplate):
        self.template = template

    def accepts(self, content_type: str):
        return 'text/html' in content_type

    def __call__(self, body, **namespace):
        return self.template(content=body, layout=self, **namespace)
