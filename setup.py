from setuptools import setup

setup(
    name='pyboinc',
    version='0.1',
    description='Python interface for BOINC',
    url='http://github.com/eczeek/pyboinc',
    author='Erik Zeek',
    author_email='zeekec@gmail.com',
    license='GPL3+',
    packages=['pyboinc'],
    scripts=['bin/pyboinc'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    install_requires=[],
    include_package_data=True,
    zip_safe=False)

