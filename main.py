from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.trading.client import TradingClient
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.trading.requests import OrderRequest
from datetime import datetime, timedelta
from time import sleep


API_KEY = 'PKSOVG2YEBLVPKNA8K5U'
API_SECRET = '09rRznBcGib14PmuAet5ctzhjA6F9vZzCjqEQC71'
BASE_URL = 'https://paper-api.alpaca.markets'  # use this for paper trading

client = StockHistoricalDataClient(API_KEY,API_SECRET)
trading_client = TradingClient(API_KEY, API_SECRET, paper=True)
account = trading_client.get_account()

#for property_name, value in account.__dict__.items():
#    print(f"\"{property_name}\": {value}")
#sleep(300)


symbols = ["F", "GE", "NOK", "MRO", "INST", "IVR", "PLTR", "KEY", "SPOT", "GPRO", "SBUX", "AAPL",
           "KR", "BAC","SIFY", "FPAY", "CAN", "GSAT", "LUMN", "API", "IHRT", "MVIS", "VMEO", "KODK",
           "UIS", "YEXT", "PTON", "T", "NIO", "TSLA", "AMZN", "MSFT", "META", "GOOG", "GOOGL", "CLNN",
           "OMQS", "SDPI", "CLRO", "PRPL", "CODX", "PFIE", "COOK", "SPWH", "SERA", "CLAR", "LFVN", "CRCT",
           "BRDG", "HCAT", "SNFCA", "RXRX", "DOMO", "CLSK", "TRAK", "NATR", "NUS", "MYGN", "VREX", "BYON",
           "PRG", "FC", "ZION", "SKYW", "USNA", "HQY", "MMSI", "UTMD", "IIPR", "EXR"]

def moving_average(lst, window_size):
    moving_averages = []
    window_sum = sum(lst[:window_size])
    moving_averages.append(window_sum / window_size)

    for i in range(window_size, len(lst)):
        window_sum = window_sum - lst[i - window_size] + lst[i]
        moving_averages.append(window_sum / window_size)

    return moving_averages

def calculate_quantity(current_buying_power, open_price):
    quantity = int(current_buying_power / open_price)
    if quantity > 5:
        print(f'Quantiy is {quantity}, reducing to 5 shares.')
        quantity = 5
    return quantity

def create_buy_order(symbol, quantity):
    return OrderRequest(
        symbol=symbol,
        qty=quantity,
        side='buy',
        type='market',
        time_in_force='gtc'
    )

for symbol in symbols:

    # Update account information
    account = trading_client.get_account()
    print(f"Current Buying Power: ${account.__dict__['buying_power']}")

    end_date = datetime.today()
    start_date = end_date - timedelta(days=365)    

    bar_request = StockBarsRequest(
        symbol_or_symbols=symbol, 
        timeframe=TimeFrame(1, TimeFrameUnit('Day')), 
        start=start_date, 
        end=end_date, 
        limit=365)
    
    bars = client.get_stock_bars(bar_request)
    """
    print(f"\n\n")
    print(bars[symbol][0])
    print(f"\n\n\n")
    """

    short_window = 50
    long_window = 200
    #print(f'Confirming data point length({len(bars[symbol])}) vs long window({long_window})')
    if len(bars[symbol]) >= long_window:  # Check to ensure we have enough data points
        #print('Data points confirmed...')
        short_moving_average = moving_average([bar.open for bar in bars[symbol]], short_window)[-1]
        long_moving_average = moving_average([bar.open for bar in bars[symbol]], long_window)[-1]
        print('Moving averages calculated...')

        # Display the signal generated by the moving averages
        print('Stock is currently trading at: $' + str(bars[symbol][-1].open))
        # Display the resulting deatch cross or golden cross signal
        if short_moving_average > long_moving_average:
            print('Golden Cross')
        elif short_moving_average < long_moving_average:
            print('Death Cross')
        else:
            print('No Signal')
        

        try:
            print(f'Getting {symbol} position...')
            position = trading_client.get_open_position(symbol)
            print(f'Position {symbol} available.')
            # Display current position return percentage
            percent_return = round(float(position.unrealized_plpc), 2)
            print(f'Current Position Return: {percent_return}%')
        except:
            print(f'No position for {symbol}.')
            percent_return = 0
            position = None

        print(f'Short Average: {short_moving_average}\nLong Average: {long_moving_average}')
        
        if percent_return < -.05 and position:
            # Stop Loss - Sell Signal
            print('Stop Loss...')

            # Generate order request object
            order = OrderRequest(
                symbol=symbol,
                qty=position.qty,
                side='sell',
                type='market',
                time_in_force='gtc'
            )
            
            trading_client.submit_order(order)
            print(f"Stop Loss detected for {symbol}. Selling {position.qty} shares.")
        
        elif percent_return > .05 and position:
            # Take Profit - Sell Signal
            print('Take Profit...')

            # Generate order request object
            order = OrderRequest(
                symbol=symbol,
                qty=position.qty,
                side='sell',
                type='market',
                time_in_force='gtc'
            )
            
            trading_client.submit_order(order)
            print(f"Take Profit detected for {symbol}. Selling {position.qty} shares.")

        elif short_moving_average > long_moving_average and not position:
            # Golden Cross - Buy Signal
            print('Buy Signal...')

            # Get current buying power
            current_buying_power = float(account.__dict__['buying_power'])
            print(f'Current Buying Power: {current_buying_power}')


            # Check symbol price
            open_price = bars[symbol][-1].open
            
            # Check if we have enough buying power, and buy up to 5 shares
            if open_price < current_buying_power:
                # Generate order request object
                # Taking current buying power and dividing by open price to get number of shares
                quantity = calculate_quantity(current_buying_power, open_price)
                print(f'Buying {quantity} shares of {symbol} at {open_price}')
                order = create_buy_order(symbol, quantity)

                # Submit order
                trading_client.submit_order(order)
                print(f"Golden Cross detected for {symbol}. Buying 1 share.")
            
            # If we don't have enough buying power, print a message
            else:
                print(f'Insufficient buying power, we have {current_buying_power} trying to buy {symbol} at {open_price}')


        elif short_moving_average < long_moving_average and position:
            # Death Cross - Sell Signal
            print('Sell Signal...')

            # Generate order request object
            order = OrderRequest(
                symbol=symbol,
                qty=position.qty,
                side='sell',
                type='market',
                time_in_force='gtc'
            )
            
            trading_client.submit_order(order)
            print(f"Death Cross detected for {symbol}. Selling {position.qty} shares.")
        
        else:
            print('No Action...')
        print('**************************************\n')
        sleep(1)

with open('log.txt', 'a') as f:
    f.write(f'Paper Trader ran at {datetime.now()}.\n')
