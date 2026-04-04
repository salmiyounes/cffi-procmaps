from setuptools import setup



if __name__ == "__main__":
    setup(
        cffi_modules=["pcmffi/_ffi_build.py:ffi"]
    )