import pytest
from knappe.blueprint import Blueprint, apply_blueprint


def test_blueprint_no_method():

    class Somestuff:
        pass

    bp: Blueprint[Somestuff] = Blueprint(Somestuff)
    with pytest.raises(AttributeError):
        bp.call(1)


def test_blueprint_bad_args_method():

    class Somestuff:
        def call(self):
            pass

    bp: Blueprint[Somestuff] = Blueprint(Somestuff)
    with pytest.raises(TypeError):
        bp.call(1)


def test_blueprint_apply():

    called = []

    class Bad:
        pass

    class Somestuff:
        def call(self):
            called.append(True)

    class SomeOtherStuff(Somestuff):
        pass

    bp: Blueprint[Somestuff] = Blueprint(Somestuff)
    bp.call()
    assert called == []

    apply_blueprint(bp, Somestuff())
    assert called == [True]

    with pytest.raises(TypeError):
        apply_blueprint(bp, Bad())

    apply_blueprint(bp, SomeOtherStuff())
    assert called == [True, True]
