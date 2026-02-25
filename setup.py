from setuptools import setup

setup(
    name="pcmffi",
    version="0.1",
    cffi_modules=["pcmffi/_ffi_build.py:ffibuilder"],
)