from datetime import timedelta

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
    handle['last_transaction_at'] = pd.to_datetime(handle.last_transaction_at)
    handle = handle.sort_values('last_transaction_at')
    handle['processed'] = 0
    handle['used'] = False
    handle['Profit'] = 0
    handle['Wash Sale'] = 0
    handle['Tax'] = 0

    # iterate over the rows, find a sale, find previous buys of same stock
    # for each sale, consider the oldest available buy first
    # mark used buys so they are not counted twice
    for index, row in handle.iterrows():
        if row.state == 'filled' and row.side == 'sell':
            previous_buys = handle.loc[(handle['symbol'] == row.symbol) &
                                       (handle['last_transaction_at'] <= row['last_transaction_at']) &
                                       (handle['state'] == 'filled') &
                                       (handle['side'] == 'buy') &
                                       (handle['used'] == False)
                                       ]
            # if no previous for a given sell, missing transaction(s)
            if previous_buys.empty:
                print(index, "missing previous transaction, skipped")
                handle.loc[index, 'Profit'] = 'missing transaction'
                continue

            # check for wash sales
            # TODO to properly track wash sales, the entire script has to be rewritten
            # If shares are sold in a wash sale and repurchased, the previous loss is not deductible and has to be added to the new purchase price
            # This can get quite complex if share from different previous trades were sold and repurchased
            # Additionally, the timing for long-term keeps on counting on those shares
            # this implementation only covers single wash sales and adds the disallowed loss in a new column 'Wash Sale'
            ws_buys = handle.loc[(handle['symbol'] == row.symbol) &
                                 (handle['last_transaction_at'] >= row['last_transaction_at']) &
                                 (handle['last_transaction_at'] <= row['last_transaction_at'] + timedelta(days=30)) &
                                 (handle['state'] == 'filled') &
                                 (handle['side'] == 'buy') &
                                 (handle['used'] == False)
                                 ]

            ws_count = 0
            if not ws_buys.empty:
                # calculate
                # find previous buys to calculate loss
                print('found')
                for buy_index, buy in ws_buys.iterrows():
                    ws_count += buy.cumulative_quantity

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
                    buy_list.append((number, float(buy.average_price)))
                    break
                elif available == number:
                    handle.loc[buy_index, 'processed'] = number
                    handle.loc[buy_index, 'used'] = True
                    buy_list.append((number, float(buy.average_price)))
                    break
                elif available < number:
                    total_used = buy.processed + available
                    # if available sell is less then total number sold, use all the bought share from this transaction
                    assert total_used == buy.cumulative_quantity
                    handle.loc[buy_index, 'processed'] = total_used
                    handle.loc[buy_index, 'used'] = True
                    buy_list.append((available, float(buy.average_price)))
                    number = number - available
            total_sell = float(row.cumulative_quantity) * float(row.average_price)
            total_buy = 0
            total_ws = 0
            ws_count_temp = ws_count
            for q, p in buy_list:
                total_buy += float(q)*float(p)
                for i in range(0, q):
                    if ws_count_temp > 0:
                        amount = p-float(row.average_price)
                        if amount > 0:
                            total_ws += amount
                            ws_count_temp -= 1

            if total_ws > 0:  # add fees
                total_ws += float(row.fees) / float(row.cumulative_quantity) * (ws_count - ws_count_temp)

            profit = total_sell - total_buy - float(row.fees)
            handle.loc[index, 'Profit'] = profit
            handle.loc[index, 'Wash Sale'] = total_ws
            if profit > 0:
                handle.loc[index, 'Tax'] = profit * tax_multiplier

    handle_raw['profit'] = handle['Profit']
    handle_raw['Wash Sale'] = handle['Wash Sale']
    tax_row = "Tax("+str(tax_multiplier)+")"
    handle_raw[tax_row] = handle['Tax']
    # save the profit CSV
    handle_raw.to_csv(profit_filename)
