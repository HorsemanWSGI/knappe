from setuptools import setup


setup(
    name='knappe',
    install_requires = [
        'chameleon',
        'horseman >= 0.6',
        'kavallerie >= 0.3',
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
