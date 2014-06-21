import json

from trash.rq import rediscache
import web
from Model.trademodel import Project, Result,Backtester,Predict, tradedb
from tools import *
from Config.causeconfig import gcausedict,gtcp_list
from tool.logger import initlog

logger=initlog(__name__)

import numpy as np
from pandas import DataFrame,Series
import umysqldb
umysqldb.install_as_MySQLdb()

#metadataflect
def backtester(project, symbol, causesin):
    #each symbol each time
    if symbol.btstatus == 1:
        return symbol.symbolid
    if symbol.btstatus==0:
        print "the first phrase is not completed"
        return None
    coefficient=project.coefficient
    ncoefficient=project.ncoefficient
    projid = project.projid
    db_list=[]
    web.ctx.orm.execute(symbol.__table__.update().where(symbol.__table__.c.symbolid==symbol.symbolid).values(btstatus=0))
    web.ctx.orm.commit()
    web.ctx.orm.flush()
    symbolid = symbol.symbolid
    resultid=str(projid) + '_' + str(symbolid)
    allresult= rediscache.resultcache(resultid)
    #allresult=list(web.ctx.orm.query(Result).filter_by(resultid=resultid).all())
    if allresult is []:
        return
    effectresult = [result for result in allresult if result['resultname'] == 'effect']
    effectlist = [processeffect(result['resultvalue']) for result in effectresult]
    RTSRcount = 0
    if effectlist == []:
        return
    for effect in effectlist:
        if effect:
            RTSRcount = RTSRcount + 1
    RTSR=round(float(RTSRcount)/len(effectlist),3)
    tradedb.insert('rtsr',symbolid=symbolid,value=RTSR)
    rtsrkey=str(symbolid)+'rtsr'
    rediscache.cached_set(rtsrkey,RTSR)
    datevalue=allresult[0]['origintime']
    for cause in causesin:
        for tcpstep in gtcp_list:
            if cause.causename in ['cause4','cause5','cause8','cause9']:
                causevalue=json.loads(cause.causevalue)
                xdayslist=causevalue[cause.causename]
                for xdays in xdayslist:
                    resultname='cp for '+xdays+' '+gcausedict[cause.causename]
                    cplist=[result for result in allresult if result['resultname']==resultname]
                    temp=calc_cplist(cplist,symbol,cause,datevalue,tcpstep,RTSR,effectlist,resultname)
                    db_list.append(temp)
                    resultname2='ncp for '+xdays+' '+gcausedict[cause.causename]
                    ncplist=[result for result in allresult if result['resultname']==resultname2]
                    temp=calc_ncplist(ncplist,symbol,cause,datevalue,tcpstep,RTSR,effectlist,resultname2)
                    db_list.append(temp)
            else:
                resultname='cp for '+gcausedict[cause.causename]
                cplist = [result for result in allresult if result['resultname'] == resultname]
                temp=calc_cplist(cplist,symbol,cause,datevalue,tcpstep,RTSR,effectlist,resultname)
                db_list.append(temp)
                resultname2='ncp for '+gcausedict[cause.causename]
                ncplist=[result for result in allresult if result['resultname']==resultname2]
                temp=calc_ncplist(ncplist,symbol,cause,datevalue,tcpstep,RTSR,effectlist,resultname2)
                db_list.append(temp)
    web.ctx.orm.add_all(db_list)
    web.ctx.orm.execute(symbol.__table__.update().where(symbol.__table__.c.symbolid == symbol.symbolid).values(btstatus=1))
    web.ctx.orm.commit()
    web.ctx.orm.flush()


def calc_cplist(cplist,symbol,cause,datevalue,tcpstep,RTSR,effectlist,resultname):
    number = 0
    SR = 0
    i = 0
    for cp in cplist:
        if process(cp['resultvalue']) is None:
            i = i + 1
            continue
        if tcpstep < process(cp['resultvalue']):
            number = number + 1
            if effectlist[i]:
                SR = SR + 1
        i = i + 1
    if number == 0:
        srvalue = 0.0
    else:
        srvalue = round(float(SR) / number, 3)*100
    rawvalue = dict(SR=srvalue, N=number)
    #SR and number should be regarded as a whole
    #advance represent the predictive flag
    backtestername = 'SR'
    backtestervalue = json.dumps(rawvalue)
    resulttype = 'int'
    tcpvalue = json.dumps(tcpstep)
    step = 'step'
    causeid = cause.causeid
    symbolid = symbol.symbolid
    symbolname = symbol.symbolname
    backtester = Backtester(datevalue=datevalue, backtestername=backtestername, backtestervalue=backtestervalue,
            tcpvalue=tcpvalue, step=step, resultname=resultname, causeid=causeid,symbolid=symbolid, symbolname=symbolname)
    backtester = backtester.check_existing(tcpvalue=tcpvalue,symbolid=symbolid,causeid=causeid,step=step,resultname=resultname)
    return backtester
