import pandas as pd


def profit_extractor(csv_val,  filename):
    # choose a filename to save to
    print("What is your tax multiplier -default 0.25 (25%) ?")
    tax_multiplier = ""
    try:
        input = raw_input
        tax_multiplier = float(input().strip())
    except:
        pass
    if not tax_multiplier:
        tax_multiplier = 0.25

    profit_filename = filename.split('.')[0] + "_profit.csv"

    handle_raw = pd.read_csv(filename)
    handle = handle_raw.copy()
    # convert date to date item and sort from oldest to newest
    handle['timestamp'] = pd.to_datetime(handle.timestamp)
    handle = handle.sort_values('timestamp')
    handle['processed'] = 0
    handle['used'] = False
    handle['Profit'] = 0
    handle['Tax'] = 0

    # iterate over the rows, find a sale, find previous buys of same stock
    # for each sale, consider the oldest available buy first
    # mark used buys so they are not counted twice
    for index, row in handle.iterrows():
        if row.state == 'filled' and row.side == 'sell':
            previous_buys = handle.loc[(handle['symbol'] == row.symbol) &
                                       (handle['timestamp'] <= row['timestamp']) &
                                       (handle['state'] == 'filled') &
                                       (handle['side'] == 'buy') &
                                       (handle['used'] == False)
                                       ]
            # if no previous for a given sell, missing transaction(s)
            if previous_buys.empty:
                print(index, "missing previous transaction, skipped")
                handle.loc[index, 'Profit'] = 'missing transaction'
                continue

            # for each buy, compare the share number to the sold, and loop until oll sold
            # shares have a corresponding buy, and store the number of processed stocks in buys
            # so they are not counted twice
            # I saw some difference between cumulative_quantity and quantity columns, used cumulative_quantity
            number = row.cumulative_quantity
            buy_list = []

            for buy_index, buy in previous_buys.iterrows():
                available = buy.cumulative_quantity - buy.processed
                if available > number:
                    handle.loc[buy_index, 'processed'] = number
                    buy_list.append((number, buy.average_price))
                    break
                elif available == number:
                    handle.loc[buy_index, 'processed'] = number
                    handle.loc[buy_index, 'used'] = True
                    buy_list.append((number, buy.average_price))
                    break
                elif available < number:
                    total_used = buy.processed + available
                    # if available sell is less then total number sold, use all the bought share from this transaction
                    assert total_used == buy.cumulative_quantity
                    handle.loc[buy_index, 'processed'] = total_used
                    handle.loc[buy_index, 'used'] = True
                    buy_list.append((available, buy.average_price))
                    number = number - available
            total_sell = float(row.cumulative_quantity) * float(row.average_price)
            total_buy = 0
            for q, p in buy_list:
                total_buy += float(q)*float(p)

            profit = total_sell - total_buy
            handle.loc[index, 'Profit'] = profit
            if profit > 0:
                handle.loc[index, 'Tax'] = profit * tax_multiplier
    handle_raw['profit'] = handle['Profit']
    tax_row = "Tax("+str(tax_multiplier)+")"
    handle_raw[tax_row] = handle['Tax']
    # save the profit CSV
    handle_raw.to_csv(profit_filename)