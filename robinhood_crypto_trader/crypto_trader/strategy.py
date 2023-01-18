#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import robin_stocks.robinhood as rh

class Strategy():
    def __init__(self, function, arguments=[]):
        self.function = function
        self.arguments = arguments
    
    def execute(self):
        crypto_historicals = rh.crypto.get_crypto_historicals('BTC', interval='5minute', span='day', bounds='24_7')
        
        trade = eval(str(self.function) + '(crypto_historicals, self.arguments)')
        
        assert trade in ['BUY', 'SELL', 'HOLD']
        
        return trade
