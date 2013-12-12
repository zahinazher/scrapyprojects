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
    name = "wallet"
    allowed_domains = ["fatwallet.com"]
    start_urls = [
        "http://fatwallet.com/cash-back-shopping/"
    ]

    op1="fatwallet.csv"
    opfile = csv.writer(open(op1, 'w'), delimiter=',')
    opfile.writerow(["Store Name","Cash Back", "Url", "Category", ""])
    now = datetime.datetime.now()
    logging.basicConfig(filename='logs.log')
    logging.critical('Date: '+str(now))

    def parse(self,response):
      selec = Selector(response)

      #f = open('resp.txt' , 'w')
      #f.write(response.body)

      tag_tr_all = selec.xpath('//tr[@class="storeListRow"]|\
          //tr[@class="storeListRow even"]|\
          //tr[@class="storeListRow even last"]|\
          //tr[@class="storeListRow last"]').extract()


      for tag_tr in tag_tr_all:

        tag_tr =  tag_tr.encode('utf-8', 'ignore').strip()

        store_name = ''
        if re.search(r"class=\"storeListStoreName\">.*?<",tag_tr,re.I|re.S):
          store_name = re.search(r"class=\"storeListStoreName\">.*?<",tag_tr,re.I|re.S).group()
          store_name = re.search(r">.*?<",store_name,re.I|re.S).group()
          store_name = re.sub(r'>',"",re.sub(r'<',"",store_name,re.I))
          store_name = re.sub(r'&amp;',"&",re.sub(r'&amp;',"&",store_name,re.I))
          #print store_name
      
        cash_back = '' ; category = ''
        if re.search(r"class=\"storeListCashbackText\">.*?<",tag_tr,re.I|re.S):
          cash_back = re.search(r"class=\"storeListCashbackText\">.*?<",tag_tr,re.I|re.S).group()
          cash_back = re.search(r">.*?<",cash_back,re.I|re.S).group()
          cash_back = re.sub(r'>',"",re.sub(r'<',"",cash_back,re.I))

        elif re.search(r"class=\"storeListCashbackSaleText\">.*?<",tag_tr,re.I|re.S):
          cash_back = re.search(r"class=\"storeListCashbackSaleText\">.*?<",tag_tr,re.I|re.S).group()
          cash_back = re.search(r">.*?<",cash_back,re.I|re.S).group()
          cash_back = re.sub(r'>',"",re.sub(r'<',"",cash_back,re.I))
          #print cash_back
        else:
          cash_back = "offers only"

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
          link = "http://fatwallet.com" + str(link)
          #print link

          
        self.opfile.writerow([store_name,cash_back,link,category])

