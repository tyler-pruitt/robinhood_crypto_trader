#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import robin_stocks.robinhood as rh

from option import Option
from optionMarketData import OptionMarketData

def logout():
    try:
        print("logging out")
        rh.authentication.logout()
    except:
        print("already logged out")

rh.authentication.login()

try:
    options = dict()
    symbol = input("Enter stock ticker ('exit' to exit): ")
    
    while symbol.lower() != "exit":
        
        tradable_options = rh.options.find_tradable_options(symbol)
        options_to_add = []
        for i in range(len(tradable_options)):
            print(symbol + ": " + str(i+1) + "/" + str(len(tradable_options)))
            options_to_add.append(Option(tradable_options[i]))
        
        options[symbol.upper()] = options_to_add
        symbol = input("Enter stock ticker ('exit' to exit): ")
    
    logout()
except:
    logout()
