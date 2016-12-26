from setuptools import setup

setup(
    name = "pynfc",
    version = "0.1",
    setup_requires = ["cffi>=1.0.0"],
    cffi_modules = ["pynfc_build.py:ffi"],
    install_requires = ["cffi>=1.0.0"],
    author = "Mike Auty",
    author_email = 'mike.auty@gmail.com',
    license = 'LGPL-3',
)
