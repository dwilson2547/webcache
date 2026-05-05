from setuptools import find_packages, setup

setup(
    name="dwilson-webcache-client",
    version="0.2.0",
    description="Python client for the WebCache REST API",
    py_modules=["webcache_client"],
    python_requires=">=3.11",
    install_requires=[
        "httpx>=0.27.0",
    ],
)
