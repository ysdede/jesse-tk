from setuptools import setup

setup(
    name="jesse-tk",
    version='0.12',
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        jesse-tk=jessetk.__init__:cli
    ''',
)
