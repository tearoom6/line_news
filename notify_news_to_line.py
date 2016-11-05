# -*- coding: utf-8 -*-
import sys
sys.path.append('./libs')

import base64
import boto3
from dateutil.parser import parse
from datetime import datetime, timedelta
import pytz
import requests
from bs4 import BeautifulSoup
import feedparser
import urllib
import urllib2

YAHOO_JAPAN_HEADLINE_RSS_URL = 'http://headlines.yahoo.co.jp/rss/list'
LINE_NOTIFY_POST_URL = 'https://notify-api.line.me/api/notify'
LINE_NOTIFY_BEARER_TOKEN = 'AQECAHgsX4pnmWlePDkEVSEwrUqHDwYd6B3NEs0GqBGZ/ilgRgAAAIowgYcGCSqGSIb3DQEHBqB6MHgCAQAwcwYJKoZIhvcNAQcBMB4GCWCGSAFlAwQBLjARBAx5CiMZTCnF+S3wxtYCARCARqjdJK983WIScJtuUqAPJM1yxcCLV9Wqaz1H51e9ymCPj3DfJl0XE8t65Z2K3EDTT805Fh4v7pbguMXKTiXBMrXLcXYUyMQ='

def decript_by_kms(ciphertext):
  kms = boto3.client('kms')
  ciphertext_blob = base64.b64decode(ciphertext)
  dec = kms.decrypt(CiphertextBlob = ciphertext_blob)
  return dec['Plaintext']

def rss_url_list():
  page = requests.get(YAHOO_JAPAN_HEADLINE_RSS_URL)
  soup = BeautifulSoup(page.content, 'html.parser')
  elements = soup.select('div[class=rss_listbox] a')
  urls = [element.get('href') for element in elements]
  return urls

def rss_news_list(rss_url, from_date):
  news_dict = feedparser.parse(rss_url)
  return [ { 'title': item.title, 'link': item.link } for item in news_dict.entries if hasattr(item, 'published') and parse(item.published) >= from_date ]

def search_latest_news(keywords, period):
  hits = []
  last_hour = datetime.now(pytz.timezone('Asia/Tokyo')) - timedelta(hours = period)
  url_list = rss_url_list()
  for url in url_list:
    print 'RSS URL: %s' % url
    news_list = rss_news_list(url, last_hour)
    for item in news_list:
      for keyword in keywords:
        if keyword.lower() in item['title'].lower():
          print ('News found: %s' % item['title']).encode('utf-8')
          hits.append(item)
          break
  return hits

def notify_to_line(message):
  params = { 'message': message }
  params = urllib.urlencode(params)
  req = urllib2.Request(LINE_NOTIFY_POST_URL)
  req.add_header('Authorization', 'Bearer ' + decript_by_kms(LINE_NOTIFY_BEARER_TOKEN))
  req.add_data(params)
  res = urllib2.urlopen(req)

# Lambda handler
def notify_news_to_line(keywords, period):
  latest_news = search_latest_news(keywords, period)
  print '%d items found' % len(latest_news)
  if len(latest_news) <= 0:
    return

  message = ''
  for item in latest_news:
    message += ("%(title)s\n%(link)s\n" % item).encode('utf-8')
  notify_to_line(message)

# Lambda handler
def lambda_handler(event, context):
  if not 'keywords' in event:
    raise ValueError('Parameter "keywords" is necessary.')
  if not 'period' in event:
    raise ValueError('Parameter "period" is necessary.')
  if not event['period'].isdigit():
    raise ValueError('Invalid parameter value "period"')

  keywords = [keyword.strip() for keyword in event['keywords'].split(',')]
  period = int(event['period'])
  notify_news_to_line(keywords, period)

