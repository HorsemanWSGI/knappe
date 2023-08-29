from knappe.ui.templates import Templates


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