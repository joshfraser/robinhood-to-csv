# Robinhood to CSV

A Python script to export your [Robinhood](https://www.robinhood.com) trades to a .csv file.  Based on the [Robinhood library by Rohan Pai](https://github.com/Jamonek/Robinhood).  Read the back story on my [blog](http://www.onlineaspect.com/2015/12/17/export-robinhood-investments-to-csv).  If you’re new to Robinhood, feel free to use [my Robinhood referral link](http://share.robinhood.com/joshf12) when you sign up to get a free share of a randomly selected stock when you fund your account.

Works on Python 2.7+ and 3.5+

#### Install:
pip install -r requirements.txt

#### Run:
python csv-export.py

#### Options:
If you use the profit parameter it will calculate a profit and tax amount (default 25%) per sale event based on the previous sales.
python csv-export.py --profit
