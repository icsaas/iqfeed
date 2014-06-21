from trash.rq import rediscache
from gevent import monkey;monkey.patch_os()
#from functionspp import calcsymbol
import multiprocessing
from Model.trademodel import  engine
from sqlalchemy import MetaData

import pandas.io.sql as psql

import MySQLdb

import functionspp
#metadata=MetaData(bind=engine)
#metadata.reflect(bind=engine)
def run2(proj):
    symbolsin=proj.symbol
    causesin=proj.cause
    pool_size=multiprocessing.cpu_count()*2
    pool=multiprocessing.Pool(processes=pool_size)
    #metadata=MetaData(bind=engine)
    #metadata.reflect(bind=engine)
    for symbol in symbolsin:
        pool.apply_async(functionspp.calcsymbol,args=(proj,symbol))
    pool.close()
    pool.join()
   # web.ctx.orm.execute(proj.__table__.update().where(proj.__table__.c.projid == proj.projid).values(btstatus=True))

def run(proj):
    symbolsin=proj.symbol
    causesin=proj.cause
    projid=proj.projid
    ma=multiprocessing.Manager()
    queue=ma.Queue()
    pool_size=multiprocessing.cpu_count()*2
    pool=multiprocessing.Pool(processes=pool_size)
    result=pool.map_async(calcsymbol,((proj,symbol,queue) for symbol in symbolsin))
    time.sleep(1)
    causedf=None
    while not queue.empty():
        print "gone in to loop now"
        item=queue.get()
        #assure item[1] type
        symbolid=item[0]
        if isinstance(item[1],int):
            if item[1]==0:
                #update the symbol status
                try:
                    conn=MySQLdb.connect(host='localhost',user='david',passwd='david',db='david_trade')
                    cur=conn.cursor()
                    expression="update symbol set status=0 where symbolid="+str(symbolid)+";"
                    #tradedb.update('symbol',where="symbolid =$symbolid",vars={'symbolid':symbolid}, btstatus = 0)
                    print "update 0"
                    cur.execute(expression)
                    conn.commit()
                    cur.close()
                    conn.close()
                except MySQLdb.Error,e:
                    print "error in update 0  "
                    print "Mysql Error %d:%s" %(e.args[0],e.args[1])
            elif item[1]==1:
                print "update select cause"
                resultid=str(projid)+'_'+str(symbolid)
                try:
                    conn=MySQLdb.connect(host='localhost',user='david',passwd='david',db='david_trade')
                    cur=conn.cursor()
                    expression="select btstatus from symbol where symbolid="+str(symbolid)+";"
                    cur.execute(expression)
                    #check btstatus to continue calc backtester
                    #will have a condition query from mysql
                    btstatus=cur.fetchone()
                    if btstatus==1:
                        return
                    else:
                        #select the causetable from mysql to calc backtester
                        resultid=str(projid)+'_'+str(symbolid)
                        tablename=resultid+'_result'
                        expression="select * from "+tablename+";"
                        causedf=psql.frame_query(expression, con=conn)
                        #generate resultdf with cp and ncp for cause
                        causedf.set_index('Date',drop=True,inplace=True)
                    conn.commit()
                    cur.close()
                    conn.close()
                    calcbtcor(proj,causedf,resultid)
                except MySQLdb.Error,e:
                    print "error in select cause"
                    print "Mysql Error %d:%s" %(e.args[0],e.args[1])
        else:
            #save causedf and use the item[2] to calc backtester
            print "update 1"
            causedf=item[1]
            resultid=str(projid)+'_'+str(symbolid)
            tablename=resultid+'_result'
            try:
                mysql_cn=MySQLdb.connect(host='localhost',user='david',passwd='david',db='david_trade')
                cur = mysql_cn.cursor()
                exists = psql.table_exists(name=tablename, con=mysql_cn, flavor='mysql')
                if not exists:
                    psql.write_frame(frame=causedf.where(pd.notnull(causedf),None), name=tablename, con=mysql_cn, if_exists='replace',flavor='mysql')
                else:
                    expression = "DROP TABLE "+tablename+";"
                    cur.execute(expression)
                    psql.write_frame(frame=causedf.where(pd.notnull(causedf),None), name=tablename, con=mysql_cn, if_exists='replace',flavor='mysql')
                #tradedb.update('symbol',where="symbolid =$symbolid",vars={'symbolid':symbolid}, status = 1)
                #update symbol expression
                expression="update symbol set status=1 where symbolid="+str(symbolid)+";"
                cur.execute(expression)
                mysql_cn.commit()
                cur.close()
                mysql_cn.close()
            except MySQLdb.Error,e:
                print "error in update cause status"
                print "Mysql Error %d:%s" %(e.args[0],e.args[1])
            calcbtcor(proj,causedf,resultid)

        #to calc backtesterdf
    time.sleep(1)
    result.join()
    for item in result:
        item.join()
    print result
    #print result.get()
    pool.close()
    pool.join()

