from setuptools import find_packages, setup

setup(
    name="jesse-tk",
    version='0.40',
    packages=find_packages(),
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        jesse-tk=jessetk.__init__:cli
    ''',
    python_requires='>=3.7',
    include_package_data=True,
)
