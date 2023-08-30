from knappe.ui.templates import Templates, TemplatesChain


def test_package_loading():
    templates = Templates().register_package_resources('knappe.fixtures:templates')
    assert set(templates.registry.keys()) == {'example', 'index'}


def test_path_loading():
    templates = Templates().register_path('./templates')
    assert set(templates.registry.keys()) == {'test', 'index'}


def test_merge():
    tpl1 = Templates().register_path('./templates')
    tpl2 = Templates().register_package_resources('knappe.fixtures:templates')
    tpl3 = tpl1 | tpl2
    assert set(tpl3.registry) == {'test', 'index', 'example'}
    assert tpl3.registry['index'] == tpl2.registry['index']


def test_prefix():
    templates = Templates('base-').register_path('./templates')
    assert set(templates.registry.keys()) == {'base-test', 'base-index'}

    templates2 = Templates().register_package_resources('knappe.fixtures:templates')
    assert set(templates2.registry.keys()) == {'example', 'index'}

def test_template_chain():
    tpl1 = Templates().register_path('./templates')
    tpl2 = Templates().register_package_resources('knappe.fixtures:templates')
    chain = TemplatesChain()
    chain.register(tpl1)
    chain.register(tpl2)
    assert list(chain) == [(0, tpl1), (0, tpl2)]
    assert chain.get('index') is tpl1['index']

    chain = TemplatesChain()
    chain.register(tpl1, 2)
    chain.register(tpl2, 1)
    assert list(chain) == [(1, tpl2), (2, tpl1)]
    assert chain.get('index') is tpl2['index']