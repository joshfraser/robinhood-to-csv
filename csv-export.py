from __future__ import print_function
from Robinhood import Robinhood
from profit_extractor import profit_extractor
import getpass
import collections
import argparse
import ast
from dotenv import load_dotenv, find_dotenv
import os
import datetime

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
parser.add_argument(
    '--dividends', action='store_true', help='export dividend payments')
parser.add_argument(
    '--start_date', default='', help='The start date of transactions logged    Format:  YYYY-MM-DD')
parser.add_argument(
    '--end_date', default='', help='The end date of transactions logged    Format:  YYYY-MM-DD')
args = parser.parse_args()
username = args.username
password = args.password
mfa_code = args.mfa_code
start_date = None
end_date = None
if args.start_date != "":
    try:
        start_date = datetime.datetime.strptime(args.start_date+"00:00:00.000000", "%Y-%m-%d%H:%M:%S.%f")
    except ValueError:
        print("Given start date " + args.start_date + " does not fit format YYYY-MM-DD")
if args.end_date != "":
    try:
        end_date = datetime.datetime.strptime(args.end_date+"23:59:59.999999", "%Y-%m-%d%H:%M:%S.%f")
    except ValueError:
        print("Given end date " + args.end_date + " does not fit format YYYY-MM-DD")

load_dotenv(find_dotenv())

robinhood = Robinhood()

# login to Robinhood
while logged_in != True:

    if username == "":
        username = os.getenv("RH_USERNAME", "")
    if username == "":
        print("Robinhood username:", end=' ')
        try:
            input = raw_input
        except NameError:
            pass
        username = input()

    if password == "":
        password = os.getenv("RH_PASSWORD", "")
    if password == "":
        password = getpass.getpass()

    logged_in = robinhood.login(username=username, password=password)
    if logged_in != True and logged_in.get('non_field_errors') == None and logged_in.get('mfa_required') == True:

        if mfa_code is None:
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

#holds instrument['symbols'] to reduce API ovehead {instrument_url:symbol}
cached_instruments = {}

# fetch order history and related metadata from the Robinhood API
orders = robinhood.get_endpoint('orders')

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

# do/while for pagination
paginated = True
page = 0
while paginated:
    for i, order in enumerate(orders['results']):
        executions = order['executions']

        symbol = cached_instruments.get(order['instrument'], False)
        if not symbol:
            symbol = robinhood.get_custom_endpoint(order['instrument'])['symbol']
            cached_instruments[order['instrument']] = symbol

        fields[i + (page * 100)]['symbol'] = symbol

        for key, value in enumerate(order):
            if value != "executions":
                fields[i + (page * 100)][value] = order[value]

        fields[i + (page * 100)]['num_of_executions'] = len(executions)
        fields[i + (page * 100)]['execution_state'] = order['state']

        if len(executions) > 0:
            fields[i + (page * 100)]['execution_state'] = ("completed", "partially filled")[order['cumulative_quantity'] < order['quantity']]
            fields[i + (page * 100)]['first_execution_at'] = executions[0]['timestamp']
            fields[i + (page * 100)]['settlement_date'] = executions[0]['settlement_date']
    # paginate
    if orders['next'] is not None:
        page = page + 1
        orders = robinhood.get_custom_endpoint(str(orders['next']))
    else:
        paginated = False

# for i in fields:
# 	print fields[i]
# 	print "-------"



# CSV headers
keys = fields[0].keys()
keys = sorted(keys)
csv = ','.join(keys) + "\n"

# CSV rows
for row in fields:
    #Check if date is compliant with filters
    date_object = datetime.datetime.strptime(fields[row]['created_at'], "%Y-%m-%dT%H:%M:%S.%fZ")
    filtered = False
    if start_date != None:
        if start_date > date_object:
            filtered = True
    if end_date != None:
        if end_date < date_object:
            filtered = True
    if not filtered:
        if fields[row]['execution_state'] in ['completed', 'partially filled']:
            trade_count += 1
        elif fields[row]['state'] == "queued":
            queued_count += 1
        for idx, key in enumerate(keys):
            if (idx > 0):
                csv += ","
            try:
                csv += str(fields[row][key])
            except:
                csv += ""

        csv += "\n"

