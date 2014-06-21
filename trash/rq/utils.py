import requests

def count_words_at_url(url):
    resp=requests.get(url)
    print 'haha'
    return len(resp.text.split())