def calcbtcor(project,causedf,resultid):
    if causedf is None:
        return
    effectcolumn=causedf['effect']
    resultdf=causedf
    for column in resultdf.columns:
        if (column.startswith('ncp') or column.startswith('cp'))==False:
            resultdf=resultdf.drop(column,axis=1)
    backtesterdf=pd.DataFrame(index=resultdf.columns,columns=[str(item) for item in gtcp_list])
    if len(resultdf.columns) == 0:
        return
    for column in resultdf.columns:
        backtesterdf.ix[column]= backtesterwrap(gtcp_list)(resultdf[column],effectcolumn)
    #calc RTSR
    #psql.write_frame(backtesterdf.where(pd.notnull(backtesterdf), None),con=mysql_cn,name=tablename,if_exists='append',flavor='mysql')
    RTSR=round(float(len(effectcolumn[effectcolumn==True].index))/len(effectcolumn.index),3)
    #correaltion
    tcpser=pd.Series(backtesterdf.columns,index=backtesterdf.columns)
    ratertsr=project.ratertsr
    coefficient=project.coefficient
    ncoefficient=project.ncoefficient
    correlationdf=pd.DataFrame(index=backtesterdf.index,columns=['correlation','predictive'])
    for index in backtesterdf.index:
        strlist=backtesterdf.ix[index]
        tcplist=[round(float(item)/100,3) for item in strlist]
        sr_corr=tcpser.corr(backtesterdf.ix[index])
        if index.startswith('ncp'):
            corr=ncoefficient
        elif index.startswith('cp'):
            corr=coefficient
        if np.isnan(sr_corr)==False and sr_corr>corr and backtesterdf.ix[index].min()>ratertsr+RTSR:
            predictive=True
        else:
            predictive=False
        correlationdf.ix[index]=pd.Series([sr_corr,predictive],name=index,index=['correlation','predictive'])
    #save backtesterdf
    tablename=resultid+'_backtester'
    wbacktesterdf=backtesterdf.reset_index()
    try:
        mysql_cn= MySQLdb.connect(host='localhost',port=3306,user='david', passwd='david',db='david_trade')
        exists = psql.table_exists(name=tablename, con=mysql_cn, flavor='mysql')
        if not exists:
            psql.write_frame(frame=wbacktesterdf.where(pd.notnull(wbacktesterdf),None), name=tablename, con=mysql_cn, if_exists='replace',flavor='mysql')
        else:
            create = "DROP TABLE "+tablename+";"
            cur = mysql_cn.cursor()
            cur.execute(create)
            mysql_cn.commit()
            cur.close()
            psql.write_frame(frame=wbacktesterdf.where(pd.notnull(wbacktesterdf),None), name=tablename, con=mysql_cn, if_exists='replace',flavor='mysql')
        #save correlationdf
        tablename=resultid+'_correlation'
        correlationdf=correlationdf.reset_index()
        exists = psql.table_exists(name=tablename, con=mysql_cn, flavor='mysql')
        if not exists:
            psql.write_frame(frame=correlationdf.where(pd.notnull(correlationdf),None), name=tablename, con=mysql_cn, if_exists='replace',flavor='mysql')
        else:
            expression = "DROP TABLE "+tablename+";"
            cur = mysql_cn.cursor()
            cur.execute(expression)
            psql.write_frame(frame=correlationdf.where(pd.notnull(correlationdf),None), name=tablename, con=mysql_cn, if_exists='replace',flavor='mysql')
            mysql_cn.commit()
            cur.close()
            mysql_cn.close()
    except MySQLdb.Error,e:
            print "Mysql Error %d:%s" %(e.args[0],e.args[1])
    logger.debug("backtester and correlation completed")

