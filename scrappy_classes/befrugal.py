from scrapy.selector import Selector
from scrapy import Spider
from scrapy.http import Request
from scrapy.http import FormRequest
import time
import datetime
import re
import csv
from scrapy.conf import settings

# Scrapes data from befrugal using scrapy framework

#settings.overrides['CONCURRENT_REQUESTS_PER_SPIDER'] = 1
#settings.overrides['CONCURRENT_REQUESTS_PER_DOMAIN'] = 1
settings.overrides['CONCURRENT_REQUESTS_PER_IP'] = 1
settings.overrides['SCHEDULER_DISK_QUEUE'] = 'scrapy.squeue.PickleFifoDiskQueue'
settings.overrides['SCHEDULER_MEMORY_QUEUE'] = 'scrapy.squeue.FifoMemoryQueue'
settings.overrides['WEBSERVICE_ENABLED'] = True

# SCRAPER NAME: befrugal

############ How to use the script ###########

# scrapy startproject befrugal
# cd befrugal
# scrapy crawl befrugal

###############################################

class Befrugal(Spider):
    name = "befrugal"
    allowed_domains = ["befrugal.com"]
    start_urls = [
        "http://www.befrugal.com"
    ]

    op="befrugal.csv"
    opfile = csv.writer(open(op, 'w'), delimiter=',')
    opfile.writerow(["Store Name","Cash Back", "Url", "Category", ""])

    now = datetime.datetime.now()

    def parse(self,response):
      selec = Selector(response)
    
      url = "http://www.befrugal.com/coupons/stores/"

      alphabets_list = ['num','A','B','C','D','E','F','G','H',
                        'I','J','K','L','M','N','O','P','Q',
                        'R','S','T','U','V','W','X','Y','Z']

      count = 0
      for alpha in alphabets_list:
        url_new = url + str(alpha)
        #print url_new
        #if count == 0:
        yield Request(url_new, callback=self.parse_page_1)
        #count +=1


    def parse_page_1(self,response):

      selec = Selector(response)

      # getting data from two different classes 
      # simultaneously to avoid any missing
      tag_tr_all = selec.xpath('//tr[@class="storeTable-row1"]|\
                                //tr[@class="storeTable-row2"]').extract()

      for tag_tr in tag_tr_all:

        tag_tr =  tag_tr.encode('utf-8', 'ignore').strip()

        store_name = '' ; link = ''
        if re.search(r"<a href.*?</a>",tag_tr,re.I|re.S):
          store_name_plus = re.search(r"<a href.*?</a>",tag_tr,re.I|re.S).group()
  
          # Extracting all store titles from store_name_plus
          store_name = re.search(r">.*?<",store_name_plus,re.I|re.S).group()
          store_name = re.sub(r'>',"",re.sub(r'<',"",store_name,re.I))
          store_name = re.sub(r'&amp;',"&",re.sub(r'&amp;',"&",store_name,re.I))  
          #print store_name

          # Extracting all links from store_name_plus
          link = re.search(r"\".*?\"",store_name_plus,re.I|re.S).group()
          link = re.sub(r'><',"",re.sub(r'\"',"",link,re.I))
          link = "http://www.befrugal.com/crumbs/" + link
          #print link


        cash_back = '' ; category = ''
        if re.search(r"<p.*?</p>",tag_tr,re.I|re.S):
          cash_back = re.search(r"<p.*?</p>",tag_tr,re.I|re.S).group()
          cash_back = re.search(r">.*?<",cash_back,re.I|re.S).group()
          cash_back = re.sub(r'>',"",re.sub(r'<',"",cash_back,re.I))
          #print cash_back

          if re.search(r"\$",cash_back,re.I):
            category = "Absolute Cash Back"
          elif re.search(r"%",cash_back,re.I):
            category = "Percentage Cash Back"
          else:
            category = "unknown"
        else:
          cash_back = 'NA'
          category = 'unknown'

        self.opfile.writerow([store_name,cash_back,link,category])
