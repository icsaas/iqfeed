import Listener

from sqlalchemy import Table, Column, MetaData
from sqlalchemy.types import Integer, Float, String,DateTime
from sqlalchemy.orm import  mapper, clear_mappers

from Model.InitModel import *
from Model.iqfeedmodel import Option, OptionDailyHistory, OptionIntervalHistory, OptionTikHistory


import logging
import datetime,time

try:
    import queue      # Python 3
except ImportError:
    import Queue as queue

metadata = MetaData(iq_engine)

tabledict = {}
objdict = {}

class IQListener(Listener.Listener):
    global tabledict
    global objdict
    def __init__(self, instrument, compression=False, date_split=False, type='OPTIONCHAIN'):
        self.instrument = instrument
        self.compression = compression
        self.outfds = {}
        self.date_split = date_split
        self.iqsession = scoped_session(sessionmaker(bind=iq_engine))
        if type == 'OPTIONCHAIN':
            tablename = self.instrument.lower() + 'option'
            print tablename
            if iq_engine.dialect.has_table(iq_engine.connect(), tablename):
                optiontable = Table(tablename, metadata, autoload=True, autoload_with=iq_engine)
                tabledict[tablename] = optiontable
                objdict[tablename] = map_class_to_some_table(Option, optiontable, tablename)
                clear_mappers()
                mapper(Option, optiontable)
            else:
                optiontable = Table(tablename, metadata,
                    Column('storedate',DateTime,nullable=True),
                    Column('optionid', Integer, primary_key=True),
                    Column('optionname', String(20), nullable=True),
                    Column('marketid', Integer, nullable=True),
                    Column('sectypeid', Integer, nullable=True),
                    Column('symbolname', String(20), nullable=True),
                    Column('validupto', String(20), nullable=True),
                    Column('contracttype',String(20),nullable=True),
                    Column('contractquote', Float, nullable=True),
                    extend_existing=True
                )
                #objdict[tablename] = map_class_to_some_table(ResultNosql, resultnosql, tablename,)
                optiontable.drop(bind=iq_engine, checkfirst=True)
                optiontable.create(bind=iq_engine, checkfirst=True)
                clear_mappers()
                mapper(Option, optiontable)
        if type == 'HISTORY':
            #maybe create three table
            #dailyhistory table
            tablename = self.instrument.lower() + 'optiondailyhistory'
            print tablename
            if iq_engine.dialect.has_table(iq_engine.connect(), tablename):
                dailyhistorytable = Table(tablename, metadata, autoload=True, autoload_with=iq_engine)
                tabledict[tablename] = dailyhistorytable
                objdict[tablename] = map_class_to_some_table(OptionDailyHistory, dailyhistorytable, tablename)
                clear_mappers()
                mapper(OptionDailyHistory, dailyhistorytable)
            else:
                dailyhistorytable = Table(tablename, metadata,
                    Column('storedate',DateTime,nullable=True),
                    Column('datevalue',DateTime,nullable=True),
                    Column('id',Integer,primary_key=True),
                    Column('highTik',Float,nullable=True),
                    Column('lowTik',Float,nullable=True),
                    Column('openTik',Float,nullable=True),
                    Column('closeTik',Float,nullable=True),
                    Column('peroidvolume',Integer,nullable=True),
                    Column('openinterest',Integer,nullable=True),
                    Column('optionname',String(20),nullable=True),
                    extend_existing=True
                )
                #objdict[tablename] = map_class_to_some_table(ResultNosql, resultnosql, tablename,)
                dailyhistorytable.drop(bind=iq_engine, checkfirst=True)
                dailyhistorytable.create(bind=iq_engine, checkfirst=True)
                clear_mappers()
                mapper(OptionDailyHistory, dailyhistorytable)
                #intervalhistory table
            tablename = self.instrument.lower() + 'optionintervalyhistory'
            if iq_engine.dialect.has_table(iq_engine.connect(), tablename):
                intervalyhistorytable = Table(tablename, metadata, autoload=True, autoload_with=iq_engine)
                tabledict[tablename] = intervalyhistorytable
                objdict[tablename] = map_class_to_some_table(OptionIntervalHistory, intervalyhistorytable, tablename)
                mapper(OptionIntervalHistory, intervalyhistorytable)
            else:
                intervalyhistorytable = Table(tablename, metadata,
                    Column('storedate',DateTime,nullable=True),
                    Column('datevalue',DateTime,nullable=True),
                    Column('id',Integer,primary_key=True),
                    Column('highTik',Float,nullable=True),
                    Column('lowTik',Float,nullable=True),
                    Column('openTik',Float,nullable=True),
                    Column('closeTik',Float,nullable=True),
                    Column('totalvolume',Integer,nullable=True),
                    Column('peroidvolume',Integer,nullable=True),
                    Column('optionname',String(20),nullable=True),
                    extend_existing=True
                )
                #objdict[tablename] = map_class_to_some_table(ResultNosql, resultnosql, tablename,)
                intervalyhistorytable.drop(bind=iq_engine, checkfirst=True)
                intervalyhistorytable.create(bind=iq_engine, checkfirst=True)
                mapper(OptionIntervalHistory, intervalyhistorytable)
                #tickhistory table
            tablename = self.instrument.lower() + 'optiontickhistory'
            if iq_engine.dialect.has_table(iq_engine.connect(), tablename):
                tickhistorytable = Table(tablename, metadata, autoload=True, autoload_with=iq_engine)
                tabledict[tablename] = tickhistorytable
                objdict[tablename] = map_class_to_some_table(OptionTikHistory, tickhistorytable, tablename)
                mapper(OptionTikHistory, tickhistorytable)
            else:
                tickhistorytable = Table(tablename, metadata,
                    Column('storedate', DateTime, nullable=True),
                    Column('datevalue', DateTime, nullable=True),
                    Column('id',Integer,primary_key=True),
                    Column('lastprice',Float,nullable=True),
                    Column('lastsize',Integer,nullable=True),
                    Column('totalvolume',Integer,nullable=True),
                    Column('bid',Float,nullable=True),
                    Column('ask',Float,nullable=True),
                    Column('tickid',Float,nullable=True),
                    Column('reserv1',Integer,nullable=True),
                    Column('reserv2',Integer,nullable=True),
                    Column('recordtype',String(5),nullable=True),
                    Column('optionname',String(20),nullable=True),
                    extend_existing=True
                )
                #objdict[tablename] = map_class_to_some_table(ResultNosql, resultnosql, tablename,)
                tickhistorytable.drop(bind=iq_engine, checkfirst=True)
                tickhistorytable.create(bind=iq_engine, checkfirst=True)
                mapper(OptionTikHistory, tickhistorytable)

        self.iqsession.commit()
        self.iqsession.flush()
    def db_HDX(self, split_str):
        """
        The response format
        Request ID,TimeStamp(CCYY-MM-DD HH:MM:SS),High(Decimal),Low,Open,Close,Peroid Volume(Integer),Open Interest(Integer)
        """
        #one record one time
        try:
            datevalue=datetime.datetime.fromtimestamp(time.mktime(time.strptime(split_str[0],"%Y-%m-%d %H:%M:%S")))
            highTik=float(split_str[1])
            lowTik=float(split_str[2])
            openTik=float(split_str[3])
            closeTik=float(split_str[4])
            peroidvolume=int(split_str[5])
            openinterest=int(split_str[6])
            #now instrument as the optionname ,a little fused
            optionname=self.instrument
            resultobj=OptionDailyHistory(storedate=datetime.datetime.now(),datevalue=datevalue,highTik=highTik,
                                     lowTik=lowTik,openTik=openTik,closeTik=closeTik,peroidvolume=peroidvolume,openinterest=openinterest,optionname=optionname)
            #resultobj=resultobj.check_existing(datevalue=datevalue,optionname=optionname)
            self.iqsession.add(resultobj)
            self.iqsession.commit()
            self.iqsession.flush()
            logging.debug("db_HDX " + split_str)
        except ValueError as e:
            logging.debug("this is a pity")
            print e

    def db_HIX(self, split_str):
        """
        The response Format:RequestID,Time Stamp(CCYY-MM-DD HH:MM:SS),High,Low,Open,Close,Total Volume,Peroid Volume
        """
        try:
            datevalue=datetime.datetime.fromtimestamp(time.mktime(time.strptime(split_str[0],"%Y-%m-%d %H:%M:%S")))
            highTik=float(split_str[1])
            lowTik=float(split_str[2])
            openTik=float(split_str[3])
            closeTik=float(split_str[4])
            totalvolume=int(split_str[5])
            peroidvolume=int(split_str[6])
            optionname=self.instrument
            resultobj=OptionIntervalHistory(storedate=datetime.datetime.now(),datevalue=datevalue,highTik=highTik,
                lowTik=lowTik,openTik=openTik,closeTik=closeTik,totalvolume=totalvolume,peroidvolume=peroidvolume,optionname=optionname)
            resultobj=resultobj.check_existing(datevalue=datevalue,optionname=optionname)
            self.iqsession.add(resultobj)
            self.iqsession.commit()
            self.iqsession.flush()
            logging.debug("db_HIX " + split_str)
        except ValueError, e:
            logging.debug("this is a pity")
            print e

    def db_HTX(self, split_str):
        """
        The response Fromat:RequestID, Time Stamp,Last(Decimal),Last(Decimal),Last Size(Integer),Total Volume(Integer),Bid(Decimal),Ask(Decimal),TickID(Integer),Reserved,Reserved,Basis For Last(Character--Possible single character values include:C-Last Qualified Trade,E-Extended Trade=Form T trade)
        """
        try:
            datevalue=datetime.datetime.fromtimestamp(time.mktime(time.strptime(split_str[0],"%Y-%m-%d %H:%M:%S")))
            lastprice=float(split_str[1])
            lastsize=int(split_str[2])
            totalvolume=int(split_str[3])
            bid=float(split_str[4])
            ask=float(split_str[5])
            tickid=int(split_str[6])
            reserv1=int(split_str[7])
            reserv2=int(split_str[8])
            recordtype=None
            optionname=self.instrument
            resultobj=OptionTikHistory(storedate=datetime.datetime.now(),datevalue=datevalue,lastprice=lastprice,lastsize=lastsize,totalvolume=totalvolume,
                bid=bid,ask=ask,tickid=tickid,reserv1=reserv1,reserv2=reserv2,
                recordtype=recordtype,optionname=optionname)
            resultobj=resultobj.check_existing(datevalue=datevalue,optionname=optionname)
            logging.debug("db_HTX " + split_str)
        except ValueError, e:
            logging.debug("this is a pity")
            print e

    def db_OPTIONCHAIN(self, split_str):
        print split_str
        #split_str = split_str.split(",")
        firstindex = len(self.instrument)
        secondindex = firstindex + 5
        contracttype = "Call"
        for loption in split_str:
            if len(loption)<firstindex or '!ENDMSG!' in loption:
                continue
            if ':' in loption:
                contracttype='Put'
            #store the data into the database
            try:
                print loption[firstindex:secondindex]
                print loption[secondindex:]
                optionname = loption
                marketid = 0
                sectypeid = int(0)
                symbolname = loption[:firstindex]
                validupto = ''
                contractquote = 0
                resultobj = Option(storedate=datetime.datetime.now(),optionname=optionname, marketid=marketid,sectypeid=sectypeid, symbolname=symbolname,validupto=validupto,contracttype=contracttype,contractquote=contractquote)
                resultobj = resultobj.check_existing(optionname=optionname)
                self.iqsession.add(resultobj)
                self.iqsession.commit()
                self.iqsession.flush()
            except ValueError, e:
                logging.debug("this is a pity")
                print e


    def on_error(self, message):
        logging.debug('ERROR in iqfeed')
        #logging.error(message)

    def on_message(self, message):
        #print message
        logging.debug(message)
        split_str = message.split(",")
        firstindex = len(self.instrument)
        secondindex = firstindex + 5
        if 'HDX' in split_str:
            self.db_HDX(split_str[1:])
        if 'HIX' in split_str:
            self.db_HIX(split_str[1:])
        if 'HTX' in split_str:
            self.db_HTX(split_str[1:])
        if 'OPTIONCHAIN' in split_str:
            print split_str
            logging.debug(split_str[1:])
            self.db_OPTIONCHAIN(split_str[1:])
    def on_data_end(self):
        logging.info("Finished.")
        for fd in self.outfds.values():
            fd.close()