def backtesterwrap(tcplist):
    def backtester_wrap(cpseries,effectseries):
        sr_list=[]
        for tcp in tcplist:
            number=0
            SR=0
            i=0
            for i in range(len(cpseries.index)):
                if cpseries.ix[i] is None:
                    continue
                if cpseries.ix[i]>tcp:
                    number=number+1
                    if effectseries.ix[i]:
                        SR=SR+1
            if number == 0:
                srvalue=0
            else:
                srvalue=round(float(SR)/number,3)*100
            sr_list.append(srvalue)
        return pd.Series(sr_list,name=cpseries.name,index=[str(item) for item in tcplist])
    return backtester_wrap


import views
import time
import json
#import umysqldb
#umysqldb.install_as_MySQLdb()

#seting files
from Config.causeconfig import gcausedict,gtcp_list

#math function tool
import numpy as np
from tools import *
import pandas as pd
import talib

from tool.logger import initlog
logger=initlog(__name__)

#Load Project
def effectfunc(highTiks,closeTiks,lcalcdays,leffectpercent):
    highTiks=highTiks.copy()
    closeTiks=closeTiks.copy()
    highTiks.sort()
    closeTiks.sort()
    effectser=pd.Series(index=highTiks.index)
    fixedhighTiks=np.zeros(len(highTiks)+lcalcdays-1)
    fixedhighTiks[:len(highTiks)]=highTiks.values
    fixedhighTiks[len(highTiks):]=highTiks.values[-1]
    highTiks_window=rolling_window(fixedhighTiks,lcalcdays)
    i=0
    for item_window in highTiks_window:
        if item_window.max()>round(float(closeTiks[i])*(1+leffectpercent),2):
            effectser[i]=True
        else:
            effectser[i]=False
        i+=1
    return effectser


def cause1func(closeTiks):
    count=0
    reversed_closeTiks = closeTiks[::-1]
    for i in xrange(len(reversed_closeTiks)-1):
        if reversed_closeTiks[i+1]>reversed_closeTiks[i]:
            count+=1
        else:
            break
    return count

def cause2func(closeTiks):
    count=0
    reversed_closeTiks=closeTiks[::-1]
    for i in xrange(len(reversed_closeTiks)-1):
        if reversed_closeTiks[i+1]<reversed_closeTiks[i]:
            count+=1
        else:
            break
    return count

def cause3func():
    pass

def cause4func(highTiks,closeTiks,xday):
    #Allocation a new array len(highTiks)+xday to fix rolling_window
    cause4ser=pd.Series(index=highTiks.index)
    fixedhighTiks=np.zeros(len(highTiks)+xday-1)
    fixedhighTiks[:len(highTiks)]=highTiks.values
    highTiks_window=rolling_window(fixedhighTiks,xday)
    i=0
    #assign the value to Series
    #the numbe of highTiks_window equals len(highTiks)
    for item_window in highTiks_window:
        cause4ser.ix[i]=round(((closeTiks[i] - item_window.max()) / item_window[0]) * 100, 2)
        i+=1
    return cause4ser

