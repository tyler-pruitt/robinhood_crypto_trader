from setuptools import setup, find_packages

setup(
    name="robinhood_crypto_trader",
    version="1.0.0",
    author="Tyler Pruitt",
    description="A Python package for an automated cryptocurrency trader on the popular trading platform Robinhood",
    url="https://github.com/tyler-pruitt/robinhood_crypto_trader",
    packages=find_packages(),
    requires=[
        "numpy",
        "robin_stocks",
        "pandas",
        "matplotlib",
        "pandas_ta",
        "discord_webhook"
    ],
    install_requires=[
        "numpy",
        "robin_stocks",
        "pandas",
        "matplotlib",
        "pandas_ta",
        "discord_webhook"
    ],
    keywords=["robinhood", "crypto", "cryptocurrency", "trading", "autotrading", "investing", "robinhood crypto trader"],
    license="MIT"
)
