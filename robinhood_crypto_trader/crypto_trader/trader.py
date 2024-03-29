"""
Version 1.1.0 Preproduction

Last updated: 01:44 PM (PST) on January 20, 2023

Issues:
- Implement buy by quantity orders with thresholds in place to prevent orders from failing [thresholds found at rh.crypto.get_crypto_info(crypto_symbol)]
- Implement miniumum values for dollars_to_spend in self.run() so that small buy orders do not fail [thresholds found at rh.crypto.get_crypto_info(crypto_symbol)]
- Implement sell by price orders with thresholds in place to prevent orders from failing if applicable [thresholds found at rh.crypto.get_crypto_info(crypto_symbol)]

To-do:
- Implement the Strategy class from strategy.py so that users can bring in their own independent strategies to decide whether to buy, sell, or hold their cryptocurrency assets.
- [Implemented, testing required] Only have self.buy_times and self.sell_times by initialized and used if config[plot_crypto] is True
- Documentation of code
- Documentation for user guide
- [Implemented, testing required] Add option to only sell if the price of the cryptocurrency is greater than the average holdings price for that cryptocurrency
- [Implemented, testing required] Add option to only buy if the price of the cryptocurrency is less than the average holings price for that cryptocurrency
"""

import numpy as np
import pandas as pd
import datetime as dt
import time as t
import matplotlib.pyplot as plt
import pandas_ta as ta
import random as r
import sys
import robin_stocks.robinhood as rh
import math

from robinhood_crypto_trader.crypto_trader.order import *