def cause5func(lowTiks,closeTiks,xday):
    cause5ser=pd.Series(index=lowTiks.index)
    fixedlowTiks=np.zeros(len(lowTiks)+xday-1)
    fixedlowTiks[:len(lowTiks)]=lowTiks.values
    lowTiks_window=rolling_window(fixedlowTiks,xday)
    i=0
    for item_window in lowTiks_window:
        cause5ser.ix[i]=round(((closeTiks[i]-item_window.min())/item_window[0])*100,2)
        i+=1
    return cause5ser

def cause6func(sector_df,closeTiks):
    i=0
    cause6ser=pd.Series(index=closeTiks.index)
    for index,itemrow in sector_df.iterrows():
        cause6ser.ix[i]=round(closeTiks.ix[i]/itemrow.mean(),2)
        i+=1
    return cause6ser
def cause7func(Volumes,spyvolumes):
    cause7ser=pd.Series(index=Volumes.index)
    i=0
    for item in Volumes:
        cause7ser.ix[i]=round(float(Volumes[i])/spyvolumes[i],2)
        i+=1
    return cause7ser
def cause8func(Volumes,highTiks,xday):
    cause8ser=pd.Series(index=Volumes.index)
    fixedhighTiks=np.zeros(len(highTiks)+xday-1)
    fixedhighTiks[:len(highTiks)]=highTiks.values
    highTiks_window=rolling_window(fixedhighTiks,xday)
    i=0
    for item_window in highTiks_window:
        cause8ser.ix[i]=round(((Volumes.ix[i]-item_window.max())/item_window[0])*100,2)
        i+=1
    return cause8ser
def cause9func(Volumes,lowTiks,xday):
    cause9ser=pd.Series(index=Volumes.index)
    fixedlowTiks=np.zeros(len(lowTiks)+xday-1)
    fixedlowTiks[:len(lowTiks)]=lowTiks.values
    lowTiks_window=rolling_window(fixedlowTiks,xday)
    i=0
    for item_window in lowTiks_window:
        cause9ser.ix[i]=round(((Volumes.ix[i]-item_window.max())/item_window[0])*100,2)
        i+=1
    return cause9ser

def cause10func():
    pass
def cause11func():
    pass
def cause12func(closeTiks,lowTiks,highTiks,xday=60):
    #For within the previous 60 days, (Current Close - Lowest Low)/(Highest High - Lowest Low) * 100
    cause12ser=pd.Series(index=closeTiks.index)
    fixedlowTiks=np.zeros(len(lowTiks)+xday-1)
    fixedhighTiks=np.zeros(len(highTiks)+xday-1)
    fixedlowTiks[:len(lowTiks)]=lowTiks.values
    fixedhighTiks[:len(highTiks)]=highTiks.values
    lowTiks_window=rolling_window(fixedlowTiks,xday)
    highTiks_window=rolling_window(fixedhighTiks,xday)
    i=0
    #iterate closeTiks maybe a better idea
    closeTiks=closeTiks.copy()
    for item in closeTiks:
        minlowTik=lowTiks_window[i].min()
        maxhighTik=highTiks_window[i].max()
        cause12ser.ix[i]=round(((item-minlowTik)/(maxhighTik-minlowTik))*100,2)
        i+=1
    return cause12ser
def cause13func(spycloses,closeTiks):
    cause13ser=pd.Series(index=closeTiks.index)
    i=0
    looplen=min(len(closeTiks.index),len(spycloses))
    for i in xrange(looplen):
        cause13ser.ix[i]=round(float(closeTiks.ix[i])/spycloses[i],2)
        i+=1
    return cause13ser

def cause14func():
    pass
def cause15func():
    pass
def cause16func():
    pass

