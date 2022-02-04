from scrapy.selector import Selector
from scrapy.spider import BaseSpider
from scrapy.http import Request
from scrapy.http import FormRequest
import time
import datetime
import logging
import re
import csv

"""
@author: Zahin
"""

class Ebates(BaseSpider):
    name = "ebates"
    allowed_domains = ["ebates.com"]
    start_urls = [
        "http://www.ebates.com/stores/all/index.htm?navigation_id=18568"
    ]

    now = datetime.datetime.now()
    logging.basicConfig(filename='logs.log')
    logging.critical('Date: '+str(now))

    op1="ebates.csv"
    opfile = csv.writer(open(op1, 'w'), delimiter=',')
    opfile.writerow(["Store Name","Cash Back", "Url", "Category", ""])


    def parse(self,response):
      selec = Selector(response)
      #f = open('resp.txt' , 'w')
      #f.write(response.body)

      tag_tr_all = selec.xpath('//table[@id="moreStoresTable"]//tr').extract()

      for tag_tr in tag_tr_all:

        tag_tr =  tag_tr.encode('utf-8', 'ignore').strip()
        store_name = ''
        if re.search(r"class=\"storeName\".*?</td>",tag_tr,re.I|re.S):
          store_name = re.search(r"class=\"storeName\".*?</td>",tag_tr,re.I|re.S).group()
          store_name = re.search(r"href=.*?<",store_name,re.I|re.S).group()

          link = re.search(r"href=.*?>",store_name,re.I|re.S).group()
          link = re.sub(r'href=',"",re.sub(r'>',"",link,re.I))
          link = re.sub(r'\"',"",re.sub(r'\"',"",link,re.I))
          link = "http://www.ebates.com" + str(link)
          #print link

          store_name = re.search(r">.*?<",store_name,re.I|re.S).group()
          store_name = re.sub(r'>',"",re.sub(r'<',"",store_name,re.I))
          store_name = re.sub(r'&amp;',"&",re.sub(r'&amp;',"&",store_name,re.I))
          store_name = re.search(r".*?\n",store_name,re.I|re.S).group()
          store_name = re.sub(r'\n\n',"",re.sub(r'Coupons',"",store_name,re.I))
          store_name = re.sub(r'\r',"",re.sub(r'\n',"",store_name,re.I))
          store_name = re.sub(r' $',"",re.sub(r'  $',"",store_name,re.I))
          #print store_name
          
        cash_back = '' ; category = ''
        if re.search(r"target=\"_blank\">.*?<",tag_tr,re.I|re.S):
          cash_back = re.search(r"target=\"_blank\">.*?<",tag_tr,re.I|re.S).group()
          cash_back = re.search(r">.*?<",cash_back,re.I|re.S).group()
          cash_back = re.sub(r'>',"",re.sub(r'<',"",cash_back,re.I))
          #print cash_back

          if re.search(r"\$",cash_back,re.I):
            category = "Absolute Cash Back"
          elif re.search(r"%",cash_back,re.I):
            category = "Percentage Cash Back"
          else:
            category = "unknown"

        if len(store_name) > 1:
          self.opfile.writerow([store_name,cash_back,link,category])

