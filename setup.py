from setuptools import find_packages, setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name="jesse-tk",
    version='0.5.0',
    packages=find_packages(),
    install_requires=required,

    entry_points='''
        [console_scripts]
        jesse-tk=jessetk.__init__:cli
    ''',
    python_requires='>=3.7',
    include_package_data=True,
)
