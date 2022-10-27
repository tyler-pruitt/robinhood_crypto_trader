import numpy as np
import pandas as pd
import datetime as dt
import time as t
import matplotlib.pyplot as plt
import matplotlib.dates as dates
import pandas_ta as ta
import random as r

from indicators import MA, EMA, RSI, MACD, BOLL
import order

import robin_stocks.robinhood as rh

class Trader():
    def __init__(self, config):
        """
        config = {
            crypto: [],
            username: '',
            password: '',
            days_to_run: 1,
            export_csv: False,
            plot_analytics: False,
            plot_crypto: False,
            mode: '',
            backtest: {
                interval: '',
                span: '',
                bounds: ''
            },
            trader: {
                interval: '',
                span: '',
                bounds: ''
            },
            determine_trade_function: 'function_name',
            cash: 2000,
            use_cash: False,
            loss_threshold: 50.00
        }
        """
        self.check_config(config)

        self.id = self.generate_id()
        self.crypto = config['crypto']
        self.username = config['username']
        self.password = config['password']
        self.days_to_run = config['days_to_run']
        self.export_csv = config['export_csv']
        self.plot_analytics_config = config['plot_analytics']
        self.plot_crypto_config = config['plot_crypto']
        self.mode = config['mode']

        if self.mode == 'backtest':
            self.backtest_interval = config['backtest']['interval']
            self.backtest_span = config['backtest']['span']
            self.backtest_bounds = config['backtest']['bounds']

            self.is_live = False
        else:
            self.interval = config['trader']['interval']
            self.span = config['trader']['span']
            self.bounds = config['trader']['bounds']

            if self.mode == 'live':
                self.is_live = True
            else:
                self.is_live = False
        
        if self.is_live:
            self.orders = []
        
        self.cash = config['cash']
        self.use_cash = config['use_cash']

        self.holdings, self.bought_price = self.get_holdings_and_bought_price()

        # Loss threshold (in dollars) taken to be a positive value
        self.loss_threshold = config['loss_threshold']
        
        # Need to set initial capital
        self.initial_capital = 5
        
        self.start_time = t.time()
        
        self.profit = 0.0
        self.percent_change = 0.0
        
        self.trade = ''
        
        # self.buy_times = [{datetime: 'status'}]
        # status possibilities are ['live_buy', 'simulated_buy', 'unable_to_buy', 'live_sell', 'simulated_sell', unable_to_sell']
        self.buy_times = [dict()] * len(self.crypto)
        self.sell_times = [dict()] * len(self.crypto)
        
        self.login()
    
    def __repr__(self):
        return "Trader(profit: " + self.display_profit() + " (" + self.display_percent_change() + "), runtime: " + self.display_time(self.get_runtime()) + ")"
    
    def generate_id(self):
        letters_and_numbers = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        id = ''
        
        # id = '####-####-####'
        for i in range(3):
            for j in range(4):
                id += letters_and_numbers[r.randint(0, len(letters_and_numbers)-1)]
            
            if i != 2:
                id += '-'
        
        return id
    
    def login(self):
        time_logged_in = 60 * 60 * 24 * self.days_to_run
        
        rh.authentication.login(username=self.username,
                                password=self.password,
                                expiresIn=time_logged_in,
                                scope='internal',
                                by_sms=True,
                                store_session=False)
        
        print("login successful")
    
    def logout(self):
        rh.authentication.logout()
        
        print("logout successful")
    
    def get_cash(self):
        rh_cash = rh.account.build_user_profile()

        cash = float(rh_cash['cash'])
        equity = float(rh_cash['equity'])
        
        
        return cash, equity
    
    def get_latest_price(self, crypto_symbol):
        
        return rh.crypto.get_crypto_quote(crypto_symbol)['mark_price']
    
    def get_crypto_holdings_capital(self):
        capital = 0
            
        for crypto_name, crypto_amount in self.holdings.items():
            capital += crypto_amount * float(get_latest_price(crypto_name))
            
        return capital
    
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
            
            nested_data['price'] = self.get_latest_price(holdings_data[i]["currency"]["code"])
            nested_data['quantity'] = holdings_data[i]["quantity"]
            
            try:
                nested_data['average_buy_price'] = str(float(holdings_data[i]["cost_bases"][0]["direct_cost_basis"]) / float(nested_data["quantity"]))
            except ZeroDivisionError:
                nested_data['average_buy_price'] = '-'
            
            build_holdings_data[holdings_data[i]["currency"]["code"]] = nested_data
        
        return build_holdings_data
    
    def get_holdings_and_bought_price(self):
        holdings = {self.crypto[i]: 0 for i in range(0, len(self.crypto))}
        bought_price = {self.crypto[i]: 0 for i in range(0, len(self.crypto))}
        
        rh_holdings = self.build_holdings()

        for crypto_symbol in self.crypto:
            try:
                holdings[crypto_symbol] = float(rh_holdings[crypto_symbol]['quantity'])
                bought_price[crypto_symbol] = float(rh_holdings[crypto_symbol]['average_buy_price'])
            except:
                holdings[crypto_symbol] = 0
                bought_price[crypto_symbol] = 0

        return holdings, bought_price
    
    def display_holdings(self):
        for crypto, amount in self.holdings.items():
            
            print('\t' + str(amount) + ' ' + crypto + " at $" + str(self.get_latest_price(crypto)))
    
    def download_backtest_data(self):
        """
        Assumes that self.mode is 'backtest'
        """
        crypto_historical_data = []
        
        for i in range(len(self.crypto)):
            
            crypto_historical_data += [rh.crypto.get_crypto_historicals(symbol=self.crypto[i], interval=self.backtest_interval, span=self.backtest_span, bounds=self.backtest_bounds)]
        
        print("downloading backtesting data finished")
        
        return crypto_historical_data
    
    def check_config(self, config):
        assert type(config['days_to_run']) == int and config['days_to_run'] >= 1

        assert type(config['username']) == str and type(config['password']) == str
        
        assert len(config['username']) > 0 and len(config['password']) > 0
        
        assert config['mode'] in ['live', 'backtest', 'safelive']
        
        assert type(config['export_csv']) == bool

        assert type(config['plot_analytics']) == bool
        
        assert type(config['plot_crypto']) == bool
        
        assert type(config['plot_portfolio']) == bool

        assert type(config['crypto']) == list and len(config['crypto']) > 0

        assert type(config['loss_threshold']) == float or type(config['loss_threshold']) == int
        
        assert config['loss_threshold'] >= 0

        assert type(config['determine_trade_function']) == str
        
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
    
    def get_percent_change(self):
        return self.percent_change
    
    def get_overbought_threshold(self):
        return self.overbought
    
    def get_oversold_threshold(self):
        return self.oversold
    
    def set_overbought_threshold(self, threshold):
        self.overbought = threshold
    
    def set_oversold_threshold(self, threshold):
        self.oversold = threshold
    
    def continue_trading(self, override=None):
        if override != None:
            assert type(override) == bool
            
            return override
        else:
            if self.get_profit() >= -1 * self.get_loss_threshold():
                return True
            else:
                print("Loss exceeded $" + str(self.get_loss_threshold()) + ": terminating automated trading")
    
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
    
    def set_trade(self, trade):
        self.trade = trade
    
    def get_trade(self):
        return self.trade
    
    def get_loss_threshold(self):
        return self.loss_threshold
    
    def set_loss_threshold(self, loss):
        if loss >= 0:
            self.loss_threshold = loss
        else:
            print("Loss must be set to a POSITIVE value: loss threshold not reset")
    
    def get_runtime(self):
        return t.time() - self.start_time

    def set_profit(self, profit):
        """
        Sets Trader.profit and Trader.percent_change accordingly
        """
        self.profit = profit
        
        self.percent_change = (profit * 100) / self.initial_capital
    
    def get_profit(self):
        return self.profit
    
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
    
    def set_interval(self, interval):
        self.interval = interval
    
    def set_span(self, span):
        self.span = span
    
    def get_interval(self):
        return self.interval
    
    def get_span(self):
        return self.span
    
    def get_crypto(self):
        return self.crypto
    
    def set_crypto(self, crypto):
        self.stocks = crypto
    
    def get_start_time(self):
        return self.start_time
    
    def set_start_time(self, time):
        self.start_time = time
    
    def get_historical_data(self, crypto_symbol, interval=self.interval, span=self.span, bounds=self.bounds):
        historical_data = rh.crypto.get_crypto_historicals(crypto_symbol, interval=interval, span=span, bounds=bounds)
        
        # df contains all the data (eg. time, open, close, high, low, volume, session, interpolated, symbol)
        df = pd.DataFrame(historical_data)
        
        return df
    
    def get_historical_times(self, crypto_symbol, interval=self.interval, span=self.span, bounds=self.bounds):
        # df contains all the data (eg. time, open, close, high, low)
        df = self.get_historical_data(crypto_symbol, interval, span, bounds)
        
        dates_times = pd.to_datetime(df.loc[:, 'begins_at'])
        
        return dates_times

    def get_historical_prices(self, crypto_symbol, interval=self.interval, span=self.span, bounds=self.bounds):
        # df contains all the data (eg. time, open, close, high, low)
        df = self.get_historical_data(crypto_symbol, interval, span, bounds)

        dates_times = pd.to_datetime(df.loc[:, 'begins_at'])
        close_prices = df.loc[:, 'close_price'].astype('float')

        df_price = pd.concat([close_prices, dates_times], axis=1)
        df_price = df_price.rename(columns={'close_price': stock})
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

    def determine_trade_macd_rsi(self, stock, stock_historicals=None):
        """
        Determines whether the trade is a 'BUY', 'SELL', or 'HOLD'
        
        If both RSI and MACD are cross their respective thresholds, then either buy or sell
        Else hold
        
        Runtime is much faster when config.PLOTANALYTICS = False
        """
        
        if self.mode == 'backtest':
            assert stock_historicals != None
            
            # Set times and prices given stock_historicals
            # For this algorithm, need times and prices to be of length >= (macd_slow_period + macd_signal_period - 1) = 34
            times, prices = [], []
            
            for k in range(len(stock_historicals)):
                times += [stock_historicals[k]['begins_at']]
                
                prices += [float(stock_historicals[k]['close_price'])]
        else:
            df_historical_prices = self.get_historical_prices(stock)
            
            # For this algorithm, need times and prices to be of length >= (macd_slow_period + macd_signal_period - 1) = 34
            
            # https://pandas.pydata.org/docs/reference/api/pandas.Timestamp.html#pandas.Timestamp
            times = self.convert_dataframe_to_list(self.get_historical_times(stock))
            prices = self.convert_dataframe_to_list(df_historical_prices, True)
        
        if self.plot_analytics_config:
            rsi_data = RSI(times, prices, 14)
        else:
            rsi_data = RSI(times[-16:], prices[-16:], 14)
            
            assert len(rsi_data) == 1
        
        if rsi_data[-1][1] > 70:
            rsi_indicator = "SELL"
        elif rsi_data[-1][1] < 30:
            rsi_indicator = "BUY"
        else:
            rsi_indicator = "HOLD"
        
        if self.plot_analytics_config:
            macd, signal = MACD(times, prices, 12, 26, 9)
            macd_signal_difference = []
        else:
            macd, signal = MACD(times[-34:], prices[-34:], 12, 26, 9)
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
        
        if self.plot_analytics_config:
            self.plot_macd_rsi_analytics(stock, macd, signal, macd_signal_difference, rsi_data)
        
        if self.plot_crypto_config:
            self.plot_crypto(stock, prices, times)
        
        if rsi_indicator == "BUY" and macd_signal_indicator == "BUY":
            
            self.set_trade("BUY")
        elif rsi_indicator == "SELL" and macd_signal_indicator == "SELL":
            
            self.set_trade("SELL")
        else:
            
            self.set_trade("HOLD")

        return self.get_trade()
    
    def determine_trade_boll(self, stock, stock_historicals=None):
        """
        Determines whether the trade is a 'BUY', 'SELL', or 'HOLD'
        
        Algorithm uses bollinger bands
        
        Runtime is much faster when config.PLOTANALYTICS = False
        """
        
        if self.mode == 'backtest':
            assert stock_historicals != None
            
            # Set times and prices given stock_historicals
            # For this algorithm, need times and prices to be of length >= period = 20
            times, prices = [], []
            
            for k in range(len(stock_historicals)):
                times += [stock_historicals[k]['begins_at']]
                
                prices += [float(stock_historicals[k]['close_price'])]
        else:
            df_historical_prices = self.get_historical_prices(stock)
            
            # For this algorithm, need times and prices to be of length >= period = 20
            
            # https://pandas.pydata.org/docs/reference/api/pandas.Timestamp.html#pandas.Timestamp
            times = self.convert_dataframe_to_list(self.get_historical_times(stock))
            prices = self.convert_dataframe_to_list(df_historical_prices, True)
        
        if self.plot_analytics_config:
            boll_data = BOLL(times, prices)
        else:
            boll_data = BOLL(times[-20:], prices[-20:])
            
            assert len(boll_data) == 1
        
        if boll_data[-1]['upper_band'] < prices[-1]:
            
            self.set_trade("SELL")
        elif boll_data[-1]['lower_band'] > prices[-1]:
            
            self.set_trade("BUY")
        else:
            
            self.set_trade("HOLD")
        
        if self.plot_analytics_config:
            self.plot_boll_analytics(stock, prices, times, boll_data)
        
        if self.plot_crypto_config:
            self.plot_crypto(stock, prices, times)

        return self.get_trade()
    
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
        
        for time, status in self.buy_times[self.crypto.index(stock)].items():
            
            min_abs_distance, min_index = dt.timedelta(days=9999), 0
            
            for i in range(len(price_times)):
                if abs(price_times[i] - time) < min_abs_distance:
                    min_abs_distance = abs(price_times[i] - time)
                    min_index = i
            
            buy_x += [price_times[min_index]]
            buy_y += [prices[min_index]]
            buy_color += [status_to_color[status]]
        
        for time, status in self.sell_times[self.crypto.index(stock)].items():
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
    
    def plot_macd_signal(self, stock, macd, signal):
        
        macd_data, macd_times = [], []
    
        for i in range(len(macd)):
            macd_data.append(macd[i][1])
            macd_times.append(self.convert_timestamp_to_datetime(macd[i][0]))
        
        signal_data, signal_times = [], []
        
        for i in range(len(signal)):
            signal_data.append(signal[i][1])
            signal_times.append(self.convert_timestamp_to_datetime(signal[i][0]))
        
        plt.figure(clear=True)
        plt.plot_date(macd_times, macd_data, 'b-')
        plt.plot_date(signal_times, signal_data, 'r-')
        plt.title(stock)
        plt.ylabel("MACD vs. Signal")
        plt.legend(["MACD", "Signal"], loc='lower left')
        plt.xlabel("Time")
        plt.show()
    
    def plot_macd_signal_difference(self, stock, macd_signal_difference):
        
        macd_signal_data, macd_signal_times = [], []
        
        for i in range(len(macd_signal_difference)):
            macd_signal_times.append(self.convert_timestamp_to_datetime(macd_signal_difference[i][0]))
            macd_signal_data.append(macd_signal_difference[i][1])
        
        zeroLine = []
        for i in range(len(macd_signal_times)):
            zeroLine.append(0)
        
        plt.figure(clear=True)
        plt.plot_date(macd_signal_times, macd_signal_data, 'r-')
        plt.plot_date(macd_signal_times, zeroLine, 'k--')
        plt.title(stock)
        plt.ylabel("MACD - Signal")
        plt.xlabel("Time")
        plt.show()
    
    def plot_rsi(self, stock, rsi):
        rsi_data, rsi_times = [], []
        
        for i in range(len(rsi)):
            rsi_times.append(self.convert_timestamp_to_datetime(rsi[i][0]))
            rsi_data.append(rsi[i][1])
        
        overbought_line, oversold_line = [], []
        
        for i in range(len(rsi_times)):
            overbought_line.append(self.get_overbought_threshold())
            oversold_line.append(self.get_oversold_threshold())
        
        plt.figure(clear=True)
        plt.plot_date(rsi_times, rsi_data, 'r-')
        plt.plot_date(rsi_times, overbought_line, 'k--')
        plt.plot_date(rsi_times, oversold_line, 'k--')
        plt.title(stock)
        plt.ylabel("RSI")
        plt.xlabel("Time")
        plt.show()
    
    def plot_macd_rsi_analytics(self, stock, macd, signal, macd_signal_difference, rsi):
        self.plot_macd_signal(stock, macd, signal)
        self.plot_macd_signal_difference(stock, macd_signal_difference)
        self.plot_rsi(stock, rsi)
    
    def plot_boll_analytics(self, stock, prices, times, boll_data):
        upper_band, moving_average, lower_band, boll_times = [], [], [], []
        
        for i in range(len(boll_data)):
            upper_band += [boll_data[i]['upper_band']]
            moving_average += [boll_data[i]['moving_average']]
            lower_band += [boll_data[i]['lower_band']]
            boll_times += [boll_data[i]['time']]
        
        plt.figure(clear=True)
        plt.plot_date(times, prices, 'g-')
        plt.plot_date(boll_times, upper_band, 'b-')
        plt.plot_date(boll_times, moving_average, 'r-')
        plt.plot_date(boll_times, lower_band, 'b-')
        plt.title(stock)
        plt.xlabel('Time')
        plt.ylabel('Price ($)')
        plt.legend(('stock', 'upper_band', 'moving_average', 'lower_band'), loc='lower left')
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
