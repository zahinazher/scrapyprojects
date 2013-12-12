from scrapy.selector import Selector
from scrapy.spider import BaseSpider
from scrapy.http import Request
from scrapy.http import FormRequest
import time
import datetime
import logging
import re
import csv
from scrapy.conf import settings

# SCRAPER NAME: pandacashback

############ How to use the script ###########

# scrapy startproject pandacashback
# cd pandacashback
# scrapy crawl panda

###############################################

settings.overrides['CONCURRENT_REQUESTS_PER_SPIDER'] = 1
#settings.overrides['CONCURRENT_REQUESTS_PER_DOMAIN'] = 1
settings.overrides['CONCURRENT_REQUESTS_PER_IP'] = 1
settings.overrides['SCHEDULER_DISK_QUEUE'] = 'scrapy.squeue.PickleFifoDiskQueue'
settings.overrides['SCHEDULER_MEMORY_QUEUE'] = 'scrapy.squeue.FifoMemoryQueue'
settings.overrides['WEBSERVICE_ENABLED'] = True


class PandaCashBack(BaseSpider):
    name = "panda"
    allowed_domains = ["pandacashback.com"]
    start_urls = [
        "http://pandacashback.com/retailers.php"
    ]

    # storing urls of alphabets that have only one page
    url_page_0_list = []
    # Count check for number of alphabets
    count_alpha = 0

    op="pandacashback.csv"
    opfile = csv.writer(open(op, 'w'), delimiter=',')
    opfile.writerow(["Store Name","Cash Back", "Url", "Catagory", ""])

    now = datetime.datetime.now()
    logging.basicConfig(filename='logs.log')
    logging.critical('Date: '+str(now))

    def parse(self,response):
      selec = Selector(response)
    
      url = "http://www.pandacashback.com/retailers.php?letter="

      alphabets_list = ['0-9','A','B','C','D','E','F','G','H',
                        'I','J','K','L','M','N','O','P','Q',
                        'R','S','T','U','V','W','X','Y','Z']

      count = 0
      for alpha in alphabets_list:
        url_new = url + str(alpha)
        self.url_page_0_list.append(url_new)

        #if count == 0:
        yield Request(url_new, callback=self.parse_page_1, dont_filter = True)
        #count +=1


    def parse_page_1(self,response):

      selec = Selector(response)

      if re.search(r"column=title&order=asc&page=2",response.body,re.I|re.S):

        pages_links_all = selec.xpath('//div[@class="pagination"]//a/@href').extract()
        #print pages_links_all
 
        u_all = pages_links_all
        

        if len(u_all) > 0:
          url_last = u_all[len(u_all)-2]
          page_num_last = re.search(r"page=.*?$",url_last,re.I|re.S).group()
          page_num_last = re.sub(r'page=',"",re.sub(r'page=',"",page_num_last,re.I))
          
          #print page_num_last

          u_ = re.search(r".*?page=",url_last,re.I|re.S).group()

          for pg_num in range(1,int(page_num_last)+1):
            url_new = u_ + str(pg_num)
            url_new = "http://www.pandacashback.com/" + url_new
            #print url_new

            yield Request(url_new, callback=self.parse_page_2, dont_filter = True)

      else:
        #print self.url_page_0_list[self.count_alpha]
        yield Request(self.url_page_0_list[self.count_alpha], callback=self.parse_page_2, dont_filter = True)

      self.count_alpha += 1

    def parse_page_2(self,response):

      selec = Selector(response)

      tag_tr_all = selec.xpath('//div[@class="featuerd_box"]').extract()

      for tag_tr in tag_tr_all:
        #print tag_tr

        tag_tr =  tag_tr.encode('utf-8', 'ignore').strip()

        store_name = ''
        if re.search(r"<a href=\".*?</a>",tag_tr,re.I|re.S):
          store_name_plus = re.search(r"<a href=\".*?</a>",tag_tr,re.I|re.S).group()

          store_name = re.search(r">.*?<",store_name_plus,re.I|re.S).group()
          store_name = re.sub(r'>',"",re.sub(r'<',"",store_name,re.I))
          store_name = re.sub(r'&amp;',"&",re.sub(r'&amp;',"&",store_name,re.I))
          store_name = re.sub(r' $',"",store_name,re.I)
          #print store_name

          link = re.search(r"\".*?\"",store_name_plus,re.I|re.S).group()
          link = re.sub(r'\"',"",link,re.I)
          link = re.sub(r'^\.\.',"",link,re.I)
          link = "http://www.pandacashback.com" + str(link)
          #print link


        cash_back = '' ; category = ''
        if re.search(r"class=\"price_tag\">.*?<",tag_tr,re.I|re.S):
          cash_back = re.search(r"class=\"price_tag\">.*?<",tag_tr,re.I|re.S).group()
          cash_back = re.search(r">.*?<",cash_back,re.I|re.S).group()
          cash_back = re.sub(r'>',"",re.sub(r'<',"",cash_back,re.I))
          cash_back = re.sub(r' Cash Back$',"",cash_back,re.I)
          #print cash_back

          if re.search(r"\$",cash_back,re.I):
            category = "Absolute Cash Back"
          elif re.search(r"%",cash_back,re.I):
            category = "Percentage Cash Back"
          else:
            category = "unknown"
        else:
          cash_back = 'NA'
          category = "unknown"


        self.opfile.writerow([store_name,cash_back,link,category])
