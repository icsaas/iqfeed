import cPickle
import copy

from sqlalchemy import Table, MetaData

import views
from trash.rq import rediscache
import web
from Model.InitModel import getsession
from Model.trademodel import engine, metadata,tradedb
from Config.causeconfig import gcausedict

session = web.config._session

from Model.trademodel import db,Result,ResultObj
from Model.setting import *
from tools import *

render=web.template.render('templates',globals={"session":session})
metabeta = MetaData(engine)

tabledict = {}
objdict = {}
from tool.logger import initlog
logger=initlog(__name__)

def inserobj(dbobj,dbsession):
    if not isInstance(dbobj,ResultObj):
        raise Exception('resultboj', 'result')
    if dbobj.check_not_existing():
            #insert into DB
        dbsession.execute(Result.__table__.insert(),
                                {'resultid':dbobj.resultid,'resulttime':dbobj.resulttime,
                                 'origintime':dbobj.origintime,'resultname':dbobj.resultname,
                                 'resulttype':dbobj.resulttype,'resultvalue':dbobj.resultvalue,
                                 'projid':dbobj.projid,'symbolid':dbobj.symbolid,
                                 'causename':dbobj.causename,'causeid':dbobj.causeid,
                                 'backtesterflag':dbobj.backtesterflag})
    else:
            #update DB
        dbsession.query(Result).filter_by(resultid=dbobj.resultid,resulttime=dbobj.resulttime,
                                          resultname=dbobj.resultname).update(
                        {Result.origintime:dbobj.origintime,Result.resulttype:dbobj.resulttype,
                         Result.resultvalue:dbobj.resultvalue,Result.projid:dbobj.projid,
                         Result.symbolid:dbobj.symbolid,Result.causename:dbobj.causename,
                         Result.causeid:dbobj.causeid,Result.backtesterflag:dbobj.backtesterflag})

#Load Project
def LoadProject(project_list):
    for project in project_list:
        symbols = project.symbol
        projid = project.projid
        for lsymbol in symbols:
            symbolid = lsymbol.symbolid
            tablename = str(projid) + '_' + str(symbolid) + '_result'
            if engine.dialect.has_table(engine.connect(), tablename):
                resultnosql = Table(tablename, metadata, autoload=True, autoload_with=engine)
                tabledict[tablename] = resultnosql
                continue
    tabledict_string = cPickle.dumps(tabledict)
    views.cached_set("tabledict", tabledict_string)


