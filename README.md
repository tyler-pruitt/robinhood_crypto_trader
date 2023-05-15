# robinhood_crypto_trader
An unofficial Python package for an automated cryptocurrency trader on the popular trading platform Robinhood

## Donate to this project and help support open-sourced financial software (anything helps!)

### I am happy to accept the following crypto currencies as gifts, it is much appreciated!
- Bitcoin (BTC) wallet address: `bc1qvljdr72k3tz6w8k6hpnhv3722fmsgftkeeakx8`
- Ethereum (ETH), US Dollar Coin (USDC), Polygon (MATIC), Shiba Inu (SHIB), Avalanche (AVAX), Uniswap (UNI), Chainlink (LINK), Compound (COMP), Aave (AAVE) wallet address: `0xDd5E232561177e5E48432F6BA4fD12173Bbe869A`
- Cardano (ADA) wallet address: `addr1q8g90gwc2u82fnv6m0pw7crervtslar746rxx06apfcf44cg6h5us0avc20ee2azzun58lgylyl54sjr6y9efwq86krst57w35`
- Solana (SOL) wallet address: `EzQveUMk45NmuftUSGLqRH8DUBmxzCpS3HuEchFc5t1X`
- Dogecoin (DOGE) wallet address: `DQCzww2Sz9UhtAaMZbHHGofng1ioRgTkEu`
- Ethereum Classic (ETC) wallet address: `0x42D1125fB02D0eaAA3b0D57330EC46AaF5F95F15`
- Litecoin (LTC) wallet address: `ltc1qvwzqm4jxqt0gjf7fwzxpnvtlssxtc9lutrnxsh`
- Bitcoin Cash (BCH) wallet address: `bitcoincash:qr4h4edxt5muv2ns3kls0d4ca8lezu8x9v9d4r227h`
- Tezos (XTZ) wallet address: `tz1Wexc9bv6BxCBgyXwaqmJq1RNYxXBr9aff`
- Stellar Lumens (XLM): `GB2ES2N326MZK4EGJBKN3ZARCQ5RTFQSAWIJAAKFVIIIJSCC35TXIMLB`, memo (needs to be included): `1592369023`

## New to Robinhood?
Join Robinhood with my link and we'll both pick our own free stock 🤝 https://join.robinhood.com/tylerp5773

## Installation
```
pip install robinhood-crypto-trader
```

## Example Usage

```python
import robinhood_crypto_trader.crypto_trader as rct

config = {
    # the cryptocurrencies that you want to trade
    'crypto': ['BTC', 'ETH'],
    
    'username': 'your_robinhood_username',
    'password': 'your_robinhood_password',
    'days_to_run': 1,
    
    # option to export a csv of completed crypto orders when you finish trading
    'export_csv': False,
    
    # option to plot the price of the cryptocurrency
    'plot_crypto': False,
    
    # option to plot your portfolio balance
    'plot_portfolio': False,
    
    # three modes: 'safelive' (simulating live trading on the market), 'live', and 'backtest'
    'mode': 'safelive',
    
    'backtest': {
        # the time between data points for backtesting, options are ’15second’, ‘5minute’, ‘10minute’, ‘hour’, ‘day’, or ‘week’
        'interval': '5minute',
        
        # the entire time frame to collect data points, options are ‘hour’, ‘day’, ‘week’, ‘month’, ‘3month’, ‘year’, or ‘5year’
        'span': 'hour',
        
        # the times of day to collect data points, options are ‘Regular’ (6 hours a day), ‘trading’ (9 hours a day), ‘extended’ (16 hours a day), ‘24_7’ (24 hours a day)
        'bounds': '24_7',
        
        # the number of data points needed for your strategy
        'index': 10
    },
    'trader': {
        # the time between data points for live trading or simulated live trading, options are ’15second’, ‘5minute’, ‘10minute’, ‘hour’, ‘day’, or ‘week’
        'interval': '5minute',
        
        # the entire time frame to collect data points, options are ‘hour’, ‘day’, ‘week’, ‘month’, ‘3month’, ‘year’, or ‘5year’
        'span': 'hour',
        
        # the times of day to collect data points, options are ‘Regular’ (6 hours a day), ‘trading’ (9 hours a day), ‘extended’ (16 hours a day), ‘24_7’ (24 hours a day)
        'bounds': '24_7'
    },
    
    # options are 'boll' and 'macd_rsi', user-defined functions will come in later versions
    'determine_trade_function': 'boll',
    
    # parameters to pass into boll or macd_rsi, boll(period=20, std_width=2.0) and macd_rsi(rsi_period, rsi_index, rsi_sell_level, rsi_buy_level, macd_fast_period, macd_slow_period, macd_signal_period, macd_index)
    'builtin_trade_function_arguments': [],
    
    # option to use actual cash in account or a specific amount
    'use_cash': True,
    
    # if 'use_cash' is True, 'cash' is the amount of money to start simulating trading on the market
    'cash': 2000,
    
    # the maximum number of dollars that can be lost before the trading automatically shuts down
    'loss_threshold': 50.00,
    
    # the maximum percentage lost during trading before the trading automatically shuts down
    'loss_percentage': 5,
    
    # the amount to be multiplied by your amount of holdings for a specific cryptocurrency that can be sold in one iteration
    'holdings_factor': 0.20,
    
    # the amount to be multiplied by your amount of cash that can be sold for a specific cryptocurrency in one iteration
    'cash_factor': 0.20,
    
    # options for 'buy_order_type' and 'sell_order_type' are 'market' and 'limit'
    'buy_order_type': 'market',
    'sell_order_type': 'market',
    
    'only_sell_above_average_bought_price': False, # version 1.0.8 onwards
    'only_buy_below_average_bought_price': False # version 1.0.8 onwards
}

tr = rct.Trader(config)

tr.run()

tr.logout()
```

## Documentation
Currently under development
