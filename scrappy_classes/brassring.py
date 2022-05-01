"""
author: Zahin Azher 
"""

from scrapy.selector import Selector
from scrapy import Spider
from scrapy.http import Request
from scrapy.http import FormRequest
from scrapy.http.cookies import CookieJar
import time
import datetime
import logging
import re
import csv

op1="output.csv"
opfile1 = csv.writer(open(op1, 'w'), delimiter=',')
opfile1.writerow(["Job Title","Description"])

class Brassring(Spider):
    name = "brass"
    allowed_domains = ["sjobs.brassring.com"]
    start_urls = [
        "https://sjobs.brassring.com/TGWebHost/home.aspx?partnerid=511&siteid=231"
    ]

    now = datetime.datetime.now()
    logging.basicConfig(filename='logs.log')
    logging.critical('Date: '+str(now))

    def parse(self,response):
      selec = Selector(response)
      uri = selec.select('//a[contains(text(),"Search Openings")]/@href').extract()[0]
      """div_title_all = selec.xpath('//div[@id="titletext1"]').extract()
      #body = selec.xpath('//title')

      div_title = div_title_all[0]
      sid = re.search(r"\"search.*?SID=.*?\"",str(div_title),re.I|re.S).group()
      sid = re.search(r"SID=.*?\"",str(sid),re.I|re.S).group()
      sid = re.sub(r"SID=","",re.sub(r"\"","",str(sid),re.I))"""
      url_search = 'https://sjobs.brassring.com/TGWebHost/' + uri
      #print "URI1",url_search

      yield Request("https://sjobs.brassring.com/TGWebHost/%s" % uri, callback=self.parse_page_1)

    def parse_page_1(self,response):

      selec = Selector(response)

      uri2 = selec.xpath('//form[@name="aspnetForm"]/@action').extract()[0]

      url2 = 'https://sjobs.brassring.com/TGWebHost/' + uri2
      #print "URL2",url2

      event_val = selec.xpath('//input[@id="__EVENTVALIDATION"]/@value').extract()[0]
      #print "event_val",event_val


      """return [FormRequest(url=url2,
        formdata={
          '__EVENTVALIDATION': event_val,
          'cleartype':'no',
          'faqueue':'',
          'hEmailIdList':'',
          'CONTROLName':'||BH||Question51184__FORMTEXT41_||EH||',
          'NAME_34778__FormText26_':'Job Family',
          'NAME_34781__FormText29_':'Location Type',
          'NAME_51181__FORMTEXT40_':'Country',
          'NAME_51184__FORMTEXT41_':'State/Province',
          'CHILD__51181':'Question51184__FORMTEXT41%-%51184',
          'Question51181__FORMTEXT40':'AnswerName&=|=X|%%%AnswerValue&=|=X|%%%GDEAnswerValue&=|TG_SEARCH_ALL=X|???',
          'Question51184__FORMTEXT41':'AnswerName&=|=X|%%%AnswerValue&=|=X|%%%GDEAnswerValue&=|TG_SEARCH_ALL=X|???',
          'Question34778__FormText26':'AnswerName&=|=X|%%%AnswerValue&=|=X|%%%GDEAnswerValue&=|TG_SEARCH_ALL=X|???',
          'Question34781__FormText29':'AnswerName&=|=X|%%%AnswerValue&=|=X|%%%GDEAnswerValue&=|TG_SEARCH_ALL=X|???',
          'keyword':'',
          'UseJobMatchCriteria':'false',
          'submit2':'',
          'ctl00$MainContent$JobMatchTextArea':''},
        callback=self.parse_page_2)]"""

      n = 1 # count for number of pages
      while (n < 200):
        print "count_n",n
        yield FormRequest(url=url2,
          formdata={
            'JobInfo':'%%',
            'recordstart':str(n),
            'totalrecords':'700',
            'sortOrder':'ASC',
            'sortField':'JobTitle',
            'sorting':'',
            'JobSiteInfo':''},
          callback=self.parse_page_2)
        n += 50
      
    def parse_page_2(self,response):
      if not "Search results" in response.body:
        logging.critical('Post Request Failed')
        print "Post Request Failed"
        return


      print "page2"

      list_links = []
      urls_all = re.findall(r"href=jobdetails.aspx.*?>",str(response.body),re.I|re.S)

      for line in urls_all:
        u = re.sub(r"href=","",re.sub(r">","",str(line),re.I|re.S))
        u = re.sub(r">","",re.sub(r"amp;","",str(u),re.I|re.S))
        link = 'https://sjobs.brassring.com/TGWebHost/' + u
        list_links.append(link)

      for link in list_links:
        yield Request(link, callback=self.parse_page_3)


    def parse_page_3(self,response):
      print "page3"
      job_title = re.search(r"id=\'Job Abbreviation Title\'.*?</span>",str(response.body),re.I|re.S).group()
      job_title = re.search(r">.*?</span>",str(job_title),re.I|re.S).group()
      job_title = re.sub(r"^>","",re.sub(r"</span>","",str(job_title),re.I|re.S))

      job_desc = re.search(r"id=\'Job Description\'.*?</span>",str(response.body),re.I|re.S).group()
      job_desc = re.search(r">.*?</span>",str(job_desc),re.I|re.S).group()
      job_desc = re.sub(r"^>","",re.sub(r"</span>","",str(job_desc),re.I|re.S))
      job_desc = re.sub(r"<br/>","",re.sub(r"<br/>","",str(job_desc),re.I|re.S))

      opfile1.writerow([job_title,job_desc])
      