def calc_ncplist(ncplist,symbol,cause,datevalue,tcpstep,RTSR,effectlist,resultname):
    number = 0
    SR = 0
    i = 0
    for ncp in ncplist:
        if process(ncp['resultvalue']) is None:
            i = i + 1
            continue
        if tcpstep < process(ncp['resultvalue']):
            number = number + 1
            if effectlist[i]:
                SR = SR + 1
        i = i + 1
    if number == 0:
        srvalue = 0.0
    else:
        srvalue = round(float(SR) / number, 3)*100
    srvalue=100-srvalue

    rawvalue = dict(SR=srvalue, N=number)
    #SR and number should be regarded as a whole
    backtestername = 'SR'
    backtestervalue = json.dumps(rawvalue)
    resulttype = 'int'
    tcpvalue = json.dumps(tcpstep)
    step = 'step'
    causeid = cause.causeid
    symbolid = symbol.symbolid
    symbolname = symbol.symbolname
    backtester = Backtester(datevalue=datevalue, backtestername=backtestername, backtestervalue=backtestervalue,
                            tcpvalue=tcpvalue, step=step, resultname=resultname, causeid=causeid,symbolid=symbolid, symbolname=symbolname)
    backtester = backtester.check_existing(tcpvalue=tcpvalue,symbolid=symbolid,causeid=causeid,step=step,resultname=resultname)
    return backtester

def summarycalc(projid,date=None,state=0):
    proj=web.ctx.orm.query(Project).filter_by(projid=projid).first()
    if proj is None:
        return None
    symbolsin=proj.symbol
    causesin = proj.cause
    summary_dict={}
    for symbol in symbolsin:
        symbolid=symbol.symbolid
        resultid=str(projid)+'_'+str(symbolid)
        allresult=[]
        totalresult=list(web.ctx.orm.query(Result).filter_by(resultid=resultid).all())
        if totalresult==[]:
            return None
        if state ==0:
            date=totalresult[0].origintime.strftime('%Y-%m-%d')
            #datestr=totalresult[0].origintime.strftime('%Y-%m-%d')
            #date=time.strptime(datestr,'%Y-%m-%d')
            #date=datetime.datetime(*totalresult[0].origintime[:6])
        #allresult=[item for item in totalresult if func.date_format(item.origintime,'%Y-%m-%d')==date]
        allresult=[item for item in totalresult if item.origintime.strftime('%Y-%m-%d')==date]
        if allresult == []:
            return None
        symbolresultdict={}
        cppredict_dict={}
        ncppredict_dict={}
        for cause in causesin:
            causeid=cause.causeid
            if cause.causename in ['cause4','cause5','cause8','cause9']:
                lcausevalue=json.loads(cause.causevalue)
                xdayslist=lcausevalue[cause.causename]
                for xday in xdayslist:
                    cpname='cp for '+xday+' '+gcausedict[cause.causename]
                    ncpname='ncp for '+xday+' '+gcausedict[cause.causename]
                    predicter_cp=web.ctx.orm.query(Predict).filter_by(causeid=causeid,resultname=cpname).first()
                    predicter_ncp=web.ctx.orm.query(Predict).filter_by(causeid=causeid,resultname=ncpname).first()
                    cppredict_dict[cpname]=predicter_cp.coefficient
                    ncppredict_dict[ncpname]=predicter_ncp.coefficient

            else:
                cpname='cp for '+gcausedict[cause.causename]
                ncpname='ncp for '+gcausedict[cause.causename]
                predicter_cp=web.ctx.orm.query(Predict).filter_by(causeid=causeid,resultname=cpname).first()
                predicter_ncp=web.ctx.orm.query(Predict).filter_by(causeid=causeid,resultname=ncpname).first()
                cppredict_dict[cpname]=predicter_cp.coefficient
                ncppredict_dict[ncpname]=predicter_ncp.coefficient
        cppredict_ser=Series(cppredict_dict,index=cppredict_dict.keys())
        ncppredict_ser=Series(ncppredict_dict,index=ncppredict_dict.keys())
        cppredict_ser.sort()
        ncppredict_ser.sort()
        if len(cppredict_ser)<3:
            realcp_ser=cppredict_ser
        else:
            realcp_ser=cppredict_ser[-3:]
        if len(ncppredict_ser)<3:
            realncp_ser=ncppredict_ser
        else:
            realncp_ser=ncppredict_ser[-3:]
        symbol_summary_dict={}
        for idx in realcp_ser.index:
            symbol_summary_dict[idx]=[process(item.resultvalue) for item in allresult if item.resultname==idx][0]
        for idx in realncp_ser.index:
            symbol_summary_dict[idx]=[process(item.resultvalue) for item in allresult if item.resultname==idx][0]
        summary_dict[symbol]=symbol_summary_dict
    summary_df=DataFrame(summary_dict)
    return summary_df.T

