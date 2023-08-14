from setuptools import setup


setup(
    name='knappe',
    install_requires=[
        "autoroutes",
        "chameleon",
        "horseman >= 1.0a1",
        "http_session",
        "inspect_mate",
        "itsdangerous",
        "orjson",
        "prejudice",
        "transaction",
        "wrapt",
        "ordered_set",
        "plum_dispatch"
    ],
    extras_require={
        'test': [
            'WebTest',
            'pytest',
            'pyhamcrest',
        ]
    }
)