def get_season(date):
  # convert date to month and day as integer (md), e.g. 4/21 = 421, 11/17 = 1117, etc.
  m = date.month * 100
  d = date.day
  md = m + d

  if ((md > 320) and (md < 621)):
    s = 1 #spring
  elif ((md > 620) and (md < 923)):
    s = 2 #summer
  elif ((md > 922) and (md < 1223)):
    s = 3 #fall
  else:
    s = 4 #winter
  return s

def rolling_window(a,window):
    shape=a.shape[:-1]+(a.shape[-1]-window+1,window)
    strides=a.strides+(a.strides[-1],)
    return np.lib.stride_tricks.as_strided(a,shape=shape,strides=strides)

def calcsymbol_phraseI(project, symbol):
    #DataFrame fixing
    #an important information to reflect the schema to metadata
    metadata=MetaData(bind=engine)
    metadata.reflect(bind=engine)
    symbolid = symbol.symbolid
    projid=project.projid
    resultid = str(projid) + '_' + str(symbolid)
    symbolname = symbol.symbolname
    lsymbolname = symbolname.lower()
    tablename = lsymbolname + 'daily'
    rs= rediscache.tablecache(tablename)
    rs_dict={
        'Date':[item['dateValue'] for item in rs],'openTik':[float(item['openTik']) for item in rs],
        'highTik':[float(item['highTik']) for item in rs],'lowTik':[float(item['lowTik']) for item in rs],
        'closeTik':[float(item['closeTik']) for item in rs],'Volume':[item['totalVolume'] for item in rs]
        }
    rs_df=pd.DataFrame(rs_dict,index=rs_dict['Date'],columns=rs_dict.keys())
    rs_df.set_index('Date',drop=True,inplace=True)
    rs_df=rs_df.sort(ascending=False)
    cause_df=pd.DataFrame(index=rs_df.index)
    lcauses=project.cause
    leffectpercent=project.effectpercent
    lcalcdays=project.calcdays
    ###########effect###########
    #effect it is to look forward
    highTiks=rs_df['highTik']
    closeTiks=rs_df['closeTik']

    cause_df['effect']=effectfunc(highTiks,closeTiks,lcalcdays,leffectpercent)
    #######effect#######
    for lcause in lcauses:
        if lcause.causename=='cause1':
            #Number of day High
            cause1ser=pd.rolling_apply(rs_df['closeTik'],len(rs_df['closeTik']),cause1func,min_periods=2)
            resultname=gcausedict['cause1']
            cause_df[resultname]=cause1ser
        elif lcause.causename=='cause2':
            #Number of day low
            cause2ser=pd.rolling_apply(rs_df['closeTik'],len(rs_df['closeTik']),cause2func,min_periods=2)
            resultname=gcausedict['cause2']
            cause_df[resultname]=cause2ser
        elif lcause.causename=='cause3':
            #rs_df['Volume']
            cause3ser=rs_df['Volume']
            resultname=gcausedict['cause3']
            cause_df[resultname]=cause3ser
        elif lcause.causename=='cause4':
            #day percent change bullish
            lcausevalue=json.loads(lcause.causevalue)
            xdayslist=lcausevalue['cause4']
            for item in xdayslist:
                xday=int(item)
                cause4ser=cause4func(rs_df['highTik'],rs_df['closeTik'],xday)
                resultname = item+" "+gcausedict['cause4']
                cause_df[resultname]=cause4ser
        elif lcause.causename=='cause5':
            #day percent change bearish
            lcausevalue=json.loads(lcause.causevalue)
            xdayslist=lcausevalue['cause5']
            for item in xdayslist:
                xday=int(item)
                cause5ser=cause5func(rs_df['lowTik'],rs_df['closeTik'],xday)
                resultname = item+" "+gcausedict['cause5']
                cause_df[resultname]=cause5ser
        elif lcause.causename=='cause6':
            #Relative Strength vs Sector
            symbolAbbvar = dict(symbolAbb=symbolname)
            sectorsymbols= rediscache.sector(symbolname)
            sectorsymbolnames=[]
            for symbol in sectorsymbols:
                sectorsymbolnames.append(symbol.symbolAbb)
            rs_sector=[]
            rs_sector_p=[]
            close_list=[]
            sectorser={}
            for sectorsymbolname in sectorsymbolnames:
                lsymbolname=sectorsymbolname.lower()
                lsymbolname=lsymbolname+'daily'
                rs_list=rediscache.tablecache(lsymbolname)
                close_list=[float(result['closeTik']) for result in rs_list]
                sectorser[sectorsymbolname]=close_list
            sector_df=pd.DataFrame(sectorser)
            cause_df[resultname]=cause6func(sector_df,rs_df['closeTik'])
        elif lcause.causename=='cause7':
            #Volume relative to Spy
            spyvolumes=[]
            #spys=list(db.select('spydaily',order='dateValue DESC'))
            spys= rediscache.tablecache('spydaily')
            spyvolumes=np.array([float(item['totalVolume'])for item in spys])
            resultname=gcausedict['cause7']
            cause_df[resultname]=cause7func(rs_df['Volume'],spyvolumes)
        elif lcause.causename=='cause8':
            #day percent Volume change bullish
            lcausevalue=json.loads(lcause.causevalue)
            xdays3list=lcausevalue['cause8']
            for item in xdays3list:
                xday=int(item)
                resultname = item+" "+gcausedict['cause8']
                cause_df[resultname]=cause8func(rs_df['Volume'],rs_df['highTik'],xday)
        elif lcause.causename=='cause9':
            #day percent Volume change bearish
            lcausevalue=json.loads(lcause.causevalue)
            xdays4list=lcausevalue['cause9']
            for item in xdays4list:
                xday=int(item)
                resultname=item+" "+gcausedict['cause9']
                cause_df[resultname]=cause9func(rs_df['Volume'],rs_df['lowTik'],xday)
        elif lcause.causename=='cause10':
            #Month --rolling_apply
            resultname=gcausedict['cause10']
            cause_df[resultname]=pd.Series([item.month for item in rs_df.index],index=rs_df.index)
        elif lcause.causename=='cause11':
            #Season --rolling_apply
            resultname=gcausedict['cause11']
            cause_df[resultname]=pd.Series([get_season(item) for item in rs_df.index],index=rs_df.index)
        elif lcause.causename=='cause12':
            #Stochastic
            #See here for reference. We will not use %D. We will set the lookback period to 60 days.
            #For within the previous 60 days, (Current Close - Lowest Low)/(Highest High - Lowest Low) * 100
            resultname=gcausedict['cause12']
            cause_df[resultname]=cause12func(rs_df['closeTik'],rs_df['lowTik'],rs_df['highTik'],xday=60)
        elif lcause.causename=='cause13':
            #Relative Strength vs SPY
            spycloses=[]
            spys= rediscache.tablecache('spydaily')
            spycloses=[float(item['closeTik']) for item in spys]
            resultname=gcausedict['cause13']
            cause_df[resultname]=cause13func(spycloses,rs_df['closeTik'])
        elif lcause.causename=='cause14':
            #ATR
            high=rs_df['highTik'].values
            low=rs_df['lowTik'].values
            close=rs_df['closeTik'].values
            atr = talib.ATR(high, low, close, timeperiod=14)
            resultname=gcausedict['cause14']
            cause_df[resultname]=pd.Series(atr,index=rs_df.index)
        elif lcause.causename=='cause15':
            #AROONOSC
            high=rs_df['highTik'].values
            low=rs_df['lowTik'].values
            aroonosc = talib.AROONOSC(high, low, timeperiod=14)
            resultname=gcausedict['cause15']
            cause_df[resultname]=pd.Series(aroonosc,index=rs_df.index)
        elif lcause.causename=='cause16':
            #ADX
            resultname=gcausedict['cause16']
            high=rs_df['highTik'].values
            low=rs_df['lowTik'].values
            close=rs_df['closeTik'].values
            adx=talib.ADX(high,low,close,timeperiod=lcalcdays)
            cause_df[resultname]=pd.Series(adx,index=rs_df.index)
        elif lcause.causename=='cause17':
            #RSI
            close=rs_df['closeTik'].values
            rsi=talib.RSI(close, timeperiod=14)
            resultname=gcausedict['cause17']
            cause_df[resultname]=pd.Series(rsi,index=rs_df.index)
    cause_df['symbolid']=symbolid
    return cause_df