def calcsymbol_phraseI(project, symbol,dbsession):
    #DataFrame fixing
    symbolid = symbol.symbolid
    projid=project.projid
    resultid = str(projid) + '_' + str(symbolid)
    symbolname = symbol.symbolname
    lsymbolname = symbolname.lower()
    tablename = lsymbolname + 'daily'
    rs= rediscache.tablecache(tablename)
    #rs_dict={
    #    'Date':[item.dateValue.strftime('%Y-%m-%d') for item in rs],'openTik':[item.openTik for item in rs],
    #    'highTik':[item.highTik for item in rs],'lowTik':[item.lowTik for item in rs],
    #    'closeTik':[item.closeTik for item in rs],'Volume':[item.totalVolume for item in rs]
    #}
    #rs_df=DataFrame(rs_dict,index=rs_dict['Date'],columns=rs_dict.keys())
    rs_sector_p=[]
    lcauses=project.cause
    leffectpercent=project.effectpercent
    lcausesname = []
    for lcause in lcauses:
        lcausesname.append(lcause.causename)
    if 'cause1' in lcausesname:
        pass
    if 'cause2' in lcausesname:
        pass
    if 'cause3' in lcausesname:
        pass

    if 'cause6' in lcausesname:
        symbolAbbvar = dict(symbolAbb=symbolname)
        sectornames = db.select('symbols', symbolAbbvar, where="symbolAbb=$symbolAbb", what="SectorName")
        sectorvar=dict(SectorName=sectornames[0].SectorName)
        sectorsymbols=db.select('symbols',sectorvar,where="Sectorname=$SectorName",what="symbolAbb")
        sectorsymbolnames=[]
        for symbol in sectorsymbols:
            sectorsymbolnames.append(symbol.symbolAbb)
        rs_sector=[]
        close_list=[]
        for sectorsymbolname in sectorsymbolnames:
            lsymbolname=sectorsymbolname.lower()
            lsymbolname=lsymbolname+'daily'
            rs_list=list(db.select(lsymbolname,order='dateValue DESC'))
            close_list=[float(result.closeTik) for result in rs_list]
            rs_sector.append(close_list)
        rs_sector_p=map(None,*rs_sector)

    if 'cause7' in lcausesname:
        #query spy volume
        spyvolumes=[]
        #spys=list(db.select('spydaily',order='dateValue DESC'))
        spys= rediscache.tablecache('spydaily')
        spyvolumes=[float(item.totalVolume) for item in spys]

    if 'cause13' in lcausesname:
        spycloses=[]
        spys=list(db.select('spydaily',order='dateValue DESC'))
        spycloses=[float(item.closeTik) for item in spys]
    lcalcdays=project.calcdays
    i = 0
    while (i < len(rs)):
        highpricelist = []
        highlist = []
        dateValue = rs[i]['dateValue']
        highrange = 0
        if i + lcalcdays + 1 > len(rs):
            highrange = len(rs)
        else:
            highrange = i + lcalcdays + 1

        if i-lcalcdays-1<0:
            startindex=0
        else:
            startindex=i-lcalcdays-1

        for item in rs[startindex:i]:
            highlist.append(round(float(item['highTik']), 2))

        for item in rs[i:]:
            highpricelist.append(round(float(item['highTik']), 2))

        lowpricelist = []
        for item in rs[i:]:
            lowpricelist.append(round(float(item['lowTik']), 2))

        closepricelist=[]
        for item in rs[i:]:
            closepricelist.append(round(float(item['closeTik']),2))
        if 'cause8' in lcausesname or 'cause9' in lcausesname:
            volumelist=[]
            for item in rs[i:]:
                volumelist.append(round(float(item['totalVolume']),2))
        #effect
        if highlist == []:
            maxhigh=rs[i]['closeTik']
        else:
            maxhigh=max(highlist)
        basicclose=float(rs[i]['closeTik'])

        if maxhigh > round(basicclose * (1+leffectpercent), 2):
            effectflag = True
        else:
            effectflag = False

        effect_resulttime = dateValue
        effect_origintime=effect_resulttime
        effectname = 'effect'
        effecttype = 'bool'
        effectvalue = str(effectflag)
        effectobj=ResultObj(resultid=resultid,resulttime=effect_resulttime,origintime=effect_origintime,resultname=effectname,
                resulttype=effecttype,resultvalue=effectvalue,projid=projid,symbolid=symbolid)
        inserobj(effectobj,dbsession)

        for lcause in lcauses:
            #cause1
            if lcause.causename=='cause1':
                highdays = 0
                for j in range(len(closepricelist[:-1])):
                    if closepricelist[j+1]>closepricelist[0]:
                        break
                    else:
                        continue
                resulttime = dateValue
                origintime=dateValue
                resultname = gcausedict[lcause.causename]
                resulttype = 'int'
                #resultvalue = str(highdays)
                resultvalue=copy.deepcopy(str(j))
                causename='cause1'
                #the result will store in the previous table if do asfollows
                resultobj=ResultObj(resultid=resultid,resulttime=resulttime,origintime=origintime,resultname=resultname,
                                 resulttype=resulttype,resultvalue=resultvalue,projid=projid,
                                 symbolid=symbolid,causename=causename)
                insertobj(resultobj,dbsession)
                #resultobj=resultobj.check_existing(resultname=resultname,resulttime=resulttime,resultid=resultid)
                #web.ctx.orm.add(resultobj)
                #resultobj.insertDB()
                #dbresultlist.append(resultobj)

            #cause2
            elif lcause.causename=='cause2':
                lowdays = 0
                for j in range(len(lowpricelist) - 1):
                    if lowpricelist[j] < lowpricelist[j + 1]:
                        lowdays = lowdays + 1
                    else:
                        break
                resulttime = dateValue
                origintime=resulttime
                resultname = gcausedict[lcause.causename]
                resulttype = 'int'
                resultvalue = str(lowdays)
                causename='cause2'
                resultobj=ResultObj(resultid=resultid,resulttime=resulttime,origintime=origintime,resultname=resultname,
                                 resulttype=resulttype,resultvalue=resultvalue,projid=projid,
                                 symbolid=symbolid,causename=causename)
                insertobj(resultobj,dbsession)
                #resultobj=resultobj.check_existing(resultname=resultname,resulttime=resulttime,resultid=resultid)
                #web.ctx.orm.add(resultobj)
                #dbresultlist.append(resultobj)
                #resultobj.insertDB()

            #cause3
            elif lcause.causename=='cause3':
                lcause3 = rs[i].totalVolume
                resulttime = dateValue
                origintime=resulttime
                resultname = gcausedict[lcause.causename]
                resulttype = 'int'
                resultvalue = str(rs[i]['totalVolume'])
                causename='cause3'
                resultobj=ResultObj(resultid=resultid,resulttime=resulttime,origintime=origintime,resultname=resultname,
                resulttype=resulttype,resultvalue=resultvalue,projid=projid,symbolid=symbolid,causename=causename)
                insertobj(resultobj,dbsession)
                #resultobj=resultobj.check_existing(resultname=resultname,resulttime=resulttime,resultid=resultid)
                #web.ctx.orm.add(resultobj)
                #dbresultlist.append(resultobj)
                #resultobj.insertDB()
            #cause4
            elif lcause.causename=='cause4':
                lcausevalue=json.loads(lcause.causevalue)
                xdays1list=lcausevalue['cause4']
                for item in xdays1list:
                    xdays1=int(item)
                    startidx=1
                    endidx=xdays1+1
                    if len(highpricelist)>1:
                        if endidx > len(highpricelist):
                            endidx=len(highpricelist)
                        lcause4 = round(((closepricelist[0] - max(highpricelist[startidx:endidx])) / highpricelist[0]) * 100, 2)
                    else:
                        lcause4=None
                    resulttime = dateValue
                    origintime=resulttime
                    resultname = item+" "+gcausedict[lcause.causename]
                    resulttype = 'float'
                    resultvalue = str(lcause4)
                    causename='cause4'
                    resultobj=ResultObj(resultid=resultid,resulttime=resulttime,origintime=origintime,resultname=resultname,
                    resulttype=resulttype,resultvalue=resultvalue,projid=projid,symbolid=symbolid,causename=causename)
                    insertobj(resultobj,dbsession)
                    #resultobj=resultobj.check_existing(resultname=resultname,resulttime=resulttime,resultid=resultid)
                    #web.ctx.orm.add(resultobj)
                    #dbresultlist.append(resultobj)
                    #resultobj.insertDB()

            #cause5
            elif lcause.causename=='cause5':
                lcausevalue=json.loads(lcause.causevalue)
                xdays2list=lcausevalue['cause5']
                for item in xdays2list:
                    xdays2=int(item)
                    startidx=1
                    endidx=xdays2+1
                    if len(lowpricelist)>1:
                        if endidx >len(lowpricelist):
                            endidx=len(lowpricelist)
                        lcause5 = round(((closepricelist[0] - min(lowpricelist[startidx: endidx])) / lowpricelist[0]) * 100, 2)
                    else:
                        lcause5=None
                    #return
                    resulttime = dateValue
                    origintime=resulttime
                    resultname = item+" "+gcausedict[lcause.causename]
                    resulttype = 'float'
                    resultvalue = str(lcause5)
                    causename='cause5'
                    resultobj=ResultObj(resultid=resultid,resulttime=resulttime,origintime=origintime,resultname=resultname,
                    resulttype=resulttype,resultvalue=resultvalue,projid=projid,symbolid=symbolid,causename=causename)
                    insertobj(resultobj,dbsession)
                    #resultobj=resultobj.check_existing(resultname=resultname,resulttime=resulttime,resultid=resultid)
                    #web.ctx.orm.add(resultobj)
                    #dbresultlist.append(resultobj)
                    #resultobj.insertDB()

            #cause6
            elif lcause.causename == 'cause6' :
                sum=0
                sec_length=0
                if len(rs_sector)==1:
                   avg=float(rs[i].closeTik)
                else:
                    for item in rs_sector_p[i]:
                        if item == None:
                            continue
                        else:
                            sum=sum+item
                            sec_length+=1
                    avg=sum/sec_length
                lcause6=round(float(rs[i].closeTik)/avg,2)
                resulttime=dateValue
                origintime=resulttime
                resultname=gcausedict[lcause.causename]
                resulttype='float'
                resultvalue=str(lcause6)
                causename='cause6'
                resultobj=ResultObj(resultid=resultid,resulttime=resulttime,origintime=origintime,resultname=resultname,
                resulttype=resulttype,resultvalue=resultvalue,projid=projid,symbolid=symbolid,causename=causename)
                insertobj(resultobj,dbsession)
                #resultobj=resultobj.check_existing(resultname=resultname,resulttime=resulttime,resultid=resultid)
                #web.ctx.orm.add(resultobj)
                #dbresultlist.append(resultobj)
                #resultobj.insertDB()

            #cause7
            elif lcause.causename=='cause7':
                spyvolume=0
                volume=0
                if i>=len(spyvolumes):
                    lcause7=None
                else:
                    lcause7=round(float(rs[i].totalVolume)/spyvolumes[i],2)
                resulttime = dateValue
                origintime=resulttime
                resultname = gcausedict[lcause.causename]
                resulttype = 'float'
                resultvalue = str(lcause7)
                causename='cause7'
                resultobj=ResultObj(resultid=resultid,resulttime=resulttime,origintime=origintime,resultname=resultname,
                resulttype=resulttype,resultvalue=resultvalue,projid=projid,symbolid=symbolid,causename=causename)
                insertobj(resultobj,dbsession)
                #resultobj=resultobj.check_existing(resultname=resultname,resulttime=resulttime,resultid=resultid)
                #web.ctx.orm.add(resultobj)
                #dbresultlist.append(resultobj)
                #resultobj.insertDB()

            #cause8
            elif lcause.causename=='cause8':
                lcausevalue=json.loads(lcause.causevalue)
                xdays3list=lcausevalue['cause8']
                for item in xdays3list:
                    xdays3=int(item)
                    startidx=1
                    endidx=xdays3+1
                    if len(highpricelist)>1:
                        if endidx > len(highpricelist):
                            endidx=len(highpricelist)
                        else:
                            pass
                        lcause8 = round(((volumelist[0] - max(highpricelist[startidx:endidx])) / highpricelist[0]) * 100, 2)
                    else:
                        lcause8=None
                    resulttime = dateValue
                    origintime=resulttime
                    resultname = item+" "+gcausedict[lcause.causename]
                    resulttype = 'float'
                    resultvalue = str(lcause8)
                    causename='cause8'
                    resultobj=ResultObj(resultid=resultid,resulttime=resulttime,origintime=origintime,resultname=resultname,
                    resulttype=resulttype,resultvalue=resultvalue,projid=projid,symbolid=symbolid,causename=causename)
                    insertobj(resultobj,dbsession)
                    #resultobj=resultobj.check_existing(resultname=resultname,resulttime=resulttime,resultid=resultid)
                    #web.ctx.orm.add(resultobj)
                    #dbresultlist.append(resultobj)
                    #resultobj.insertDB()
            #cause9
            elif lcause.causename=='cause9':
                lcausevalue=json.loads(lcause.causevalue)
                xdays4list=lcausevalue['cause9']
                for item in xdays4list:
                    xdays4=int(item)
                    startidx=1
                    endidx=xdays4+1
                    if len(lowpricelist)>1:
                        if endidx >len(lowpricelist):
                            endidx=len(lowpricelist)
                        lcause9 = round(((volumelist[0] - min(lowpricelist[startidx: endidx])) / lowpricelist[0]) * 100, 2)
                    else:
                        lcause9=None
                    #return
                    resulttime = dateValue
                    origintime=resulttime
                    resultname = item+" "+gcausedict[lcause.causename]
                    resulttype = 'float'
                    resultvalue = str(lcause9)
                    causename='cause9'
                    resultobj=ResultObj(resultid=resultid,resulttime=resulttime,origintime=origintime,resultname=resultname,
                    resulttype=resulttype,resultvalue=resultvalue,projid=projid,symbolid=symbolid,causename=causename)
                    insertobj(resultobj,dbsession)
                    #resultobj=resultobj.check_existing(resultname=resultname,resulttime=resulttime,resultid=resultid)
                    #web.ctx.orm.add(resultobj)
                    #dbresultlist.append(resultobj)
                    #resultobj.insertDB()
            #cause10
            elif lcause.causename=='cause10':
                print 'cause10'
                pass

            #cause11
            elif lcause.causename=='cause11':
                print 'cause11'
            #Stochastic
                pass
            #cause12
            elif lcause.causename=='cause12':
                pass
            elif lcause.causename=='cause13':
            #
                if i>=len(spycloses):
                #lcause12=None
                    lcause12=0.0
                else:
                    lcause12=round(float(rs[i]['closeTik'])/spycloses[i],2)
                resulttime = dateValue
                origintime=resulttime
                resultname = gcausedict[lcause.causename]
                resulttype = 'float'
                resultvalue = str(lcause12)
                causename='cause12'
                resultobj=ResultObj(resultid=resultid,resulttime=resulttime,origintime=origintime,resultname=resultname,
                resulttype=resulttype,resultvalue=resultvalue,projid=projid,symbolid=symbolid,causename=causename)
                insertobj(resultobj,dbsession)
                #resultobj=resultobj.check_existing(resultname=resultname,resulttime=resulttime,resultid=resultid)
                #web.ctx.orm.add(resultobj)
                #dbresultlist.append(resultobj)
                #resultobj.insertDB()

            #cause14
            elif lcause.causename=='cause14':
                pass

            #cause14
            elif lcause.causename=='cause15':
                pass

            #cause15
            elif lcause.causename=='cause16':
                pass

            #cause16
            elif lcause.causename=='cause17':
                pass
            #cause17
            elif lcause.causename=='cause18':
                pass
        i = i + 1
    #web.ctx.orm.execute(Result.__table__.insert(),
    #                    [{'resultid':item.resultid,'resulttime':item.resulttime,'origintime':item.origintime,
    #                      'resultname':item.resultname,'resulttype':item.resulttype,
    #                      'resultvalue':item.resultvalue,'projid':item.projid,
    #                      'symbolid':item.symbolid,'causename':item.causename,
    #                      'causeid':item.causeid,'backtesterflag':item.backtesterflag}
    #                     for item in dbresultlist if item.check_not_existing()])
    #web.ctx.orm.add_all(dbresultlist)

    dbsession.commit()