class Trader():
    def __init__(self, config):
        """
        config = {
            'crypto': [],
            'username': '',
            'password': '',
            'days_to_run': 1,
            'export_csv': False,
            'plot_crypto': False,
            'plot_portfolio': False,
            'mode': '',
            'backtest': {
                'interval': '',
                'span': '',
                'bounds': '',
                'index': 10
            },
            'trader': {
                'interval': '',
                'span': '',
                'bounds': ''
            },
            'determine_trade_function': 'function_name',
            'builtin_trade_function_arguments': [],
            'cash': 2000,
            'use_cash': False,
            'loss_threshold': 50.00,
            'loss_percentage': 5.00,
            'holdings_factor': 0.20,
            'cash_factor': 0.20,
            'buy_order_type': 'market',
            'sell_order_type': 'market',
            'only_sell_above_average_bought_price': False,
            'only_buy_below_average_bought_price': False
        }
        """
        self.check_config(config)

        self.id = self.generate_id()
        self.crypto = config['crypto']
        self.username = config['username']
        self.password = config['password']
        self.days_to_run = config['days_to_run']
        self.export_csv_config = config['export_csv']
        self.plot_crypto_config = config['plot_crypto']
        self.plot_portfolio_config = config['plot_portfolio']
        self.mode = config['mode']
        self.determine_trade_func = config['determine_trade_function']
        self.only_sell_above_bought = config['only_sell_above_average_bought_price']
        self.only_buy_below_bought = config['only_buy_below_average_bought_price']

        self.overbought_threshold = 70
        self.oversold_threshold = 30
        
        if config.get('builtin_trade_function_arguments', []) != []:
            self.builtin_trade_function_arguments = config['builtin_trade_function_arguments']
        else:
            self.builtin_trade_function_arguments = []
        
        self.login()
        
        self.crypto_meta_data = {crypto_name: rh.crypto.get_crypto_info(crypto_name) for crypto_name in self.crypto}

        # self.buy_order_type and self.sell_order_type are only used when self.mode == 'live'
        self.buy_order_type = config['buy_order_type']
        self.sell_order_type = config['sell_order_type']

        if self.mode == 'backtest':
            self.backtest_interval = config['backtest']['interval']
            self.backtest_span = config['backtest']['span']
            self.backtest_bounds = config['backtest']['bounds']

            self.is_live = False

            if self.determine_trade_func == 'boll':
                self.backtest_index = 19
            elif self.determine_trade_func == 'macd_rsi':
                self.backtest_index = 33
            else:
                self.backtest_index = config['backtest']['index']
            
            self.total_iteration_number = self.convert_time_to_sec(self.backtest_span) // self.convert_time_to_sec(self.backtest_interval) - self.backtest_index
        else:
            self.interval = config['trader']['interval']
            self.span = config['trader']['span']
            self.bounds = config['trader']['bounds']

            if self.mode == 'live':
                self.is_live = True
            else:
                self.is_live = False
        
        if self.is_live:
            self.orders = {crypto_name: [] for crypto_name in self.crypto}
        
        self.use_cash = config['use_cash']

        self.cash, self.equity = self.retrieve_cash_and_equity()

        # Initialization of holdings and bought price (necessary to be here due to different modes and cash initializations)
        self.holdings, self.bought_price = self.get_holdings_and_bought_price()

        # Loss threshold (in dollars) taken to be a positive value
        self.loss_threshold = config['loss_threshold']

        # Loss threshold (in percent) taken to be a positive value (it is the percent of total capital lost)
        self.loss_percentage = config['loss_percentage']
        
        # Need to set initial capital
        if self.use_cash == False or self.is_live:
            self.initial_capital = self.get_crypto_holdings_capital() + self.cash
        else:
            self.initial_capital = round(config['cash'], 2)
            self.cash = round(config['cash'], 2)
        
        assert self.initial_capital > 0
        
        self.start_time = t.time()
        
        self.profit = 0.00
        self.percent_change = 0.00
        
        self.trade = ''
        
        if self.plot_crypto_config:
            # self.buy_times and self.sell_times look like {'crypto1': {datetime: status, datetime: status}, 'crypto2': {datetime: status, datetime: status}}
            # status possibilities are ['live_buy', 'simulated_buy', 'unable_to_buy', 'live_sell', 'simulated_sell', unable_to_sell']
            self.buy_times = {crypto_name: {} for crypto_name in self.crypto}
            self.sell_times = {crypto_name: {} for crypto_name in self.crypto}

        if self.plot_portfolio_config:
            self.time_data, self.portfolio_data = [], []
        
        self.iteration_number = 1

        if self.mode != 'backtest':
            self.average_iteration_runtime = 0.00
        
        self.cash_factor = config['cash_factor']
        self.holdings_factor = config['holdings_factor']

        self.trade_dict = {self.crypto[i]: 0 for i in range(0, len(self.crypto))}
        self.price_dict = {self.crypto[i]: 0 for i in range(0, len(self.crypto))}
        
        self.df_trades = pd.DataFrame(columns=self.crypto)
        self.df_prices = pd.DataFrame(columns=self.crypto)
    
    def __repr__(self):
        if self.mode != 'backtest':
            return 'Trader{\n\tid: ' + self.id + '\n\tcrypto: ' + str(self.crypto) + '\n\tmode: ' + self.mode + '\n\tdetermine_trade_function: ' + self.determine_trade_func + '\n\tcash: $' + str(self.cash) + '\n\tuse_cash: ' + str(self.use_cash) + '\n\tholdings: ' + str(self.holdings) + '\n\tbuy_order_type: ' + self.buy_order_type + '\n\tsell_order_type: ' + self.sell_order_type + '\n\tequity: $' + str(self.equity) + '\n\taverage_bought_price: ' + str(self.bought_price) + '\n\tinterval: ' + self.interval + '\n\tspan: ' + self.span + '\n\tbounds: ' + self.bounds + '\n\tloss_threshold: $' + str(self.loss_threshold) + '\n\tloss_percentage: ' + str(self.loss_percentage) + '%\n\tcash_factor: ' + str(self.cash_factor) + '\n\tholdings_factor: ' + str(self.holdings_factor) + '\n\tprofit: ' + self.display_profit() + '\n\tpercent_change: ' + self.display_percent_change() + '\n\titeration_number: ' + str(self.iteration_number) + '\n\tinitial_capital: $' + str(self.initial_capital) + '\n\truntime: ' + self.display_time(self.get_runtime()) + '\n}'
        else:
            return 'Trader{\n\tid: ' + self.id + '\n\tcrypto: ' + str(self.crypto) + '\n\tmode: ' + self.mode + '\n\tdetermine_trade_function: ' + self.determine_trade_func + '\n\tcash: $' + str(self.cash) + '\n\tuse_cash: ' + str(self.use_cash) + '\n\tholdings: ' + str(self.holdings) + '\n\tbuy_order_type: ' + self.buy_order_type + '\n\tsell_order_type: ' + self.sell_order_type + '\n\tequity: $' + str(self.equity) + '\n\taverage_bought_price: ' + str(self.bought_price) + '\n\tbacktest_interval: ' + self.backtest_interval + '\n\tbacktest_span: ' + self.backtest_span + '\n\tbacktest_bounds: ' + self.backtest_bounds + '\n\tloss_threshold: $' + str(self.loss_threshold) + '\n\tloss_percentage: ' + str(self.loss_percentage) + '%\n\tcash_factor: ' + str(self.cash_factor) + '\n\tholdings_factor: ' + str(self.holdings_factor) + '\n\tprofit: ' + self.display_profit() + '\n\tpercent_change: ' + self.display_percent_change() + '\n\titeration_number: ' + str(self.iteration_number) + '\n\tinitial_capital: $' + str(self.initial_capital) + '\n\truntime: ' + self.display_time(self.get_runtime()) + '\n}'
    
    def run(self):
        try:
            print("cryptos: ", self.crypto)
    
            if self.mode == 'backtest':
                crypto_historicals = self.download_backtest_data()
            
            while self.continue_trading():
                if self.mode != 'backtest':
                    self.iteration_runtime_start = t.time()
                
                if self.mode == 'backtest':
                    if self.backtest_index == len(crypto_historicals[self.crypto[0]]):
                        print("backtesting finished")
                        
                        break
                    elif self.backtest_index > len(crypto_historicals[self.crypto[0]]):
                        print("not enough backtesting data to perform calculations")
                        
                        break
                
                prices = []
                
                if self.mode != 'backtest':
                    for crypto_symbol in self.crypto:
                        prices += [round(float(self.get_latest_quote(crypto_symbol)['ask_price']), self.get_precision(self.crypto_meta_data[crypto_symbol]['min_order_price_increment']))]
                else:
                    for i in range(len(self.crypto)):
                        prices += [round(float(crypto_historicals[self.crypto[i]][self.backtest_index]['close_price']), self.get_precision(self.crypto_meta_data[self.crypto[i]]['min_order_price_increment']))]
                
                if self.use_cash == False or self.is_live:
                    # Update holdings and bought_price
                    self.holdings, self.bought_price = self.get_holdings_and_bought_price()
    
                    # Update cash and equity
                    self.cash, self.equity = self.retrieve_cash_and_equity()
                else:
                    # Update equity only
                    _, self.equity = self.retrieve_cash_and_equity()
                
                # Set the profit and percent change for the trader
                # self.set_profit(self.cash + self.get_crypto_holdings_capital() - self.initial_capital)
                self.profit = self.cash + self.get_crypto_holdings_capital() - self.initial_capital
                # self.set_percent_change(((self.cash + self.get_crypto_holdings_capital() - self.initial_capital) * 100) / self.initial_capital)
                self.percent_change = ((self.cash + self.get_crypto_holdings_capital() - self.initial_capital) * 100) / self.initial_capital
    
                # Update console
                self.update_output()
    
                if self.plot_portfolio_config:
                    self.time_data += [self.get_runtime()]
                    self.portfolio_data += [self.cash + self.get_crypto_holdings_capital()]
    
                    self.plot_portfolio()
                
                for i, crypto_name in enumerate(self.crypto):
                    price = prices[i]
                    
                    print('\n{} = ${}'.format(crypto_name, price))
    
                    if self.mode != 'backtest':
                        trade = self.determine_trade(crypto_name)
                    else:
                        trade = self.determine_trade(crypto_name, crypto_historicals)
                    
                    print('trade:', trade, end='\n\n')
    
                    # Update cash for buy or sell calculations
                    if self.use_cash == False or self.is_live:
                        self.cash, self.equity = self.retrieve_cash_and_equity()
    
                    if trade == 'BUY':
                        if self.mode != 'backtest':
                            price = round(float(self.get_latest_quote(crypto_name)['ask_price']), self.get_precision(self.crypto_meta_data[crypto_symbol]['min_order_price_increment']))
                        
                        if self.cash > 0:
                            
                            restricted_buy = False
                            
                            if self.only_buy_below_bought:
                                if self.bought_price[crypto_name] <= price:
                                    print('Price is not lower than average bought price')
                                    restricted_buy = True
                            
                            if not restricted_buy:
                                # https://robin-stocks.readthedocs.io/en/latest/robinhood.html#placing-and-cancelling-orders

                                dollars_to_spend = self.round_down_to_2(self.cash * self.cash_factor)

                                print('Attempting to BUY ${} of {} at price ${}'.format(dollars_to_spend, crypto_name, price))

                                if self.is_live:

                                    if self.buy_order_type == 'limit':
                                        # Limit order by price
                                        order_info = rh.orders.order_buy_crypto_limit_by_price(symbol=crypto_name, amountInDollars=dollars_to_spend, limitPrice=price, timeInForce='gtc', jsonify=True)

                                    else:
                                        # Market order
                                        order_info = rh.orders.order_buy_crypto_by_price(symbol=crypto_name, amountInDollars=dollars_to_spend, timeInForce='gtc', jsonify=True)

                                    self.orders[crypto_name] += [Order(order_info)]

                                    print("Order info:", order_info)

                                    if self.plot_crypto_config:
                                        self.buy_times[crypto_name][dt.datetime.now()] = 'live_buy'
                                else:
                                    # Simulate buying the crypto by subtracting from cash, adding to holdings, and adjusting average bought price

                                    self.cash -= dollars_to_spend

                                    holdings_to_add = round(dollars_to_spend / price, self.get_precision(self.crypto_meta_data[crypto_name]['min_order_quantity_increment']))

                                    self.bought_price[crypto_name] = round( ((self.bought_price[crypto_name] * self.holdings[crypto_name]) + (holdings_to_add * price)) / (self.holdings[crypto_name] + holdings_to_add), self.get_precision(self.crypto_meta_data[crypto_name]['min_order_price_increment']))

                                    self.holdings[crypto_name] += holdings_to_add

                                    trade = 'SIMULATION BUY'

                                    if self.plot_crypto_config:
                                        if self.mode == 'safelive':
                                            self.buy_times[crypto_name][dt.datetime.now()] = 'simulated_buy'
                                        else:
                                            self.buy_times[crypto_name][self.convert_timestamp_to_datetime(crypto_historicals[i][self.backtest_index]['begins_at'])] = 'simulated_buy'
                            else:
                                trade = "UNABLE TO BUY (BOUGHT PRICE)"

                                if self.plot_crypto_config:
                                    if self.mode != 'backtest':
                                        self.buy_times[crypto_name][dt.datetime.now()] = 'unable_to_buy'
                                    else:
                                        self.buy_times[crypto_name][self.convert_timestamp_to_datetime(crypto_historicals[i][self.backtest_index]['begins_at'])] = 'unable_to_buy'
                        else:
                            print('Not enough cash')
    
                            trade = "UNABLE TO BUY (NOT ENOUGH CASH)"
                            
                            if self.plot_crypto_config:
                                if self.mode != 'backtest':
                                    self.buy_times[crypto_name][dt.datetime.now()] = 'unable_to_buy'
                                else:
                                    self.buy_times[crypto_name][self.convert_timestamp_to_datetime(crypto_historicals[i][self.backtest_index]['begins_at'])] = 'unable_to_buy'
                    elif trade == 'SELL':
                        if self.holdings[crypto_name] > 0:
                            
                            # https://robin-stocks.readthedocs.io/en/latest/robinhood.html#placing-and-cancelling-orders
    
                            if self.mode != 'backtest':
                                price = round(float(self.get_latest_quote(crypto_name)['ask_price']), self.get_precision(self.crypto_meta_data[crypto_symbol]['min_order_price_increment']))
                            
                            
                            
                            restricted_sell = False
                            
                            if self.only_sell_above_bought:
                                if self.bought_price[crypto_name] >= price:
                                    print('Price is not higher than average bought price')
                                    restricted_sell = True
                            
                            if not restricted_sell:
                                holdings_to_sell = round(self.holdings[crypto_name] * self.holdings_factor, self.get_precision(self.crypto_meta_data['min_order_quantity_increment']))

                                print('Attempting to SELL {} of {} at price ${} for ${}'.format(holdings_to_sell, crypto_name, price, round(holdings_to_sell * price, 2)))

                                if self.is_live:

                                    if self.sell_order_type == 'limit':
                                        # Limit order by price for a set quantity
                                        order_info = rh.orders.order_sell_crypto_limit(symbol=crypto_name, quantity=holdings_to_sell, limitPrice=price, timeInForce='gtc', jsonify=True)

                                    else:
                                        # Market order
                                        order_info = rh.orders.order_sell_crypto_by_quantity(symbol=crypto_name, quantity=holdings_to_sell, timeInForce='gtc', jsonify=True)


                                    self.orders[crypto_name] += [Order(order_info)]

                                    print("Order info:", order_info)

                                    if self.plot_crypto_config:
                                        self.sell_times[crypto_name][dt.datetime.now()] = 'live_sell'
                                else:
                                    # Simulate selling the crypto by adding to cash and substracting from holdings
                                    self.cash += round(holdings_to_sell * price, 2)

                                    self.holdings[crypto_name] -= holdings_to_sell

                                    # Average bought price is unaffected when selling
                                    if self.holdings[crypto_name] == 0:
                                        self.bought_price[crypto_name] = 0

                                    trade = 'SIMULATION SELL'
                                    if self.plot_crypto_config:
                                        if self.mode == 'safelive':
                                            self.sell_times[crypto_name][dt.datetime.now()] = 'simulated_sell'
                                        else:
                                            self.sell_times[crypto_name][self.convert_timestamp_to_datetime(crypto_historicals[i][self.backtest_index]['begins_at'])] = 'simulated_sell'
                            else:
                                trade = 'UNABLE TO SELL (BOUGHT PRICE)'

                                if self.plot_crypto_config:
                                    if self.mode != 'backtest':
                                        self.sell_times[crypto_name][dt.datetime.now()] = 'unable_to_sell'
                                    else:
                                        self.sell_times[crypto_name][self.convert_timestamp_to_datetime(crypto_historicals[i][self.backtest_index]['begins_at'])] = 'unable_to_sell'
                        else:
                            print("Not enough holdings")
    
                            trade = 'UNABLE TO SELL (NOT ENOUGH HOLDINGS)'
                            
                            if self.plot_crypto_config:
                                if self.mode != 'backtest':
                                    self.sell_times[crypto_name][dt.datetime.now()] = 'unable_to_sell'
                                else:
                                    self.sell_times[crypto_name][self.convert_timestamp_to_datetime(crypto_historicals[i][self.backtest_index]['begins_at'])] = 'unable_to_sell'
                    
                    self.price_dict[crypto_name] = price
                    
                    self.trade_dict[crypto_name] = trade
                
                self.df_trades, self.df_prices = self.build_dataframes()
    
                print('\ndf_prices \n', self.df_prices, end='\n\n')
                print('df_trades \n', self.df_trades, end='\n\n')
    
                if self.mode != 'backtest':
                    self.iteration_runtime_end = t.time()
    
                    if self.average_iteration_runtime == 0:
    
                        self.average_iteration_runtime = self.iteration_runtime_end - self.iteration_runtime_start
                    else:
                        # Update average iteration runtime
                        self.average_iteration_runtime *= self.iteration_number
    
                        self.average_iteration_runtime += (self.iteration_runtime_end - self.iteration_runtime_start)
    
                        self.average_iteration_runtime /= (self.iteration_number + 1)
                    
                    # wait_time = self.convert_time_to_sec(self.get_interval()) - self.average_iteration_runtime
                    wait_time = self.convert_time_to_sec(self.interval) - self.average_iteration_runtime
    
                    if wait_time < 0:
                        wait_time = 0
                    
                    if wait_time > 0:
                        print('Waiting ' + str(round(wait_time, 2)) + ' seconds...')
    
                        t.sleep(wait_time)
                else:
                    self.backtest_index += 1
                
                self.iteration_number += 1
            
            if self.export_csv_config:
                self.export_csv()
        
        except KeyboardInterrupt:
            print("User ended execution of program.")
            
            if self.export_csv_config:
                print("Exporting csv...")
                self.export_csv()
            
            self.logout()
        
        except TypeError:
            # Robinhood Internal Error
            # 503 Server Error: Service Unavailable for url: https://api.robinhood.com/marketdata/forex/quotes/76637d50-c702-4ed1-bcb5-5b0732a81f48/
            print("Robinhood Internal Error: TypeError: continuing trading")
            
            # Continue trading
            self.run()
        
        except KeyError:
            # Robinhood Internal Error
            # 503 Service Error: Service Unavailable for url: https://api.robinhood.com/portfolios/
            # 500 Server Error: Internal Server Error for url: https://api.robinhood.com/portfolios/
            print("Robinhood Internal Error: KeyError: continuing trading")
            
            # Continue trading
            self.run()
        
        except Exception:
            print("An unexpected error occured: stopping trading")

            if self.export_csv_config:
                print("Exporting csv...")
                self.export_csv()
            
            self.logout()
            
            raise Exception
    
    def generate_id(self):
        """
        Generates a random id string consisting of letters and numbers that is 12 digits long
        """
        letters_and_numbers = 'abcdefghijklmnopqrstuvwxyz0123456789'
        id = ''
        
        # id = '############'
        for i in range(12):
            id += letters_and_numbers[r.randint(0, len(letters_and_numbers)-1)]
        
        return id
    
    def get_precision(self, text):
        """
        Returns the number of decimal places the number has
        
        text needs to contain one and only one '1' and one and only one '.'
        
        E.g. text: output
        '100.000000000000': -2
        '10.0000000000000': -1
        '1.00000000000000': 0
        '0.10000000000000': 1
        '0.01000000000000': 2
        '0.00100000000000': 3
        '0.00010000000000': 4
        """
        one = text.find('1')
        dot = text.find('.')
        
        if one < dot:
            return one - dot + 1
        else:
            return one - dot
    
    def round_down_to_2(self, value):
        """
        Converts a float to two decimal places and rounds down

        E.g.
        26.537 -> 26.53
        26.531 -> 26.53
        -26.539 -> -26.53
        """
        if value < 0:
            return math.ceil(value * 100)/100.0
        else:
            return math.floor(value * 100)/100.0
    
    def login(self):
        """
        Logs the user in with username and password with verification by sms text. This method does not store the session.
        """
        time_logged_in = 60 * 60 * 24 * self.days_to_run
        
        rh.authentication.login(username=self.username,
                                password=self.password,
                                expiresIn=time_logged_in,
                                scope='internal',
                                by_sms=True,
                                store_session=False)
        
        print("login successful")
    
    def logout(self):
        """
        Attempts to log out the user unless already logged out.
        """
        try:
            rh.authentication.logout()
            
            print('logout successful')
        except:
            print('already logged out: logout() can only be called when currently logged in')
    
    def retrieve_cash_and_equity(self):
        """
        Returns cash, equity as floats from robin_stocks.robinhood.account.build_user_profile() rounded to two decimal places
        """
        rh_cash = rh.account.build_user_profile()
        
        cash = round(float(rh_cash['cash']), 2)
        equity = round(float(rh_cash['equity']), 2)
        
        return cash, equity
    
    def payment(self, crypto_symbol, amount):
        """
        Need to finish implementation
        """
        # Ensure that there are enough holdings to send
        if self.holdings[crypto_symbol] < amount:
            return
        
        crypto_id = rh.crypto.get_crypto_id(crypto_symbol)

        # Ensure that all possible crypto_symbol can be found using payment_address
        # E.g. 'BTC' and 'BTC-USD' need to both point to Bitcoin
        payment_address = {}

        receive_address = payment_address.get(crypto_symbol)

        if receive_address == None:
            # Not possible to transfer crypto
            return
        else:
            # Send the amount in crypto to receive_address
            return
    
    def get_latest_quote(self, crypto_symbol):
        """
        Returns a string of the latest quote of the cryptocurrency.
        """
        return rh.crypto.get_crypto_quote(crypto_symbol)
    
    def get_crypto_holdings_capital(self):
        """
        Returns the current dollar value of crypto assets rounded to two decimal places
        """
        capital = 0.00
            
        for crypto_name, crypto_amount in self.holdings.items():
            capital += crypto_amount * float(self.get_latest_quote(crypto_name)['mark_price'])
        
        return round(capital, 2)
    
    def convert_time_to_sec(self, time_str):
        """
        Input:
            time (str)
        Output:
            sec (int): time in seconds
        """
        assert type(time_str) == str
        
        digit = 1
        
        for i in range(1, len(time_str)):
            try:
                digit = int(time_str[:i])
            except ValueError:
                break
        
        time_str = time_str[i-1:]
        
        if time_str == 'second':
            sec = digit
        elif time_str == 'minute':
            sec = 60 * digit
        elif time_str == 'hour':
            sec = 3600 * digit
        elif time_str == 'day':
            sec = 86400 * digit
        elif time_str == 'week':
            sec = 604800 * digit
        else:
            raise ValueError
        
        return sec
    
    def update_output(self):
        """
        Prints out the lastest information out to console
        """
        
        if self.mode != 'backtest':
            print("======================ITERATION " + str(self.iteration_number) + "======================")
        else:
            print("======================ITERATION " + str(self.iteration_number) + '/' + str(self.total_iteration_number) + "======================")
        
        print("mode: " + self.mode)
        print("runtime: " + self.display_time(self.get_runtime()))
        
        print("equity: $" + str(round(self.equity, 2)))
        
        print('crypto holdings:')
        print(self.display_holdings())
        
        print("crypto equity: $" + str(round(self.get_crypto_holdings_capital(), 2)))
        print("cash: $" + str(round(self.cash, 2)))
        print("crypto equity and cash: $" + str(round(self.cash + self.get_crypto_holdings_capital(), 2)))
        
        print("profit: " + self.display_profit() + " (" + self.display_percent_change() + ")")

        if self.is_live:
            print("number of pending orders:", len(get_all_open_orders()))
            print("number of orders:", {crypto_symbol: len(self.orders[crypto_symbol]) for crypto_symbol in self.crypto})
    
    def build_dataframes(self):
        """
        Need to determine if self.df_trades and self.df_prices are changed and therefore do not need to be returned
        """
        time_now = str(dt.datetime.now().time())[:8]
        
        self.df_trades.loc[time_now] = self.trade_dict
        self.df_prices.loc[time_now] = self.price_dict
        
        return self.df_trades, self.df_prices
    
    def build_holdings(self):
        """
        Returns {
            'crypto1': {
                'price': '76.24',
                'quantity': '2.00',
                'average_buy_price': '79.26',
                },
            'crypto2': {
                'price': '76.24',
                'quantity': '2.00',
                'average_buy_price': '79.26',
                }}
        """
        
        holdings_data = rh.crypto.get_crypto_positions()
        
        build_holdings_data = dict()
        
        for i in range(len(holdings_data)):
            nested_data = dict()
            
            nested_data['price'] = self.get_latest_quote(holdings_data[i]["currency"]["code"])['mark_price']
            nested_data['quantity'] = holdings_data[i]["quantity"]
            
            try:
                nested_data['average_buy_price'] = str(float(holdings_data[i]["cost_bases"][0]["direct_cost_basis"]) / float(nested_data["quantity"]))
            except ZeroDivisionError:
                nested_data['average_buy_price'] = '-'
            
            build_holdings_data[holdings_data[i]["currency"]["code"]] = nested_data
        
        return build_holdings_data
    
    def get_holdings_and_bought_price(self):
        """
        Returns two dictionaries, holdings and bought_price, in the following format
        E.g.
            holdings = {'BTC': 1.25, 'ETH': 0.50}
            bought_price = {'BTC': 19784.21, 'ETH': 1923.61}
        """
        holdings = {self.crypto[i]: 0 for i in range(0, len(self.crypto))}
        bought_price = {self.crypto[i]: 0 for i in range(0, len(self.crypto))}
        
        rh_holdings = self.build_holdings()

        for crypto_symbol in self.crypto:
            try:
                holdings[crypto_symbol] = round(float(rh_holdings[crypto_symbol]['quantity']), self.get_precision(self.crypto_meta_data[crypto_symbol]['min_order_quantity_increment']))
                
                bought_price[crypto_symbol] = round( float(rh_holdings[crypto_symbol]['average_buy_price']), self.get_precision(self.crypto_meta_data[crypto_symbol]['min_order_price_increment']))
            except:
                holdings[crypto_symbol] = 0
                bought_price[crypto_symbol] = 0

        return holdings, bought_price
    
    def display_holdings(self):
        """
        Returns a string listing the amount of crypto held and the latest price to be printed out
        """
        text = ''

        for crypto, amount in self.holdings.items():
            
            text += '\t' + str(amount) + ' ' + crypto + " at $" + str(round(float(self.get_latest_quote(crypto)['mark_price']), self.get_precision(self.crypto_meta_data[crypto]['min_order_price_increment']))) + '\n'
        
        text = text[:-2]
        
        return text
        
    def download_backtest_data(self):
        """
        Returns historical crypto data for every crypto in self.crypto
        
        Assumes that self.mode is 'backtest'
        """
        crypto_historical_data = {}
        
        for i in range(len(self.crypto)):
            
            crypto_historical_data[self.crypto[i]] = rh.crypto.get_crypto_historicals(symbol=self.crypto[i], interval=self.backtest_interval, span=self.backtest_span, bounds=self.backtest_bounds)
        
        print("downloading backtesting data finished")
        
        return crypto_historical_data
    
    def export_csv(self):
        """
        Exports a csv of completed crypto orders
        """
        rh.export.export_completed_crypto_orders('./', 'completed_crypto_orders')
    
    def check_config(self, config):
        """
        Assures that the configuration is as expected. Raises an exception if an error is found.
        """
        assert type(config['days_to_run']) == int and config['days_to_run'] >= 1

        assert type(config['username']) == str and type(config['password']) == str
        
        assert len(config['username']) > 0 and len(config['password']) > 0
        
        assert config['mode'] in ['live', 'backtest', 'safelive']
        
        assert type(config['export_csv']) == bool
        
        assert type(config['plot_crypto']) == bool
        
        assert type(config['plot_portfolio']) == bool

        assert type(config['crypto']) == list and len(config['crypto']) > 0

        assert type(config['loss_threshold']) == float or type(config['loss_threshold']) == int
        
        assert config['loss_threshold'] >= 0

        assert type(config['loss_percentage']) == float or type(config['loss_percentage']) == int
        
        assert config['loss_percentage'] >= 0
        
        assert type(config['determine_trade_function']) == str
        
        assert type(config['only_buy_below_average_bought_price']) == bool
        
        assert type(config['only_sell_above_average_bought_price']) == bool
        
        assert type(config.get('builtin_trade_function_arguments', [])) == list

        assert type(config['cash_factor']) == int or type(config['cash_factor']) == float
        
        assert config['cash_factor'] >= 0 and config['cash_factor'] <= 1

        assert type(config['holdings_factor']) == int or type(config['holdings_factor']) == float
        
        assert config['holdings_factor'] > 0 and config['holdings_factor'] <= 1

        assert type(config['buy_order_type']) == str

        assert type(config['sell_order_type']) == str

        order_types = ['market', 'limit']

        assert config['buy_order_type'] in order_types

        assert config['sell_order_type'] in order_types
        
        # Use rh.crypto.get_crypto_currency_pairs() for 'pairs' so that it is up-to-date
        
        crypto_pair_data = rh.crypto.get_crypto_currency_pairs()
        
        pairs = []
        
        for i in range(len(crypto_pair_data)):
            if crypto_pair_data[i]['tradability'] == 'tradable':
                pairs += [crypto_pair_data[i]['asset_currency']['code']]
                pairs += [crypto_pair_data[i]['symbol']]
        
        for i in range(len(config['crypto'])):
            assert config['crypto'][i] in pairs
        
        assert type(config['use_cash']) == bool
        
        if config['use_cash']:
            assert type(config['cash']) == float or type(config['cash']) == int
            
            assert config['cash'] > 0
        
        intervals = ['15second', '5minute', '10minute', 'hour', 'day', 'week']
        spans = ['hour', 'day', 'week', 'month', '3month', 'year', '5year']
        bounds = ['Regular', 'trading', 'extended', '24_7']
        
        if config['mode'] == 'backtest':
            assert type(config['backtest']['interval']) == str
            
            assert config['backtest']['interval'] in intervals
            
            assert type(config['backtest']['span']) == str
            
            assert config['backtest']['span'] in spans
            
            assert type(config['backtest']['bounds']) == str
            
            assert config['backtest']['bounds'] in bounds

            functions = ['boll', 'macd_rsi']

            if config['determine_trade_function'] not in functions:
                assert type(config['backtest']['index']) == int

                assert config['backtest']['index'] >= 0
            
            assert config['use_cash'] == True
        elif config['mode'] == 'live':
            
            assert config['use_cash'] == False
        
        if config['mode'] == 'live' or config['mode'] == 'safelive':
            assert type(config['trader']['interval']) == str

            assert config['trader']['interval'] in intervals

            assert type(config['trader']['span']) == str

            assert config['trader']['span'] in spans

            assert type(config['trader']['bounds']) == str

            assert config['trader']['bounds'] in bounds
        
        print("configuration test: PASSED")
    
    def set_loss_percentage(self, loss_percentage):
        if loss_percentage >= 0:
            self.loss_percentage = loss_percentage
        else:
            print('Loss percentage (%) must be set to a POSITIVE value: loss percentage not reset')
    
    def continue_trading(self, override=None):
        """
        Returns true if loss has not exceeded loss threshold or loss percentage threshold. If either loss threshold or loss percentage threshold have been passed then False is returned.
        If the bool parameter override is passed into the function, then override is returned by the function.
        """
        if override != None:
            assert type(override) == bool
            
            return override
        else:
            if self.profit >= -1 * self.loss_threshold:
                if self.percent_change >= -1 * self.loss_percentage:
                    return True
                else:
                    print("Loss percentage exceeded " + str(self.loss_percentage) + "%: terminating automated trading")
                    
                    return False
            else:
                print("Loss exceeded $" + str(self.loss_threshold) + ": terminating automated trading")
                
                return False
    
    def display_time(self, seconds, granularity=5):
        result = []
        
        intervals = (
        ('weeks', 604800),  # 60 * 60 * 24 * 7
        ('days', 86400),    # 60 * 60 * 24
        ('hours', 3600),    # 60 * 60
        ('minutes', 60),
        ('seconds', 1),
        )
    
        for name, count in intervals:
            value = seconds // count
            if value:
                seconds -= value * count
                if value == 1:
                    name = name.rstrip('s')
                result.append("{} {}".format(value, name))
        
        
        return ', '.join(result[:granularity])
    
    def set_loss_threshold(self, loss):
        if loss >= 0:
            self.loss_threshold = loss
        else:
            print("Loss threshold (in dollars) must be set to a POSITIVE value: loss threshold not reset")
    
    def get_runtime(self):
        """
        Returns the runtime in seconds
        """
        return t.time() - self.start_time
    
    def display_profit(self):

        if self.profit >= 0:
            text = '+$'
        else:
            text = '-$'

        text += str(abs(round(self.profit, 2)))

        return text
    
    def display_percent_change(self):

        if self.percent_change >= 0:
            text = '+'
        else:
            text = '-'

        text += str(abs(round(self.percent_change, 2)))
        text += '%'

        return text
    
    def get_historical_data(self, crypto_symbol):
        """
        Returns historical crypto data for crypto_symbol.
        Assumes self.mode is either 'live' or 'safelive'.
        """
        historical_data = rh.crypto.get_crypto_historicals(crypto_symbol, interval=self.interval, span=self.span, bounds=self.bounds)
        
        # df contains all the data (eg. time, open, close, high, low, volume, session, interpolated, symbol)
        df = pd.DataFrame(historical_data)
        
        return df
    
    def get_historical_times(self, crypto_symbol):
        # df contains all the data (eg. time, open, close, high, low)
        df = self.get_historical_data(crypto_symbol)
        
        dates_times = pd.to_datetime(df.loc[:, 'begins_at'])
        
        return dates_times

    def get_historical_prices(self, crypto_symbol):
        # df contains all the data (eg. time, open, close, high, low)
        df = self.get_historical_data(crypto_symbol)

        dates_times = pd.to_datetime(df.loc[:, 'begins_at'])
        close_prices = df.loc[:, 'close_price'].astype('float')

        df_price = pd.concat([close_prices, dates_times], axis=1)
        df_price = df_price.rename(columns={'close_price': crypto_symbol})
        df_price = df_price.set_index('begins_at')

        return df_price
    
    def convert_dataframe_to_list(self, df, is_nested=False):
        df = df.to_numpy()
        
        data = []
        
        for i in range(len(df)):
            if is_nested:
                data.append(df[i][0])
            else:
                data.append(df[i])
        
        return data
    
    def determine_trade(self, crypto_symbol, crypto_historicals=None):
        if self.mode == 'backtest':
            assert crypto_historicals != None
            
            # Set times and prices given stock_historicals
            times, prices = [], []
            
            for k in range(len(crypto_historicals[crypto_symbol])):
                times += [crypto_historicals[crypto_symbol][k]['begins_at']]
                
                prices += [float(crypto_historicals[crypto_symbol][k]['close_price'])]
        else:
            df_historical_prices = self.get_historical_prices(crypto_symbol)
            
            # https://pandas.pydata.org/docs/reference/api/pandas.Timestamp.html#pandas.Timestamp
            times = self.convert_dataframe_to_list(self.get_historical_times(crypto_symbol))
            prices = self.convert_dataframe_to_list(df_historical_prices, True)
        
        if self.determine_trade_func in ['boll', 'macd_rsi']:
            trade = eval('self.' + self.determine_trade_func + '(crypto_symbol, times, prices)')
        else:
            # Need to finish implementation for personalized trading strategies
            trade = 'HOLD'
            print("Setting trade to default value of 'HOLD'")
            assert trade in ['BUY', 'SELL', 'HOLD']

            self.trade = trade
        
        if self.plot_crypto_config:
            self.plot_crypto(crypto_symbol, prices, times)
        
        return trade

    def macd_rsi(self, crypto_name, times, prices):
        """
        Determines whether the trade is a 'BUY', 'SELL', or 'HOLD'
        
        If both RSI and MACD are cross their respective thresholds, then either buy or sell
        Else hold
        """

        """
        Start Helper Functions
        """
        def RSI(times, prices, period):
            """
            Relative Strength Index (RSI)
            """
            
            assert len(times) == len(prices)
            assert len(times) >= period + 2
            assert len(prices) >= period + 2
            
            RSI = []
            
            for i in range(1, len(prices) - period):
                count_gain, count_loss = 0, 0
                
                for j in range(i, i + period):
                    if prices[j] - prices[j-1] > 0:
                        count_gain += 1
                    elif prices[j] - prices[j-1] < 0:
                        count_loss += 1
                
                avgU = count_gain / period
                avgD = count_loss / period
                
                try:
                    RSI.append([times[j+1], 100 - 100 / (1 + (avgU / avgD))])
                except ZeroDivisionError:
                    RSI.append([times[j+1], 100])
            
            return RSI
        
        def MACD(times, prices, fast_period, slow_period, signal_period):
            """
            Moving Average Convergence Divergence (MACD)
            """

            def EMA(times, prices, period):
                """
                Exponential Moving Average (EMA)
                """
                
                assert len(times) == len(prices)
                
                ema = []
                
                # First calculate the moving average for the first length
                ma = 0
                
                for i in range(period):
                    ma += prices[i]
                
                ma /= period
                
                
                ema.append([times[period-1], ma])
                
                multiplier = 2 / (period + 1)
                
                # Calculate the EMA for the rest of the lengths
                for i in range(period, len(prices)):
                    ema.append([times[i], (prices[i] * multiplier + (ema[-1][1] * (1 - multiplier)))])
                
                return ema
            
            assert len(times) == len(prices)
            assert len(times) >= slow_period + signal_period - 1
            assert len(prices) >= slow_period + signal_period - 1
            
            macd = []
            signal = []
            
            fast = EMA(times, prices, fast_period)
            
            slow = EMA(times, prices, slow_period)
            
            for i in range(len(slow)):
                for j in range(len(fast)):
                    if slow[i][0] == fast[j][0]:
                        macd.append([slow[i][0], fast[j][1] - slow[i][1]])
            
            macd_times, macd_values = [], []
            
            for i in range(len(macd)):
                macd_times.append(macd[i][0])
                macd_values.append(macd[i][1])
            
            signal = EMA(macd_times, macd_values, signal_period)
            
            return macd, signal
        """
        End Helper Functions
        """
        if self.builtin_trade_function_arguments == []:
            rsi_period, rsi_index, rsi_sell_level, rsi_buy_level, macd_fast_period, macd_slow_period, macd_signal_period, macd_index = 14, -16, 70, 30, 12, 26, 9, -34
        else:
            rsi_period, rsi_index, rsi_sell_level, rsi_buy_level, macd_fast_period, macd_slow_period, macd_signal_period, macd_index = self.builtin_trade_function_arguments[0], self.builtin_trade_function_arguments[1], self.builtin_trade_function_arguments[2], self.builtin_trade_function_arguments[3], self.builtin_trade_function_arguments[4], self.builtin_trade_function_arguments[5], self.builtin_trade_function_arguments[6], self.builtin_trade_function_arguments[7]
        
        rsi_data = RSI(times[rsi_index:], prices[rsi_index:], rsi_period)
        
        assert len(rsi_data) == 1
        
        if rsi_data[-1][1] > rsi_sell_level:
            rsi_indicator = "SELL"
        elif rsi_data[-1][1] < rsi_buy_level:
            rsi_indicator = "BUY"
        else:
            rsi_indicator = "HOLD"
        
        macd, signal = MACD(times[macd_index:], prices[macd_index:], macd_fast_period, macd_slow_period, macd_signal_period)
        macd_signal_difference = []
        
        assert len(signal) == 1
        
        for i in range(len(macd)):
            for j in range(len(signal)):
                if macd[i][0] == signal[j][0]:
                    macd_signal_difference.append([signal[j][0], macd[i][1] - signal[j][1]])
        
        if macd_signal_difference[-1][1] > 0:
            macd_signal_indicator = "SELL"
        elif macd_signal_difference[-1][1] < 0:
            macd_signal_indicator = "BUY"
        else:
            macd_signal_indicator = "HOLD"
        
        if rsi_indicator == "BUY" and macd_signal_indicator == "BUY":

            self.trade = "BUY"
        elif rsi_indicator == "SELL" and macd_signal_indicator == "SELL":

            self.trade = "SELL"
        else:

            self.trade = "HOLD"

        return self.trade
    
    def boll(self, crypto_name, times, prices):
        """
        Determines whether the trade is a 'BUY', 'SELL', or 'HOLD'
        
        Algorithm uses bollinger bands
        """
        if self.builtin_trade_function_arguments == []:
            period = 20
            std_width = 2
        else:
            period = self.builtin_trade_function_arguments[0]
            std_width = self.builtin_trade_function_arguments[1]

        # Helper function
        def BOLL(times, prices, period, std_width):
            """
            Bollinger bands (BOLL)
            
            Returns:
                [{'time': 'time1',
                'moving_average': 0.397,
                'upper_band': 0.348,
                'lower_band': 0.299},
                {'time': 'time2',
                'moving_average': 0.972,
                'upper_band': 1.000
                'lower_band': 0.944}
                ]
            """

            # Helper function
            def MA(times, prices, period):
                """
                Moving Average (MA)
                """
                
                assert len(times) == len(prices)
                
                ma = []
                
                for i in range(len(prices) - period + 1):
                    total = 0
                    
                    for j in range(i, i+period):
                        
                        total += prices[j]
                    
                    total /= period
                    
                    ma.append([times[i + period - 1], total])
                
                return ma
            
            assert len(times) == len(prices)
            assert len(times) >= period
            assert len(prices) >= period
            
            moving_average = MA(times, prices, period)
            
            boll = []
            
            for i in range(len(moving_average)):
                std = np.std(prices[i:i+period])
                
                boll += [{'time': moving_average[i][0], 'moving_average': moving_average[i][1], 'upper_band': moving_average[i][1] + (std * std_width), 'lower_band': moving_average[i][1] - (std * std_width)}]
            
            return boll

        boll_data = BOLL(times[-1 * period:], prices[-1 * period:], period, std_width)
        
        assert len(boll_data) == 1
        
        if boll_data[-1]['upper_band'] < prices[-1]:

            self.trade = "SELL"
        elif boll_data[-1]['lower_band'] > prices[-1]:

            self.trade = "BUY"
        else:

            self.trade = "HOLD"

        return self.trade
    
    def plot_crypto(self, stock, prices, price_times):
        # RGBA: [red, green, blue, alpha]
        """
        status_to_color = {
            'live_buy': dark_red,
            'simulated_buy': light_red,
            'unable_to_buy': yellow,
            'live_sell': dark_green,
            'simulated_sell': light_green,
            'unable_to_sell': blue
        }
        """
        status_to_color = {'live_buy': [1, 0, 0, 1], 'simulated_buy': [1, 0, 0, 0.5], 'unable_to_buy': [1, 1, 0, 1], 'live_sell': [0, 1, 0, 1], 'simulated_sell': [0, 1, 0, 0.5], 'unable_to_sell': [0, 0, 1, 1]}
        
        buy_x, buy_y, buy_color = [], [], []
        sell_x, sell_y, sell_color = [], [], []
        
        for i in range(len(price_times)):
            price_times[i] = self.convert_timestamp_to_datetime(price_times[i])
        
        for time, status in self.buy_times[stock].items():
            
            min_abs_distance, min_index = dt.timedelta(days=9999), 0
            
            for i in range(len(price_times)):
                if abs(price_times[i] - time) < min_abs_distance:
                    min_abs_distance = abs(price_times[i] - time)
                    min_index = i
            
            buy_x += [price_times[min_index]]
            buy_y += [prices[min_index]]
            buy_color += [status_to_color[status]]
        
        for time, status in self.sell_times[stock].items():
            min_abs_distance, min_index = dt.timedelta(days=9999), 0
            
            for i in range(len(price_times)):
                if abs(price_times[i] - time) < min_abs_distance:
                    min_abs_distance = abs(price_times[i] - time)
                    min_index = i
            
            sell_x += [price_times[min_index]]
            sell_y += [prices[min_index]]
            sell_color += [status_to_color[status]]
        
        plt.figure(clear=True)
        plt.plot_date(price_times, prices, 'g-')
        
        # https://matplotlib.org/stable/api/markers_api.html#module-matplotlib.markers
        plt.scatter(x=buy_x, y=buy_y, c=buy_color)
        plt.scatter(x=sell_x, y=sell_y, c=sell_color)
        
        plt.title(stock)
        plt.ylabel("Price ($)")
        plt.xlabel("Time")
        plt.show()
    
    def plot_portfolio(self):
        plt.plot(self.time_data, self.portfolio_data, 'g-')
        plt.title("Portfolio (cash + crypto equity)")
        plt.xlabel("Runtime (in seconds)")
        plt.ylabel("Price ($)")
        plt.show()
    
    def convert_timestamp_to_datetime(self, timestamp):
        if type(timestamp) != str:
            timestamp = str(timestamp)[:-6]
        
        year = int(timestamp[:4])
        month = int(timestamp[5:7])
        day = int(timestamp[8:10])
        
        hour = int(timestamp[11:13])
        minute = int(timestamp[14:16])
        second = int(timestamp[17:19])
        
        return dt.datetime(year, month, day, hour, minute, second)
