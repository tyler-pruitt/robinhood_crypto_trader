import robinhood_crypto_trader.crypto_trader as rct

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
        'determine_trade_function': 'personal_strategy',
        'cash': 2000,
        'use_cash': True,
        'loss_threshold': 50.00,
        'loss_percentage': 5,
        'holdings_factor': 0.20,
        'cash_factor': 0.20,
        'buy_order_type': 'market',
        'sell_order_type': 'market'
    }

    tr = rct.Trader(config)

    tr.run()

    tr.logout()

if __name__ == '__main__':
    test_trader()