def calc_causeresult(lcauseresult,effectlist,cause,calcdays,backcount,segcount,minicc,projid,symbolid):
    lcauselist=[process(result['resultvalue']) for result in lcauseresult]
    resultid = str(projid) + '_' + str(symbolid)
    ccrangelist=[]
    if lcauselist:
        templist=[item for item in lcauselist if item is not None]
        maxcause=max(templist)
        mincause=min(templist)
        if mincause is None:
            mincause=0
        causeunit=round((maxcause-mincause)/segcount,3)
        #if type(lcauselist[0]) is float:
        #    causeunit=round((maxcause-mincause)/(segcount),3)
        #elif type(lcauselist[0]) is int:
        #    causeunit = (maxcause - mincause) / segcount
        #make a range list
        for idx in range(segcount):
            ccrangelist.append(mincause+idx*causeunit)
    i=0
    db_list=[]
    for result in lcauseresult:
        dateValue=result['resulttime']
        startdays=calcdays+i-1
        enddays=startdays+backcount
        if result['resulttype'] == 'int':
            innerresult=int(result['resultvalue'])
        if result['resulttype'] == 'float':
            innerresult=process(result['resultvalue'])
        cc=0
        effectcount=0
        if startdays>len(lcauselist):
            startdays=-1
        if enddays>len(lcauselist):
            enddays=-1
        effectindex=startdays
        innercount=0
        #assure the innerresult range
        j=0
        startccidx=0
        endccidx=0
        for item in ccrangelist:
            if innerresult is None:
                break
            if item<=innerresult and (0<=innerresult-item<causeunit):
                startccidx=j
            elif item>=innerresult and (0<=item-innerresult<causeunit):
                endccidx=j
            j+=1

        for lresult in lcauselist[startdays:enddays]:
            if lresult is None or lcauselist[i] is None:
                effectindex=effectindex+1
                continue
            #if abs(lresult-lcauselist[i])<=causeunit:
            #compare the innerresult and lresult whether in the same range
            if ccrangelist[startccidx]<lresult<ccrangelist[endccidx]:
                cc=cc+1
                if effectlist[effectindex]:
                    innercount=innercount+1
            effectindex=effectindex+1
        #if str(dateValue).startswith('2013-01-31'):
        #    logger.debug("2013-01-31")
        #    logger.debug(lcauselist[startdays])
        #    logger.debug(lcauselist[enddays-1])
        #    logger.debug(len(lcauselist[startdays:enddays]))
        #    logger.debug(lcauselist[startdays:enddays])
        #    logger.debug(causeunit)
        #    logger.debug(cc)
        #    logger.debug(lcauselist[i])
        #    logger.debug("End 2013-01-31")

        resulttime=dateValue
        origintime=resulttime
        resultname='cc for '+result['resultname']
        resulttype='int'
        resultvalue=str(cc)
        causename=cause.causename
        causeid=cause.causeid
        backtesterflag=False
        resultobj=ResultObj(resultid=resultid,resulttime=resulttime,origintime=origintime,resultname=resultname,
        resulttype=resulttype,resultvalue=resultvalue,projid=projid,symbolid=symbolid,causename=causename,causeid=causeid)
        insertobj(resultobj,dbsession)
        #resultobj=resultobj.check_existing(resultname=resultname,resulttime=resulttime,resultid=resultid)
        #resultobj.insertDB()
        #db_list.append(resultobj)
        #web.ctx.orm.add(resultobj)

        if cc<minicc or enddays==-1 or cc==0:
            cp=None
            ncp=None
        else:
            cp=round((float(innercount)/cc)*100,2)
            ncp=100-cp
        resulttime = dateValue
        resultname = 'cp for '+result['resultname']
        resulttype = 'float'
        resultvalue=str(cp)
        #resultvalue = json.dumps(cp)
        causename=cause.causename
        causeid=cause.causeid
        backtesterflag=True
        resultobj=ResultObj(resultid=resultid,resulttime=resulttime,origintime=origintime,resultname=resultname,
        resulttype=resulttype,resultvalue=resultvalue,projid=projid,symbolid=symbolid,causename=causename,causeid=causeid)
        insertobj(resultobj,dbsession)
        #resultobj=resultobj.check_existing(resultname=resultname,resulttime=resulttime,resultid=resultid)
        #db_list.append(resultobj)
        #web.ctx.orm.add(resultobj)
        #resultobj.insertDB()

        resultname='ncp for '+result['resultname']
        resulttype='float'
        resultvalue=str(ncp)
        #resultvalue=json.dumps(ncp)
        causename=cause.causename
        causeid=cause.causeid
        resultobj=ResultObj(resultid=resultid,resulttime=resulttime,origintime=origintime,resultname=resultname,
        resulttype=resulttype,resultvalue=resultvalue,projid=projid,symbolid=symbolid,causename=causename,causeid=causeid)
        insertobj(resultobj,dbsession)
        #resultobj=resultobj.check_existing(resultname=resultname,resulttime=resulttime,resultid=resultid)
        #db_list.append(resultobj)
        #web.ctx.orm.add(resultobj)
        #resultobj.insertDB()
        i=i+1
    #return db_list

