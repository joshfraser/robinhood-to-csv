from Robinhood import Robinhood
from profit_extractor import profit_extractor
import getpass
import collections
import argparse
import ast
from dotenv import load_dotenv, find_dotenv
import os

logged_in = False

parser = argparse.ArgumentParser(
    description='Export Robinhood trades to a CSV file')
parser.add_argument(
    '--debug', action='store_true', help='store raw JSON output to debug.json')
parser.add_argument(
    '--username', default='', help='your Robinhood username')
parser.add_argument(
    '--password', default='', help='your Robinhood password')
parser.add_argument(
    '--mfa_code', help='your Robinhood mfa_code')
parser.add_argument(
    '--profit', action='store_true', help='calculate profit for each sale')
args = parser.parse_args()
username = args.username
password = args.password
mfa_code = args.mfa_code

load_dotenv(find_dotenv())

robinhood = Robinhood()

# login to Robinhood
while logged_in != True:

    if username == "":
        username = os.getenv("RH_USERNAME")
    if username == "":
        print("Robinhood username:", end=' ')
        try:
            input = raw_input
        except NameError:
            pass
        username = input()

    if password == "":
        password = os.getenv("RH_PASSWORD")
    if password == "":
        password = getpass.getpass()

    logged_in = robinhood.login(username=username, password=password)
    if logged_in != True and logged_in.get('non_field_errors') == None and logged_in['mfa_required'] == True:
        mfa_code = os.getenv("RH_MFA")
        if mfa_code == "":
            print("Robinhood MFA:", end=' ')
            try:
                input = raw_input
            except NameError:
                pass
            mfa_code = input()
        logged_in = robinhood.login(username=username, password=password, mfa_code=mfa_code)

    if logged_in != True:
        password = ""
        print("Invalid username or password.  Try again.\n")

print("Pulling trades. Please wait...")

fields = collections.defaultdict(dict)
trade_count = 0
queued_count = 0

# fetch order history and related metadata from the Robinhood API
#orders = robinhood.get_endpoint('orders')
orders = robinhood.get_endpoint('optionsOrders');
# load a debug file
# raw_json = open('debug.txt','rU').read()
# orders = ast.literal_eval(raw_json)

# store debug
if args.debug:
    # save the CSV
    try:
        with open("debug.txt", "w+") as outfile:
            outfile.write(str(orders))
            print("Debug infomation written to debug.txt")
    except IOError:
        print('Oops.  Unable to write file to debug.txt')

# Vignesh save the CSV
try:
    with open("stocks.txt", "w+") as outfile:
        outfile.write(str(orders))
except IOError:
    print("Oops.  Unable to write options file to ", filename)
#Vignesh end

# do/while for pagination
paginated = True
page = 0
row = 0
while paginated:
    for i, order in enumerate(orders['results']):
        for j, leg in enumerate(order['legs']):
            counter = row + (page * 100)
            executions = leg['executions']
            #Fetch meta info such as strike price, expiration, ticker name of this order
            contract = robinhood.get_custom_endpoint(leg['option'])
            fields[counter]['Leg'] = j + 1
            fields[counter]['Ticker'] = contract['chain_symbol']
            fields[counter]['Strike_price'] = contract['strike_price']
            fields[counter]['Expiration_date'] = contract['expiration_date']
            # Read thro all the data under the order and add it to the csv row
            for key, value in enumerate(leg):
                if value != 'executions':
                        fields[counter][value] = leg[value]
            for key, value in enumerate(order):
                if value != "legs":
                    fields[counter][value] = order[value]
            # Update trade count if order was filled to report at the end about how many trades were exported
            if order['state'] == "filled":
                trade_count += 1
                # Since the order is filled, read all the leg and execution information such as date placed, amount paid, drag them over to csv
                for key, value in enumerate(executions[0]):
                    fields[counter][value] = executions[0][value]
            elif order['state'] == "queued":
                queued_count += 1
            #Add a calculation for the amount this trade will have effected on the buying power, this will help calculate total profit.
            if leg['side'] == 'sell':
                fields[counter]['Change_in_Buying_Power'] = order['processed_premium']
            else:
                fields[counter]['Change_in_Buying_Power'] = "-" + (order['processed_premium']);
            row += 1
    # paginate
    if orders['next'] is not None:
        page = page + 1
        orders = robinhood.get_custom_endpoint(str(orders['next']))
    else:
        paginated = False

# for i in fields:
# 	print fields[i]
# 	print "-------"

# check we have trade data to export
if trade_count > 0 or queued_count > 0:
    print("%d queued trade%s and %d executed trade%s found in your account." %
          (queued_count, "s" [queued_count == 1:], trade_count,
           "s" [trade_count == 1:]))
    # print str(queued_count) + " queded trade(s) and " + str(trade_count) + " executed trade(s) found in your account."
else:
    print("No trade history found in your account.")
    quit()

# CSV headers
keys = fields[0].keys()
#keys = sorted(keys)
csv = ','.join(keys) + "\n"

# CSV rows
for row in fields:
    for idx, key in enumerate(keys):
        if (idx > 0):
            csv += ","
        try:
            csv += str(fields[row][key])
        except:
            csv += ""

    csv += "\n"

# choose a filename to save to
print("Choose a filename or press enter to save to `option-trades.csv`:")
try:
    input = raw_input
except NameError:
    pass
filename = input().strip()
if filename == '':
    filename = "option-trades.csv"

# save the CSV
try:
    with open(filename, "w+") as outfile:
        outfile.write(csv)
except IOError:
    print("Oops. Unable to write file to ", filename, ". Close the file if it is open and try again.")

if args.profit:
    profit_csv = profit_extractor(csv, filename)
