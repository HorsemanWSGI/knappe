from setuptools import setup


setup(
    name='knappe',
    install_requires = [
        'autoroutes',
        'chameleon',
        'horseman >= 1.0a1',
        'http_session',
        'inspect_mate',
        'itsdangerous',
        'multimethod',
        'orjson',
        'prejudice',
        'transaction',
        'wrapt',
    ],
    extras_require={
        'test': [
            'WebTest',
            'pytest',
            'pyhamcrest',
        ]
    }
)
