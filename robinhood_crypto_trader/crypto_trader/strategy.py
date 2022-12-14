#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import robin_stocks.robinhood as rh

def trade1(crypto_historicals, arguments=[]):
    return 'BUY'

class Strategy():
    def __init__(self, func, arguments=[]):
        self.function = func
        self.arguments = arguments
    
    def execute(self):
        crypto_historicals = rh.crypto.get_crypto_historicals('BTC', interval='5minute', span='day', bounds='24_7')
        
        trade = eval(str(self.function) + '(crypto_historicals, self.arguments)')
        
        assert trade in ['BUY', 'SELL', 'HOLD']
        
        return trade

strat1 = Strategy('trade1')

decision = strat1.execute()