def correlation(project, symbolsin, causesin):
    projid=project.projid
    ratertsr=project.ratertsr
    coefficient=project.coefficient
    ncoefficient=project.ncoefficient
    for symbol in symbolsin:
        symbolid=symbol.symbolid
        rtsrkey=str(symbolid)+'rtsr'
        RTSR=float(rediscache.rtsrcache(rtsrkey))
        for cause in causesin:
            causeid=cause.causeid
            if cause.causename in ['cause4','cause5','cause8','cause9']:
                causevalue=json.loads(cause.causevalue)
                xdayslist=causevalue[cause.causename]
                for xdays in xdayslist:
                    resultname='cp for '+xdays+' '+gcausedict[cause.causename]
                    resultname2='ncp for '+xdays+' '+gcausedict[cause.causename]
            else:
                resultname='cp for '+gcausedict[cause.causename]
                resultname2='ncp for '+gcausedict[cause.causename]
            cp_backtesters=web.ctx.orm.query(Backtester).filter_by(causeid=causeid,resultname=resultname).all()
            ncp_backtesters=web.ctx.orm.query(Backtester).filter_by(causeid=causeid,resultname=resultname2).all()
            sr_dict={json.loads(item.tcpvalue):json.loads(item.backtestervalue)['SR'] for item in cp_backtesters}
            nsr_dict={json.loads(item.tcpvalue):json.loads(item.backtestervalue)['SR'] for item in ncp_backtesters}
            sr_list=[sr_dict[item] for item in sr_dict]
            nsr_list=[nsr_dict[item] for item in nsr_dict]
            tcp_list=[float(item) for item in sr_dict.keys()]
            sr_series=Series(sr_list)
            nsr_series=Series(nsr_list)
            tcp_series=Series(tcp_list)
            sr_corr=sr_series.corr(tcp_series)
            nsr_corr=nsr_series.corr(tcp_series)
            #compare sr_corr and coefficient
            if np.isnan(sr_corr)==False and sr_corr>coefficient and sr_series.min>(RTSR+ratertsr):
                sr_predictive=True
            else:
                sr_predictive=False
            #compare nsr_corr and coefficient
            if np.isnan(nsr_corr)==False and nsr_corr>ncoefficient and nsr_series.min>(RTSR+ratertsr):
                nsr_predictive=True
            else:
                nsr_predictive=False
            predict=Predict(symbolid=symbolid,causeid=causeid,coefficient=json.dumps(sr_corr),Predictive=sr_predictive,resultname=resultname)
            predict=predict.check_existing(symbolid=symbolid,causeid=causeid,resultname=resultname)
            web.ctx.orm.add(predict)
            predict2=Predict(symbolid=symbolid,causeid=causeid,coefficient=json.dumps(nsr_corr),Predictive=nsr_predictive,resultname=resultname2)
            predict2=predict2.check_existing(symbolid=symbolid,causeid=causeid,resultname=resultname2)
            web.ctx.orm.add(predict2)
    web.ctx.orm.commit()
    web.ctx.orm.flush()







