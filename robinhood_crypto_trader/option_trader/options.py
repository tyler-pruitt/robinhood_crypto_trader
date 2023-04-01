#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import robin_stocks.robinhood as rh

class TradableOption():
    """
    {'chain_id': '71b2a769-4781-4df1-a776-222206504c43',
     'chain_symbol': 'XPEV',
     'created_at': '2023-03-02T02:05:57.413583Z',
     'expiration_date': '2023-04-14',
     'id': 'fff615b6-9334-4da9-85ba-337acfaa8ca7',
     'issue_date': '2023-03-02',
     'min_ticks': {'above_tick': '0.05',
      'below_tick': '0.01',
      'cutoff_price': '3.00'},
     'rhs_tradability': 'tradable',
     'state': 'active',
     'strike_price': '9.0000',
     'tradability': 'tradable',
     'type': 'put',
     'updated_at': '2023-03-02T02:05:57.413588Z',
     'url': 'https://api.robinhood.com/options/instruments/fff615b6-9334-4da9-85ba-337acfaa8ca7/',
     'sellout_datetime': '2023-04-14T19:30:00+00:00',
     'long_strategy_code': 'fff615b6-9334-4da9-85ba-337acfaa8ca7_L1',
     'short_strategy_code': 'fff615b6-9334-4da9-85ba-337acfaa8ca7_S1'}
    """
    
    def __init__(self):
        return

class OptionMarketData():
    """
    [[{'adjusted_mark_price': '1.610000',
       'adjusted_mark_price_round_down': '1.610000',
       'ask_price': '1.640000',
       'ask_size': 3,
       'bid_price': '1.580000',
       'bid_size': 234,
       'break_even_price': '9.390000',
       'high_price': '1.570000',
       'instrument': 'https://api.robinhood.com/options/instruments/e6324dbb-a2d4-43d8-b4b4-821881b640ea/',
       'instrument_id': 'e6324dbb-a2d4-43d8-b4b4-821881b640ea',
       'last_trade_price': '1.550000',
       'last_trade_size': 3,
       'low_price': '1.550000',
       'mark_price': '1.610000',
       'open_interest': 2033,
       'previous_close_date': '2023-03-30',
       'previous_close_price': '1.550000',
       'updated_at': '2023-03-31T19:59:59.9403136Z',
       'volume': 19,
       'symbol': 'XPEV',
       'occ_symbol': 'XPEV  230616P00011000',
       'state': 'active',
       'chance_of_profit_long': '0.399220',
       'chance_of_profit_short': '0.600780',
       'delta': '-0.402601',
       'gamma': '0.088530',
       'implied_volatility': '0.861432',
       'rho': '-0.012690',
       'theta': '-0.010335',
       'vega': '0.019638',
       'high_fill_rate_buy_price': '1.628000',
       'high_fill_rate_sell_price': '1.591000',
       'low_fill_rate_buy_price': '1.599000',
       'low_fill_rate_sell_price': '1.620000'}]]
    """
    
    def __init__(self):
        return

rh.authentication.login()

try:
    symbol = input("Enter stock ticker ('EXIT' to exit): ")
    
    while symbol.lower() != "exit":
        
        tradable_options = rh.options.find_tradable_options(symbol)
        
        print('tradable_options:', tradable_options, end='\n\n')
    
        option_market_data = rh.options.get_option_market_data(symbol, '2023-06-16', '11.0000', 'put')
        
        print('option_market_data:', option_market_data, end='\n\n')
        
        symbol = input("Enter stock ticker ('exit' to exit): ")
    
    rh.authentication.logout()
except:
    rh.authentication.logout()
