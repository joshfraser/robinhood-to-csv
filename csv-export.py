from Robinhood import Robinhood
import getpass
import collections
import argparse
import ast

logged_in = False

# hard code your credentials here to avoid entering them each time you run the script
username = ""
password = ""

parser = argparse.ArgumentParser(description='Export Robinhood trades to a CSV file')
parser.add_argument('--debug', action='store_true', help='store raw JSON output to debug.json')
parser.add_argument('--username', default=username, help='your Robinhood username')
parser.add_argument('--password', default=password, help='your Robinhood password')
args = parser.parse_args()
username = args.username
password = args.password

robinhood = Robinhood();

# login to Robinhood
while not logged_in:
	if username == "":
		print("Robinhood username:")
		try: input = raw_input
		except NameError: pass
		username = input()
	if password == "":
		password = getpass.getpass()

	logged_in = robinhood.login(username=username, password=password)
	if logged_in == False:
		password = ""
		print ("Invalid username or password.  Try again.\n")

fields = collections.defaultdict(dict)
trade_count = 0
queued_count = 0

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
		instrument = robinhood.get_custom_endpoint(order['instrument'])
		fields[i+(page*100)]['symbol'] = instrument['symbol']
		for key, value in enumerate(order):
			if value != "executions":
				fields[i+(page*100)][value] = order[value]
		if order['state'] == "filled":
			trade_count += 1
			for key, value in enumerate(executions[0]):
			 	fields[i+(page*100)][value] = executions[0][value]
		elif order['state'] == "queued":
			queued_count += 1
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
if trade_count > 0 or queded_count > 0:
	print("%d queued trade%s and %d executed trade%s found in your account." % (queued_count, "s"[queued_count==1:], trade_count, "s"[trade_count==1:]))
	# print str(queued_count) + " queded trade(s) and " + str(trade_count) + " executed trade(s) found in your account."
else:
	print("No trade history found in your account.")
	quit()

# CSV headers
keys = fields[0].keys()
keys = sorted(keys)
csv = ','.join(keys)+"\n"

# CSV rows
for row in fields:
	for idx, key in enumerate(keys):
		if(idx > 0):
			csv += ","
		try:
			csv += str(fields[row][key])
		except:
			csv += ""

	csv += "\n"

# choose a filename to save to
print("Choose a filename or press enter to save to `robinhood.csv`:")
try: input = raw_input
except NameError: pass
filename = input().strip()
if filename == '':
	filename = "robinhood.csv"

# save the CSV
try:
    with open(filename, "w+") as outfile:
        outfile.write(csv)
except IOError:
    print("Oops.  Unable to write file to ",filename)



