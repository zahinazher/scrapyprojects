from scrapy.selector import Selector
from scrapy.spider import BaseSpider
from scrapy.http import Request
from scrapy.http import FormRequest
import time
import datetime
import logging
import re
import csv

# SCRAPER NAME: savingswatch

############ How to use the script ###########

# scrapy startproject savingswatch
# cd savingswatch
# scrapy crawl savingswatch

###############################################

class Fat_Wallet(BaseSpider):
    name = "savingswatch"
    allowed_domains = ["savingswatch.com"]
    start_urls = [
        "http://www.savingswatch.com/allstores/81150/"
    ]

    op1="savingswatch.csv"
    opfile = csv.writer(open(op1, 'w'), delimiter=',')
    opfile.writerow(["Store Name","Cash Back", "Url", "Category", ""])
    now = datetime.datetime.now()
    logging.basicConfig(filename='logs.log')
    logging.critical('Date: '+str(now))

    def parse(self,response):
      selec = Selector(response)

      #f = open('resp.txt' , 'w')
      #f.write(response.body)

      tag_tr_all = selec.xpath('//div[@id="catlistline"]').extract()


      for tag_tr in tag_tr_all:

        tag_tr =  tag_tr.encode('utf-8', 'ignore').strip()

        store_name = '' ; link = ''
        # class="store" 
        if re.search(r"<a href=.*?</a>",tag_tr,re.I|re.S):
          store_name = re.search(r"<a href=.*?</a>",tag_tr,re.I|re.S).group()

          link = re.search(r"<a href=\".*?\"",tag_tr,re.I|re.S).group()
          link = re.search(r"\".*?\"",link,re.I|re.S).group()
          link = re.sub(r'><',"",re.sub(r'\"',"",link,re.I))
          link = "http://www.savingswatch.com" + link
          #print link

          store_name = re.search(r">.*?<",store_name,re.I|re.S).group()
          store_name = re.sub(r'>',"",re.sub(r'<',"",store_name,re.I))
          store_name = re.sub(r'&amp;',"&",re.sub(r'&amp;',"&",store_name,re.I))
          #print store_name


        cash_back = '' ; category = ''
        # class="rebate"
        if re.search(r"class=\"rebate\">.*?</a>",tag_tr,re.I|re.S):
          cash_back = re.search(r"class=\"rebate\">.*?</a>",tag_tr,re.I|re.S).group()
          cash_back = re.search(r"href=.*?</a>",cash_back,re.I|re.S).group()
          cash_back = re.search(r">.*?<",cash_back,re.I|re.S).group()
          cash_back = re.sub(r'>',"",re.sub(r'<',"",cash_back,re.I))
          #print cash_back

        if re.search(r"\$",cash_back,re.I):
          category = "Absolute Cash Back"
        elif re.search(r"%",cash_back,re.I):
          category = "Percentage Cash Back"
        else:
          category = "unknown"

        # Exporting the scraped result
        self.opfile.writerow([store_name,cash_back,link,category])