from math import floor
def IsinUnit(mincause,causeunit,causevalue):
    def IsinUnit_cause(causeseries,effectseries):
        count=0
        cpcount=0
        for i in range(len(causeseries.index)):
            if floor((causeseries.ix[i]-mincause)/causeunit)==floor((causevalue-mincause)/causeunit):
                count=count+1
                if effectseries.ix[i]:
                    cpcount+=1
        if count==0:
            cp=None
        else:
            cp=round(float(cpcount)/count,3)*100
        return (count,cp)
    return IsinUnit_cause

def calc_func(causecolumn,effectcolumn,segcount,calcdays,backcount):
    mincause=causecolumn.min()
    maxcause=causecolumn.max()
    resultname=causecolumn.name
    if causecolumn.name in ['Month','Season']:
        segcount=4
    causeunit=(maxcause-mincause)/segcount
    ccname='cc for '+resultname
    cpname='cp for '+resultname
    nccname='ncc for '+resultname
    ncpname='ncp for '+resultname
    causelen=len(causecolumn.index)
    cclist=[]
    cplist=[]
    ncclist=[]
    ncplist=[]
    for i in range(causelen):
        startday=i+calcdays
        endday=startday+backcount
        if startday>=causelen:
            startday=causelen-1
            endday=causelen
        elif endday>=causelen:
            endday=causelen
        causevalue=causecolumn.ix[i]
        backcolumn=causecolumn.ix[startday:endday]
        backeffect=effectcolumn.ix[startday:endday]
        (cc,cp)=IsinUnit(mincause,causeunit,causevalue)(backcolumn,backeffect)
        cclist.append(cc)
        cplist.append(cp)
        if cp is None:
            ncp = None
        else:
            ncp=100-cp
        ncplist.append(ncp)
    return pd.DataFrame({ccname:cclist,cpname:cplist,ncpname:ncplist},index=causecolumn.index)


