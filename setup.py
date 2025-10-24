"""Setup configuration for OnlyFans Deals Finder."""
from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ""

setup(
    name="onlyfans-deals-finder",
    version="1.0.0",
    description="Automated OnlyFans subscription data scraper and analyzer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="[Your Name]",
    author_email="[your.email@example.com]",
    maintainer="[Maintainer Name]",
    maintainer_email="[maintainer@example.com]",
    url="https://github.com/[username]/onlyfans-deals-finder",
    project_urls={
        "Bug Tracker": "https://github.com/[username]/onlyfans-deals-finder/issues",
        "Documentation": "https://github.com/[username]/onlyfans-deals-finder/blob/main/README.md",
        "Source Code": "https://github.com/[username]/onlyfans-deals-finder",
    },
    license="MIT",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.31.0",
        "pygments>=2.14.0",
        "colorlog>=6.7.0",
        "backoff>=2.2.0",
        "enlighten>=1.11.0",
        "selenium>=4.10.0,<5.0",
        "undetected-chromedriver>=3.5.0,<4.0",
        "price-parser>=0.4.0",
        "click>=8.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=23.0",
            "flake8>=6.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ofdeals=cli:main",
            "onlyfans-deals=cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
    ],
    keywords="onlyfans scraper selenium automation web-scraping",
)
