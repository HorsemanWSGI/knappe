from chameleon.zpt import template


class Layout:

    def __init__(self, template: template.PageTemplate):
        self.template = template

    def render(self, content: str, **namespace):
        return self.template.render(
            content=content,
            layout=self,
            **namespace
        )
