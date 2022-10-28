import trader

def test_trader():
    config = {
                'crypto': ['BTC', 'ETH'],
                'username': 'your_robinhood_username',
                'password': 'your_robinhood_password',
                'days_to_run': 1,
                'export_csv': False,
                'plot_analytics': False,
                'plot_crypto': False,
                'plot_portfolio': False,
                'mode': 'safelive',
                'backtest': {
                    'interval': '15second',
                    'span': 'hour',
                    'bounds': '24_7',
                    'index': 10
                },
                'trader': {
                    'interval': '15second',
                    'span': 'hour',
                    'bounds': '24_7'
                },
                'determine_trade_function': 'function_name',
                'cash': 2000,
                'use_cash': True,
                'loss_threshold': 50.00,
                'holdings_divisor': 5,
                'cash_divisor': 5
            }

    tr = trader.Trader(config)

    tr.run()

if __name__ == '__main__':
    test_trader()