# check we have trade data to export
if trade_count > 0 or queued_count > 0:
    print("%d queued trade%s and %d executed trade%s found in your account." %
          (queued_count, "s" [queued_count == 1:], trade_count,
           "s" [trade_count == 1:]))
    # print str(queued_count) + " queded trade(s) and " + str(trade_count) + " executed trade(s) found in your account."
else:
    print("No trade history found in your account.")
    quit()


# choose a filename to save to
print("Choose a filename or press enter to save to `robinhood.csv`:")
try:
    input = raw_input
except NameError:
    pass
filename = input().strip()
if filename == '':
    filename = "robinhood.csv"

try:
    with open(filename, "w+") as outfile:
        outfile.write(csv)
except IOError:
    print("Oops.  Unable to write file to ", filename)


if args.dividends:
    fields=collections.defaultdict(dict)
    dividend_count = 0
    queued_dividends = 0

    # fetch order history and related metadata from the Robinhood API
    dividends = robinhood.get_endpoint('dividends')


    paginated = True
    page = 0
    while paginated:
        for i, dividend in enumerate(dividends['results']):
            symbol = cached_instruments.get(dividend['instrument'], False)
            if not symbol:
                symbol = robinhood.get_custom_endpoint(dividend['instrument'])['symbol']
                cached_instruments[dividend['instrument']] = symbol

            fields[i + (page * 100)]['symbol'] = symbol

            for key, value in enumerate(dividend):
                if value != "executions":
                    fields[i + (page * 100)][value] = dividend[value]

            fields[i + (page * 100)]['execution_state'] = order['state']
        # paginate
        if dividends['next'] is not None:
            page = page + 1
            orders = robinhood.get_custom_endpoint(str(dividends['next']))
        else:
            paginated = False

    # for i in fields:
    # 	print fields[i]
    # 	print "-------"



    # CSV headers
    keys = fields[0].keys()
    keys = sorted(keys)
    csv = ','.join(keys) + "\n"

    # CSV rows
    for row in fields:
        #Check if date is compliant with filters
        date_object = datetime.datetime.strptime(fields[row]['payable_date']+"12", "%Y-%m-%d%H")
        filtered = False
        if start_date != None:
            if start_date > date_object:
                filtered = True
        if end_date != None:
            if end_date < date_object:
                filtered = True
        if not filtered:
            if fields[row]['state'] == "paid":
                dividend_count += 1
            elif fields[row]['state'] == "pending":
                queued_dividends += 1
            for idx, key in enumerate(keys):
                if (idx > 0):
                    csv += ","
                try:
                    csv += str(fields[row][key])
                except:
                    csv += ""

            csv += "\n"

    # check we have trade data to export
    if dividend_count > 0 or queued_dividends > 0:
        print("%d queued dividend%s and %d executed dividend%s found in your account." %
              (queued_dividends, "s" [queued_count == 1:], dividend_count,
               "s" [trade_count == 1:]))
        # print str(queued_count) + " queded trade(s) and " + str(trade_count) + " executed trade(s) found in your account."
    else:
        print("No dividend history found in your account.")
        quit()

    # choose a filename to save to
    print("Choose a filename or press enter to save to `dividends.csv`:")
    try:
        input = raw_input
    except NameError:
        pass
    filename = input().strip()
    if filename == '':
        filename = "dividends.csv"

    # save the CSV
    try:
        with open(filename, "w+") as outfile:
            outfile.write(csv)
    except IOError:
        print("Oops.  Unable to write file to ", filename)

if args.profit:
    profit_csv = profit_extractor(csv, filename)
