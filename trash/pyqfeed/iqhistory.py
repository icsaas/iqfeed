#!/usr/bin/env python
'''
Scrape history data for a set of instruments from IQfeed.
'''

import os, sys, logging, optparse, time, datetime, types, gzip, csv
import pyqfeed.History
import pyqfeed.Listener


class IQHistoryListener(pyqfeed.Listener.Listener):
    def __init__(self, instrument, compression=False, date_split=False):
        self.instrument = instrument
        self.compression = compression
        self.outfds = {}
        self.date_split = date_split

    def on_error(self, message):
        logging.error(message)

    def on_message(self, message, **kwargs):
        if message:
            print message
            return True

        split_str = message.split(",")
        date = split_str[0].partition(" ")[0]

        if self.date_split:
            outfilename = "%s_%s.csv" % (date, self.instrument)
        else:
            outfilename = "%s-daily.csv" % (self.instrument)

        if not self.outfds.has_key(outfilename):
            if self.compression:
                self.outfds[outfilename] = gzip.open(outfilename + ".gz", "wb")
            else:
                self.outfds[outfilename] = open(outfilename, "wb")
            logging.info("Opening %s" % outfilename)
        self.outfds[outfilename].write(message + "\n")


    def on_data_end(self):
        logging.info("Finished.")
        for fd in self.outfds.values():
            fd.close()


def scrapeHistory(host, port, symbols, start_date, num_days=1):
    if type(start_date) == types.StringType:
        start_date = datetime.date(int(start_date[0:4]), int(start_date[5:7]), int(start_date[8:10]))
    SERVER_ADDR = (host, port)
    client = pyqfeed.History.HistoryClient(SERVER_ADDR)
    # Set up the IQfeed client.

    for symbol in symbols:
        listener = IQHistoryListener(symbol, date_split=True)
        client.set_listener('iqhislistener', listener)
        client.getHistory(symbol, start_date, num_days)
        client.del_listener('iqhislistener')


def loadSymbolsFromFile(filename):
    base, ext = os.path.splitext(filename)
    symbols = []

    if ext.lower() == ".csv":
        for row in csv.reader(open(filename, "rb")):
            symbols.append(row[0])

    return symbols


def main():
    # Vanilla command-line arg parsing. Run with -h to see pretty output"
    parser = optparse.OptionParser()
    parser.add_option('-p', dest="port", type="int", default=5009, help="IQFeed service port. Default=5009")
    parser.add_option('-s', dest="host", type="string", default="127.0.0.1",
                          help="IQFeed service host. Default=localhost")
    parser.add_option('-f', dest="input_file", type="string", help="Input file")
    parser.add_option('-i', dest="instruments", type="string", help="Comma-separated list of instruments")
    parser.add_option('-d', dest="start_date", type="string", default=str(datetime.date.today()),
                          help="Start date. Default=today")
    parser.add_option('-n', dest="num_days", type="int", default=1, help="Number of days of data to get")
    parser.add_option("--debug", action="store_true", dest="debug", default=False, help="Debug this script?")
    (options, args) = parser.parse_args()

    if options.debug:
        logging.basicConfig(level=logging.DEBUG)

    if not options.input_file and not options.instruments:
        parser.error("Please specify an input file with -f or a list of instruments with -i")

    if options.instruments:
        symbols = [x.strip() for x in options.instruments.split(",")]
    else:
        symbols = loadSymbolsFromFile(options.input_file)

    scrapeHistory(options.host, options.port, symbols, options.start_date, options.num_days)


if __name__ == "__main__":
    main()
