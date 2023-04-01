#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import robin_stocks.robinhood as rh

from optionMarketData import OptionMarketData

class Option():
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
    
    def __init__(self, config):
        self.chain_id = config['chain_id']
        self.chain_symbol = config['chain_symbol']
        self.created_at = config['created_at']
        self.expiration_date = config['expiration_date']
        self.id = config['id']
        self.issue_date = config['issue_date']
        self.min_ticks = config['min_ticks']
        self.rhs_tradability = config['rhs_tradability']
        self.state = config['state']
        self.strike_price = config['strike_price']
        self.tradability = config['tradability']
        self.type = config['type']
        self.updated_at = config['updated_at']
        self.url = config['url']
        self.sellout_datetime = config['sellout_datetime']
        self.long_strategy_code = config['long_strategy_code']
        self.short_strategy_code = config['short_strategy_code']
        
        market_data = rh.options.get_option_market_data(self.chain_symbol, self.expiration_date, self.strike_price, self.type)[0][0]
        
        self.market_data = OptionMarketData(market_data)