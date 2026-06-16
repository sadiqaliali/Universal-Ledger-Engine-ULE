from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ule-db",
    version="0.1.0",
    author="ULE Contributors",
    author_email="ule@example.com",
    description="Universal Ledger Engine - The People's Database: SQL + NoSQL + Graph + Vector with Natural Language Queries in 9 Languages",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ule-db/ule",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Database",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: Database :: Front-Ends",
    ],
    python_requires=">=3.10",
    install_requires=[
        "cryptography>=41.0.0",
        "click>=8.1.7",
        "rich>=13.7.0",
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "jinja2>=3.1.2",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "vector": ["hnswlib>=0.7.0"],
        "dev": ["pytest", "pytest-cov"],
    },
    entry_points={
        "console_scripts": [
            "ule=ule.cli:main",
        ],
    },
)