def calcsymbol(args):
    project=args[0]
    symbol=args[1]
    #lcauses=args[2]
    queue=args[2]
    projid = project.projid
    symbolid=symbol.symbolid
    lcalcdays = project.calcdays
    lcauses=project.cause
    leffectpercent = project.effectpercent
    if symbol.status != 1:#runing or completed
        #queue.put((symbolid,0))
        causedf=calcsymbol_phraseI(project,symbol)
        logger.debug("cause caculated")
        segcount=project.segcount
        lcalcdays=project.calcdays
        backcount=project.backcount
        calcdf=causedf.drop(["symbolid","effect"],axis=1)
        resultdf=pd.DataFrame(index=causedf.index)
        effectcolumn=causedf['effect']
        for column in calcdf.columns:
            resultdf=resultdf.join(calc_func(calcdf[column],effectcolumn,segcount,lcalcdays,backcount))
        causedf=causedf.join(resultdf)
        causedf=causedf.reset_index()
        queue.put((symbolid,causedf))
        logger.debug('cp caculated')
        return "OK"
    else:
        queue.put((symbol,1))
        #load dataframe from mysql
        return

    #psql.write_frame(correlationdf.where(pd.notnull(correlationdf), None),con=mysql_cn,name=tablename,if_exists='append',flavor='mysql')
    #df_mysql = psql.frame_query('select * from VIEWS;', con=mysql_cn)
    #backtester


