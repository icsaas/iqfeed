import simplejson as json
import datetime
from simplejson import JSONDecoder
import MySQLdb

from Model.trademodel import create_kvdb
from Model.trademodel import tradedb


class DateTimeDecoder(JSONDecoder):
    def __init__(self,*args,**kwargs):
        JSONDecoder.__init__(self,object_hook=self.dict_to_object,*args,**kwargs)
    def dict_to_object(self,d):
        if '__type__' not in d:
            return d
        type=d.pop('__type__')
        try:
            dateobj=datetime.datetime(**d)
            return dateobj
        except:
            d['__type__']=type
            return d
class DateTimeEncoder(json.JSONEncoder):
    def default(self,obj):
        if isinstance(obj,datetime.datetime):
            return {
                '__type__':'datetime',
                'year':obj.year,
                'month':obj.month,
                'day':obj.day,
                'hour':obj.hour,
                'minute':obj.minute,
                'second':obj.second,
            }
        else:
            return json.JSONEncoder.default(self,obj)

kvmem=create_kvdb()
def clearcache(kvmem):
    kvmem.flushdb()
def savecache(kvmem):
    kvmem.save()

def cached_set(key,value):
    kvmem.set(key,value)
    #kvmem.expire(key,2*60)

def cached_get(key):
    result=kvmem.get(key)
    if result is not None:
        kvmem.expire(key,5*60)
    return result

from trash.rq.redislru import add_item,get_item

def projectcache(projid):
    queue_name=str(projid)
    try:
        conn=MySQLdb.connect(host='localhost',user='david',passwd='david',db='david_hlocvdb')
        cur=conn.cursor()
        expression="select * from project where projid="+queue_name+";"
        cur.execute(expression)
        conn.commit()
        #rs=cur.fetchall()
        #cols=[d[0] for d in cur.description]
        result=[]
        columns=tuple([d[0].decode('utf8') for d in cur.description])
        for row in cur:
            result.append(dict(zip(columns,row)))
        tablename="projtable_"+queue_name
        add_item(tablename,json.dumps(result,cls=DateTimeEncoder))
        cur.close()
        cur=conn.cursor()
        columns=None
        expression='select * from symbol where projid='+queue_name+';'
        cur.execute(expression)
        conn.commit()
        result=[]
        columns=tuple([d[0].decode('utf8') for d in cur.description])
        for row in cur:
            result.append(dict(zip(columns,row)))
        conn.close()
        tablename="symboltable_"+queue_name
        #cached_set(tablename,json.dumps(result,cls=DateTimeEncoder))
        add_item(tablename,json.dumps(result,cls=DateTimeEncoder))
    except MySQLdb.Error,e:
        print "Mysql Error %d:%s" %(e.args[0],e.args[1])

def symbolcache(projid):
    pass

def tablecache(tablename,where=None,what=None):
    #dailydata=cached_get(tablename)
    dailydata=get_item(tablename)
    rs=[]
    if dailydata is None:
        try:
            conn=MySQLdb.connect(host='localhost',user='david',passwd='david',db='david_hlocvdb')
            cur=conn.cursor()
            expression="select * from "+tablename+";"
            print expression
            print 'well1'
            cur.execute(expression)
            conn.commit()
            #rs=cur.fetchall()
            #cols=[d[0] for d in cur.description]
            result=[]
            columns=tuple([d[0].decode('utf8') for d in cur.description])
            for row in cur:
                result.append(dict(zip(columns,row)))
            #print result
            #print len(result)
#            rs = list(db.select(tablename, order='dateValue DESC'))
            #print rs
            cur.close()
            conn.close()
            #cached_set(tablename,json.dumps(result,cls=DateTimeEncoder))
            add_item(tablename,json.dumps(result,cls=DateTimeEncoder))
        except MySQLdb.Error,e:
            print "Mysql Error %d:%s" %(e.args[0],e.args[1])

        #get the data from database and save it into the redis and return
    else:
        #covert serialized the dailydata
        result=json.loads(dailydata,cls=DateTimeDecoder)
    return result

#not good to add cache,maybe not easy
def sector(symbolname):
    try:
        conn=MySQLdb.connect(host='localhost',user='david',passwd='david',db='david_hlocvdb')
        cur=conn.cursor()
        expression="select SectorName from symbols where symbolAbb=''"+symbolname+"';"
        cur.execute(expression)

        sectorname=cur.fetchone()[0]
        expression="select symbolAbb from symbols where Sectorname=''"+sectorname+"';"
        cur.execute(expression)
        result=cur.fetchall()
        sectorsymbols=[]
        for item in result:
            sectorsymbols.append(item[0])
        cur.close()
        conn.close()
        return sectorsymbols
    except MySQLdb.Error,e:
        print "Mysql Error %d:%s" %(e.args[0],e.args[1])


def resultcache(resultid):
    #allresult=cached_get(resultid)
    allresult=get_item(resultid)
    myvar = dict(resultid=resultid)
    rs=[]
    if allresult is None:
        rs=list(tradedb.select('result',myvar,where="resultid=$resultid"))
        #cached_set(resultid,json.dumps(rs,cls=DateTimeEncoder))
        add_item(resultid,json.dumps(rs,cls=DateTimeEncoder))
    else:
        rs=json.loads(allresult,cls=DateTimeDecoder)
    return rs

def rtsrcache(rtsrkey):
    #rawrtsr=cached_get(rtsrkey)
    rawrtsr=get_item(rtsrkey)
    rs=None
    symbolid=int(rtsrkey[:-4])
    myvar=dict(symbolid=symbolid)
    if rawrtsr is None:
        rs=tradedb.select('rtsr',myvar,where='symbolid=$symbolid')[0].value
        #cached_set(rtsrkey,rs)
        add_item(rtsrkey,rs)
    else:
        rs=rawrtsr
    return rs

def DBstatus(projid):
    proj=web.ctx.orm.query(Project).filter_by(projid=projid).first()
    status=proj.status
    btstatus=proj.btstatus
    proj_status={}
    proj_status['projstatus']=status
    proj_status['btstatus']=btstatus
    statuslist=[]
    symbols=proj.symbol
    newsymbol_status={}
    btsymbol_status={}
    for symbol in symbols:
        newsymbol_status[symbol.symbolid]=symbol.status
        btsymbol_status[symbol.symbolid]=symbol.btstatus
    statuslist.append(proj_status)
    statuslist.append(newsymbol_status)
    statuslist.append(btsymbol_status)
    json_status=json.dumps(statuslist)
    return json_status

def statuscahce(statuskey):
    #rawstatus=cached_get(statuskey)
    rawstatus=get_item(statuskey)
    rs=None
if __name__=='__main__':
    #kvmem=create_kvdb()
    clearcache(kvmem)
    pass




