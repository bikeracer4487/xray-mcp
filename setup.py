from setuptools import setup, find_packages

setup(
    name="xray-mcp",
    version="2.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "fastmcp>=0.1.0",
        "httpx>=0.25.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "xray-mcp=xray_mcp.server:main",
        ],
    },
)