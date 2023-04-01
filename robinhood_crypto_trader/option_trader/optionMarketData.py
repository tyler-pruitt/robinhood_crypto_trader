#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class OptionMarketData():
    """
    {'adjusted_mark_price': '1.610000',
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
     'chance_of_profit_long': '0.399222',
     'chance_of_profit_short': '0.600778',
     'delta': '-0.402638',
     'gamma': '0.088542',
     'implied_volatility': '0.862730',
     'rho': '-0.012650',
     'theta': '-0.010370',
     'vega': '0.019607',
     'high_fill_rate_buy_price': '1.628000',
     'high_fill_rate_sell_price': '1.591000',
     'low_fill_rate_buy_price': '1.599000',
     'low_fill_rate_sell_price': '1.620000'}
    """
    
    def __init__(self, config):
        self.adjusted_mark_price = config['adjusted_mark_price']
        self.adjusted_mark_price_round_down = config['adjusted_mark_price_round_down']
        self.ask_price = config['ask_price']
        self.ask_size = config['ask_size']
        self.bid_price = config['bid_price']
        self.bid_size = config['bid_size']
        self.break_even_price = config['break_even_price']
        self.high_price = config['high_price']
        self.instrument = config['instrument']
        self.instrument_id = config['instrument_id']
        self.last_trade_price = config['last_trade_price']
        self.last_trade_size = config['last_trade_size']
        self.low_price = config['low_price']
        self.mark_price = config['mark_price']
        self.open_interest = config['open_interest']
        self.previous_close_date = config['previous_close_date']
        self.previous_close_price = config['previous_close_price']
        self.updated_at = config['updated_at']
        self.volume = config['volume']
        self.symbol = config['symbol']
        self.occ_symbol = config['occ_symbol']
        self.state = config['state']
        self.chance_of_profit_long = config['chance_of_profit_long']
        self.chance_of_profit_short = config['chance_of_profit_short']
        self.delta = config['delta']
        self.gamma = config['gamma']
        self.implied_volatility = config['implied_volatility']
        self.rho = config['rho']
        self.theta = config['theta']
        self.vega = config['vega']
        self.high_fill_rate_buy_price = config['high_fill_rate_buy_price']
        self.high_fill_rate_sell_price = config['high_fill_rate_sell_price']
        self.low_fill_rate_buy_price = config['low_fill_rate_buy_price']
        self.low_fill_rate_sell_price = config['low_fill_rate_sell_price']