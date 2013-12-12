from scrapy.selector import Selector
from scrapy.spider import BaseSpider
from scrapy.http import Request
from scrapy.http import FormRequest
import time
import datetime
import logging
import re
import csv


class Fat_Wallet(BaseSpider):
    # name of spider used to run the script
    name = "cactus"
    allowed_domains = ["couponcactus.com"]
    # required urls list
    start_urls = [
        "http://www.couponcactus.com/coupons"
    ]

    op1="cactus.csv"
    opfile = csv.writer(open(op1, 'w'), delimiter=',')
    opfile.writerow(["Store Name","Cash Back", "Url", "Category", ""])

    # get current date and time
    now = datetime.datetime.now()
    # creating a log file
    logging.basicConfig(filename='logs.log')
    logging.critical('Date: '+str(now))

    def parse(self,response):
      selec = Selector(response)

      #f = open('resp.txt' , 'w')
      #f.write(response.body)

      tag_tr_all = selec.xpath('//tr[@class="spon body-content"]|\
                                //tr[@class=" body-content"]').extract()

      count = 0
      for tag_tr in tag_tr_all:

        tag_tr =  tag_tr.encode('utf-8', 'ignore').strip()
        #print tag_tr

        store_name = '' ; link = ''
        if re.search(r"href=\".*?</a>",tag_tr,re.I|re.S):
          store_name = re.search(r"href=\".*?</a>",tag_tr,re.I|re.S).group()

          link = re.search(r"\".*?\"",store_name,re.I|re.S).group()
          link = re.sub(r'\"',"",link,re.I)
          link = "http://www.couponcactus.com" + link
          #print link

          store_name = re.search(r">.*?<",store_name,re.I|re.S).group()
          store_name = re.sub(r'>',"",re.sub(r'<',"",store_name,re.I))
          store_name = re.sub(r'&amp;',"&",re.sub(r'&amp;',"&",store_name,re.I))
          store_name = re.sub(r' coupons$',"",store_name,re.I)
          #print store_name


        cash_back = '' ; category = ''
        if re.search(r"<td .*?</td>",tag_tr,re.I|re.S):
          cash_back = re.findall(r"<td .*?</td>",tag_tr,re.I|re.S)[1]
          cash_back = re.search(r">.*?<",cash_back,re.I|re.S).group()
          cash_back = re.sub(r'>',"",re.sub(r'<',"",cash_back,re.I))
          #print cash_back


        # Differentiating between absolute and percentage cash back
        if re.search(r"\$",cash_back,re.I):
          category = "Absolute Cash Back"
        elif re.search(r"%",cash_back,re.I):
          category = "Percentage Cash Back"
        else:
          category = "unknown"

        self.opfile.writerow([store_name,cash_back,link,category])

