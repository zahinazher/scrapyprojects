from scrapy.selector import Selector
from scrapy import Spider
from scrapy.http import Request
from scrapy.http import FormRequest
import time
import datetime
import logging
import re
import csv
from scrapy.conf import settings

settings.overrides['CONCURRENT_REQUESTS_PER_SPIDER'] = 1
#settings.overrides['CONCURRENT_REQUESTS_PER_DOMAIN'] = 1
#settings.overrides['CONCURRENT_REQUESTS_PER_IP'] = 1
settings.overrides['SCHEDULER_DISK_QUEUE'] = 'scrapy.squeue.PickleFifoDiskQueue'
settings.overrides['SCHEDULER_MEMORY_QUEUE'] = 'scrapy.squeue.FifoMemoryQueue'
settings.overrides['WEBSERVICE_ENABLED'] = True


class Mr_rebates(Spider):
    name = "rebates"
    allowed_domains = ["mrrebates.com"]
    start_urls = [
        "http://mrrebates.com/merchants/all_merchants_tabbed.asp"
    ]

    op="mrrebates.csv"
    opfile = csv.writer(open(op, 'w'), delimiter=',')
    opfile.writerow(["Store Name","Cash Back", "Url", "Catagory", ""])

    now = datetime.datetime.now()
    logging.basicConfig(filename='logs.log')
    logging.critical('Date: '+str(now))

    def parse(self,response):
      selec = Selector(response)
    
      url = "http://mrrebates.com/merchants/all_merchants_tabbed.asp?letter="

      alphabets_list = ["#",'a','b','c','d','e','f','g','h',
                        'i','j','k','l','m','n','o','p','q',
                        'r','s','t','u','v','w','x','y','z']

      count = 0
      for alpha in alphabets_list:
        url_new = url + str(alpha)
        #print url_new
        #if count == 0:
        yield Request(url_new, callback=self.parse_page_1)
        #count +=1


    def parse_page_1(self,response):


      selec = Selector(response)

      tag_tr_all = selec.xpath('//tr[@class="even"]|\
                        //tr[@class="odd"]').extract()

      for tag_tr in tag_tr_all:
        #print tag_tr

        tag_tr =  tag_tr.encode('utf-8', 'ignore').strip()

        store_name = ''
        if re.search(r"<b>.*?</b>",tag_tr,re.I|re.S):
          store_name = re.search(r"<b>.*?</b>",tag_tr,re.I|re.S).group()
          store_name = re.sub(r'<b>',"",re.sub(r'</b>',"",store_name,re.I))
          store_name = re.sub(r'&amp;',"&",re.sub(r'&amp;',"&",store_name,re.I))  
          #print store_name


        cash_back = '' ; category = ''
        if re.search(r"class=\"r\">.*?<",tag_tr,re.I|re.S):
          cash_back = re.search(r"class=\"r\">.*?<",tag_tr,re.I|re.S).group()
          cash_back = re.search(r">.*?<",cash_back,re.I|re.S).group()
          cash_back = re.sub(r'>',"",re.sub(r'<',"",cash_back,re.I))
          #print cash_back

          if re.search(r"\$",cash_back,re.I):
            category = "Absolute Cash Back"
          elif re.search(r"%",cash_back,re.I):
            category = "Percentage Cash Back"
          else:
            category = "unknown"

        link = ''
        if re.search(r"<a href.*?>",tag_tr,re.I|re.S):

          link = re.search(r"<a href.*?>",tag_tr,re.I|re.S).group()
          link = re.search(r"\".*?\"",link,re.I|re.S).group()
          link = re.search(r"\".*?\"",link,re.I|re.S).group()
          link = re.sub(r'\"',"",link,re.I)
          link = "http://mrrebates.com" + str(link)
          #print link

        self.opfile.writerow([store_name,cash_back,link,category])
