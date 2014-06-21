from rq import Queue
from trash.rq.worker import conn
#use_connection(conn)
q=Queue(connection=conn)

from trash.rq.utils import count_words_at_url
result=q.enqueue(count_words_at_url,'http://justpic.org')
print 'main'
print result