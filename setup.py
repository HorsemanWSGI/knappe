from setuptools import setup


setup(
    name='knappe',
    install_requires = [
        'chameleon',
        'horseman',
        'multimethod',
        'orjson',
        'wrapt',
    ],
    extras_require={
        'test': [
            'WebTest',
            'pytest'
        ]
    }
)
