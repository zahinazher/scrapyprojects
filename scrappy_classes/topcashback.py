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

# SCRAPER NAME: topcashback

############ How to use the script ###########

# scrapy startproject topcashback
# cd topcashback
# scrapy crawl topcashback

###############################################

settings.overrides['CONCURRENT_REQUESTS_PER_SPIDER'] = 1
#settings.overrides['CONCURRENT_REQUESTS_PER_DOMAIN'] = 1
settings.overrides['CONCURRENT_REQUESTS_PER_IP'] = 1
settings.overrides['SCHEDULER_DISK_QUEUE'] = 'scrapy.squeue.PickleFifoDiskQueue'
settings.overrides['SCHEDULER_MEMORY_QUEUE'] = 'scrapy.squeue.FifoMemoryQueue'
settings.overrides['WEBSERVICE_ENABLED'] = True


class TopCashBack(Spider):
    name = "topcashback"
    allowed_domains = ["topcashback.com"]
    start_urls = [
        "http://topcashback.com"
    ]

    # storing urls of alphabets that have only one page
    url_page_0_list = []
    # Count check for number of alphabets
    count_alpha = 0

    op="topcashback.csv"
    opfile = csv.writer(open(op, 'w'), delimiter=',')
    opfile.writerow(["Store Name","Cash Back", "Url", "Catagory", ""])

    now = datetime.datetime.now()
    logging.basicConfig(filename='logs.log')
    logging.critical('Date: '+str(now))

    def parse(self,response):
      selec = Selector(response)
    
      url = "http://www.topcashback.com/search/merchants/?letter="

      alphabets_list = ['0','A','B','C','D','E','F','G','H',
                        'I','J','K','L','M','N','O','P','Q',
                        'R','S','T','U','V','W','X','Y','Z']

      count = 0
      for alpha in alphabets_list:
        url_new = url + str(alpha)
        self.url_page_0_list.append(url_new)
        #print url_new
        #if count == 0:
        yield Request(url_new, callback=self.parse_page_1, dont_filter = True)
        #count +=1


    def parse_page_1(self,response):

      selec = Selector(response)

      if re.search(r"/search/merchants/\?letter=.&page=2",response.body,re.I|re.S):

        pages_links_all = selec.xpath('//div[@class="pagination-nav-comments"]').extract()[2]

        #pages_links_ =  pages_links_all.encode('utf-8', 'ignore').strip()

        url_list = []
        if re.search(r"<li>.*?</li>",pages_links_all,re.I|re.S):
          tag_a_all = re.findall(r"<a href=\".*?\"",pages_links_all,re.I|re.S)
          for tag_a in tag_a_all:
            u = re.search(r"\".*?\"",tag_a,re.I|re.S).group()
            u = re.sub(r'&amp;',"&",re.sub(r'\"',"",u,re.I))
            url_list.append(u)
            #print tag_a

          u_all = sorted(set(url_list))

          if len(u_all) > 0:
            u_0 = u_all[0]
            u_0 = re.search(r".*?page=",u_0,re.I|re.S).group()
            u_0 = u_0 + '1'
            u_all.insert(0,u_0)

            for url in u_all:

              url_new = "http://www.topcashback.com" + str(url)
              #print url_new
              yield Request(url_new, callback=self.parse_page_2, dont_filter = True)
 
        else:
          #print self.url_page_0_list[self.count_alpha]
          yield Request(self.url_page_0_list[self.count_alpha], callback=self.parse_page_2, dont_filter = True)

      else:
        #print self.url_page_0_list[self.count_alpha]
        yield Request(self.url_page_0_list[self.count_alpha], callback=self.parse_page_2, dont_filter = True)

      self.count_alpha += 1

    def parse_page_2(self,response):

      selec = Selector(response)

      tag_tr_all = selec.xpath('//div[@class="offerlist-container"]').extract()

      for tag_tr in tag_tr_all:
        #print tag_tr

        tag_tr =  tag_tr.encode('utf-8', 'ignore').strip()

        store_name = ''
        if re.search(r"class=\"offerlist-description-title\".*?<",tag_tr,re.I|re.S):
          store_name = re.search(r"class=\"offerlist-description-title\".*?<",tag_tr,re.I|re.S).group()
          store_name = re.search(r">.*?<",store_name,re.I|re.S).group()
          store_name = re.sub(r'>',"",re.sub(r'<',"",store_name,re.I))
          store_name = re.sub(r'&amp;',"&",re.sub(r'&amp;',"&",store_name,re.I))
          store_name = re.sub(r' Cashback',"",re.sub(r' $',"",store_name,re.I))
          #print store_name


        link = ''
        if re.search(r"class=\"offerlist-description\">.*?</a>",tag_tr,re.I|re.S):

          link = re.search(r"<a href=.*?>",tag_tr,re.I|re.S).group()
          link = re.search(r"\".*?\"",link,re.I|re.S).group()
          link = re.sub(r'\"',"",link,re.I)
          link = "http://www.topcashback.com" + str(link)
          #print link


        cash_back = '' ; category = ''
        if re.search(r"class=\"rate\">.*?<",tag_tr,re.I|re.S):
          cash_back = re.search(r"class=\"rate\">.*?<",tag_tr,re.I|re.S).group()
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
          category = "unknown"


        self.opfile.writerow([store_name,cash_back,link,category])
