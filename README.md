# Robinhood to CSV

A Python script to export your [Robinhood](https://www.robinhood.com) trades to a .csv file.  Based on the [Robinhood library by Rohan Pai](https://github.com/Jamonek/Robinhood).  Read the back story on my [blog](http://www.onlineaspect.com/2015/12/17/export-robinhood-investments-to-csv).

Works on Python 2.7+ and 3.5+

#### Install:
pip install -r requirements.txt

#### Run:

For exporting stock trades, run:

`python csv-export.py`

For exporting options trades, run:

`python csv-options-export.py`


For Device_Token go to your browser

    Go to robinhood.com. Log out if you're already logged in
    Right click > Inspect element
    Click on Network tab
    -Enter "token" in the input line at the top where it says "Filter URLs"
    With the network monitor-er open, login to Robinhood
    You'll see two new urls pop up that say "api.robinhood.com" and "/oauth2/token"
    Click the one that's not 0 bytes in size
    Click on Headers, then scroll down to the Request Payload section
    Here, you'll see new JSON parameters for your login. What you'll need here is the device token.
