from scrapy.selector import Selector
from scrapy import Spider
from scrapy.http import Request
from scrapy.http import FormRequest
import time
import datetime
import re
import csv

"""
@author: Zahin
"""

from scrapy.conf import settings
#settings.overrides['CONCURRENT_REQUESTS_PER_SPIDER'] = 1
#settings.overrides['SCHEDULER_MEMORY_QUEUE'] = 'scrapy.squeue.FifoMemoryQueue'

class Fat_Wallet(Spider):
    # name of spider used to run the script
    name = "cardsnagger"
    allowed_domains = ["cardsnagger.com"]
    # required urls list
    start_urls = [
        "http://buy.cardsnagger.com/buy/"
    ]

    op1="./../Results/cardsnagger.csv"
    opfile = csv.writer(open(op1, 'w'), delimiter=',')
    opfile.writerow(["Store Name","Cash Back", "Url", "Category", ""])

    def parse(self,response):
      selec = Selector(response)
      url = "http://buy.cardsnagger.com/buy/?sort=alphaasc&page="

      #f = open('resp.txt' , 'w')
      #f.write(response.body)

      tag_div_all = selec.xpath('//ul[@class="PagingList"]//li/a/text()').extract()
      stock =  selec.xpath('//ul[@class="PagingList"]//li/a/text()').extract()[len(tag_div_all)-1]
      #print stock

      #total_pages = re.search(r"[0-9][0-9][0-9]|[0-9][0-9]|[0-9]",tag_div_all,re.I).group()

      count = 0
      for alpha in range(1,int(stock)+1):
        url_new = url + str(alpha)
        yield Request(url_new, callback=self.parse_page_1, dont_filter = True)

    def parse_page_1(self,response):

      selec = Selector(response)

      tag_div_all = selec.xpath('//ul[@class="ProductList "]//li')

      count = 0
      for tag_tr_raw in tag_div_all:
        tag_tr = tag_tr_raw.extract()

        tag_tr =  tag_tr.encode('utf-8', 'ignore').strip()
        #print tag_tr

        store_name = '' ; link = ''
        if re.search(r"href=\".*?</a>",tag_tr,re.I|re.S):
          store_name = re.search(r"href=\".*?</a>",tag_tr,re.I|re.S).group()

          link = re.search(r"\".*?\"",store_name,re.I|re.S).group()
          link = re.sub(r'\"',"",link,re.I)
          #print link

          store_name = tag_tr_raw.xpath('//div[@class="ProductDetails"]//a/text()').extract()[count]
          store_name = re.sub(r'Card',"",re.sub(r'Gift Card',"",str(store_name),re.I))
          store_name = re.sub(r'^ ',"",re.sub(r' $',"",str(store_name),re.I))
          #print store_name
          cash_back_new = re.search(r"\$.*[0-9]",store_name,re.I|re.S).group()

        cash_back = '' ; category = ''
        if re.search(r"class=\"RetailPriceValue\">.*?<",tag_tr,re.I|re.S):
          cash_back = re.search(r"class=\"RetailPriceValue\">.*?<",tag_tr,re.I|re.S).group()
          cash_back = re.search(r">.*?<",cash_back,re.I|re.S).group()
          cash_back = re.sub(r'>',"",re.sub(r'<',"",cash_back,re.I))
          cash_back = re.sub(r'\"',"",re.sub(r'\"',"",cash_back,re.I))
          cash_back = re.sub(r'\$',"",re.sub(r'\$',"",cash_back,re.I))
          retail_price = re.sub(r'^ ',"",re.sub(r' $',"",cash_back,re.I))
          #print retail_price

          if re.search(r"class=\"RetailPriceValue\">.*?<.*?>.*?<",tag_tr,re.I|re.S):
            cash_back = re.search(r"class=\"RetailPriceValue\">.*?<.*?>.*?<",tag_tr,re.I|re.S).group()
            cash_back = re.search(r"<.*?<",cash_back,re.I|re.S).group()
            cash_back = re.search(r">.*?<",cash_back,re.I|re.S).group()
            cash_back = re.sub(r'>',"",re.sub(r'<',"",cash_back,re.I))
            cash_back = re.sub(r'\"',"",re.sub(r'\"',"",cash_back,re.I))
            cash_back = re.sub(r'\$',"",re.sub(r'\$',"",cash_back,re.I))
            discounted_price = re.sub(r'^ ',"",re.sub(r' $',"",cash_back,re.I))
            #print discounted_price


        else:
          cash_back = re.sub(r'\"',"",re.sub(r'\"',"",cash_back_new,re.I))
          cash_back = re.sub(r'\$',"",re.sub(r'\$',"",cash_back,re.I))
          retail_price = re.sub(r'^ ',"",re.sub(r' $',"",cash_back,re.I))
          #print retail_price

          cash_back = re.search(r"<em>.*?</em>",tag_tr,re.I|re.S).group()
          cash_back = re.search(r">.*?<",cash_back,re.I|re.S).group()
          cash_back = re.sub(r'>',"",re.sub(r'<',"",cash_back,re.I))
          cash_back = re.sub(r'\"',"",re.sub(r'\"',"",cash_back,re.I))
          cash_back = re.sub(r'\$',"",re.sub(r'\$',"",cash_back,re.I))
          discounted_price = re.sub(r'^ ',"",re.sub(r' $',"",cash_back,re.I))
          #print discounted_price

        cash_back = ((float(retail_price)-float(discounted_price))/float(retail_price))*100
        cash_back = round(cash_back,2)
        cash_back = re.sub(r'$',"%",str(cash_back),re.I)
        #print cash_back

        # Differentiating between absolute and percentage cash back
        if re.search(r"\$",cash_back,re.I):
          category = "Absolute Cash Back"
        elif re.search(r"%",cash_back,re.I):
          category = "Percentage Cash Back"
        else:
          category = "unknown"

        #------------ check for out of stock store names
        #if stock != "0":
        self.opfile.writerow([store_name,cash_back,link,category])
        count += 1