def calcsymbol_phraseII(symbol, segcount, lcalcdays, backcount, minicc,  lcauses,dbsession):
    symbolid = symbol.symbolid
    projid = symbol.projid
    resultid = str(projid) + '_' + str(symbolid)
    allresult=[]
    #allresult=list(web.ctx.orm.query(Result).filter_by(resultid=resultid).all())
    allresult= rediscache.resultcache(resultid)
    effectresult = [result for result in allresult if result['resultname'] == 'effect']
    effectlist = [processeffect(result['resultvalue']) for result in effectresult]
    # return
    for cause in lcauses:
        if cause.causename in ['cause4','cause5','cause8','cause9']:
            causevalue=json.loads(cause.causevalue)
            xdayslist=causevalue[cause.causename]
            for xdays in xdayslist:
                resultname=xdays+' '+gcausedict[cause.causename]
                lcauseresult=[result for result in allresult if result['causename']==cause.causename and result['resultname']==resultname]
                calc_causeresult(lcauseresult,effectlist,cause,lcalcdays,backcount,segcount,minicc,projid,symbolid)
        else:
            lcauseresult=[result for result in allresult if result['causename']==cause.causename]
            calc_causeresult(lcauseresult,effectlist,cause,lcalcdays,backcount,segcount,minicc,projid,symbolid)
    dbsession.commit()

def calcsymbol(project,symbol):
    #caculating
    #symbol=web.ctx.orm.query(Symbol).filter_by(symbolid=symbolid).first()
    #project=symbol.project
    dbsession=getsession()
    projid = project.projid
    lcalcdays = project.calcdays
    leffectpercent = project.effectpercent
    lcauses = project.cause
    symbolid = symbol.symbolid
    status=symbol.status
    if status == 1:#runing or completed
        return symbolid
    tradedb.update('symbol',where="symbolid =$symbolid",vars={'symbolid':symbolid}, status = 0)
    calcsymbol_phraseI(project,symbol,dbsession)
    dbsession.commit()
    logger.debug("cause caculation is completed")
    #step2
    lcalcdays = project.calcdays
    backcount = project.backcount
    segcount = project.segcount
    minicc = project.minicc
    symbols = project.symbol
    projid = project.projid
    calcsymbol_phraseII(symbol, segcount, lcalcdays, backcount, minicc, lcauses,session)
    dbsession.commit()
    logger.debug("cc and cp caculation completed")

