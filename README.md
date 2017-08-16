# Robinhood Calculate Profit

This repo is based on [robinhood-to-csv repo of joshfraser](https://github.com/joshfraser/robinhood-to-csv) which used the [Robinhood library by Rohan Pai](https://github.com/Jamonek/Robinhood).

You most probably already have a robinhood account, but if not, you can use this referal link to get a free random stock when you sign up.
[Get a free stock from Robinhood](http://share.robinhood.com/korayk1).

At the moment this repo will create a csv file and calculate profit per sale

This are the things I will be adding
- simplify the table
- add a basic tax information (deduction of losses upto 3000 Dollars)

Works on Python 2.7+ and 3.5+

#### Install:
pip install -r requirements.txt

#### Run:
python csv-export.py

#### Options:
If you use the profit parameter it will calculate a profit and tax amount (default 25%) per sale event based on the previous sales.
python csv-export.py --profit
