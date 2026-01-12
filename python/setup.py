"""
ApexQuant Python 包安装脚本
"""

from setuptools import setup, find_packages

with open("../README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="apexquant",
    version="1.0.0",
    author="ApexQuant Team",
    description="AI 驱动的混合语言量化交易系统",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ApexQuant",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "akshare>=1.12.0",
        "openai>=1.10.0",
        "matplotlib>=3.8.0",
        "scikit-learn>=1.3.0",
    ],
    extras_require={
        "all": [
            "anthropic>=0.18.0",
            "xgboost>=2.0.0",
            "lightgbm>=4.1.0",
            "torch>=2.1.0",
            "ray[rllib]>=2.9.0",
            "plotly>=5.18.0",
            "mplfinance>=0.12.10",
        ],
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.12.0",
            "flake8>=7.0.0",
            "mypy>=1.8.0",
        ],
    },
)

