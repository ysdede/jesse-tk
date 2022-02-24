from setuptools import find_packages, setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

required.append('jesse @ git+https://github.com/ysdede/jesse.git@cache+yakirsim#egg=jesse',)

setup(
    name="jesse-tk",
    version='0.5.8',
    packages=find_packages(),
    install_requires=required,

    entry_points='''
        [console_scripts]
        jesse-tk=jessetk.__init__:cli
    ''',
    python_requires='>=3.7',
    include_package_data=True,
)
