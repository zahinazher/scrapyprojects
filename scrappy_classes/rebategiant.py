from scrapy.selector import Selector
from scrapy import Spider
from scrapy.http import Request
from scrapy.http import FormRequest
import re, os
import csv
from scrapy.conf import settings
from crawler import *

settings.overrides['CONCURRENT_REQUESTS_PER_SPIDER'] = 1
#settings.overrides['CONCURRENT_REQUESTS_PER_DOMAIN'] = 1
settings.overrides['CONCURRENT_REQUESTS_PER_IP'] = 1
settings.overrides['DEPTH_PRIORITY'] = 1
settings.overrides['SCHEDULER_DISK_QUEUE'] = 'scrapy.squeue.PickleFifoDiskQueue'
settings.overrides['SCHEDULER_MEMORY_QUEUE'] = 'scrapy.squeue.FifoMemoryQueue'
#settings.overrides['WEBSERVICE_ENABLED'] = True
#settings.overrides['REDIRECT_ENABLED'] = False

# SCRAPER NAME: rebategiant

############ How to use the script ###########

# scrapy startproject rebategiant
# cd rebategiant
# scrapy crawl rebategiant

###############################################

class Rebate_giant(Spider):
    name = "rebategiant"
    allowed_domains = ["rebategiant.com"]
    start_urls = [
        "http://www.rebategiant.com/stores.html"
    ]

    op="rebategiant.csv"
    opfile = csv.writer(open(op, 'w'), delimiter=',')
    opfile.writerow(["Store Name","Cash Back", "Url", "Category", ""])

    def parse_page_1(self,data):

      selec = Selector(text=data)

      tag_tr_all = selec.xpath('//div[@class="box list"]//tr').extract()

      for tag_tr in tag_tr_all:
        #print tag_tr

        #tag_tr =  tag_tr.encode('utf-8', 'ignore').strip()

        store_name = '' ; link = ''
        if re.search(r"<a href=.*?</a>",tag_tr,re.I|re.S):
          name_ = re.search(r"<a href=.*?</a>",tag_tr,re.I|re.S).group()

          store_name = re.search(r">.*?<",name_,re.I|re.S).group()
          store_name = re.sub(r'>',"",re.sub(r'<',"",store_name,re.I))
          store_name = re.sub(r'^ ',"",re.sub(r'&amp;',"&",store_name,re.I))  
          store_name = re.sub(r' $',"",re.sub(r'  $',"",store_name,re.I))  
          #print store_name

          link = re.search(r"\".*?\"",name_,re.I|re.S).group()
          link = re.sub(r'>>',"",re.sub(r'\"',"",link,re.I))
          #print link

          cash_back = '' ; category = ''
          if re.search(r"<strong>.*?</strong>",tag_tr,re.I|re.S):
            cash_back = re.search(r"<strong>.*?</strong>",tag_tr,re.I|re.S).group()
            cash_back = re.search(r">.*?<",cash_back,re.I|re.S).group()
            cash_back = re.sub(r'>',"",re.sub(r'<',"",cash_back,re.I))
            #print cash_back

            if re.search(r"\$",cash_back,re.I):
              category = "Absolute Cash Back"
            elif re.search(r"%",cash_back,re.I):
              category = "Percentage Cash Back"
            else:
              category = "unknown"

          self.opfile.writerow([store_name,cash_back,link,category])


    def parse(self,response):
      selec = Selector(response)

      u_all = selec.xpath('//div[@class="pages"]//a/@href').extract()
      if len(u_all) > 0:
        url_last = u_all[len(u_all)-3]
        page_num_last = re.search(r"pg=.*?$",url_last,re.I|re.S).group()
        page_num_last = re.sub(r'pg=',"",re.sub(r'pg=',"",page_num_last,re.I))
        #print page_num_last

        u_ = re.search(r".*?pg=",url_last,re.I|re.S).group()

        count = 0
        for pg_num in range(1,int(page_num_last)+1):

          #if count == 0:
          url_new = u_ + str(pg_num)
          url_new = "http://www.rebategiant.com" + url_new

          cmd = os.popen("python crawler.py -u " +  url_new + " -f " + 'res.txt') 
          cmd.close()
          f = open('res.txt','rb')
          data = f.read()
          self.parse_page_1(data)

          #count +=1

    
