from scrapy.selector import Selector
from scrapy.spider import BaseSpider
from scrapy.http import Request
from scrapy.http import FormRequest
import time
import datetime
import re
import csv
from scrapy.conf import settings

#settings.overrides['CONCURRENT_REQUESTS_PER_DOMAIN'] = 1
#settings.overrides['SCHEDULER_MEMORY_QUEUE'] = 'scrapy.squeue.FifoMemoryQueue'

class Fat_Wallet(BaseSpider):
    # name of spider used to run the script
    name = "giftcardgranny"
    allowed_domains = ["giftcardgranny.com"]
    # required urls list
    start_urls = [
        "http://www.giftcardgranny.com/buy-gift-cards/"
    ]

    op1="./../Results/giftcardgranny.csv"
    opfile = csv.writer(open(op1, 'w'), delimiter=',')
    opfile.writerow(["Store Name","Cash Back", "Url", "Category", ""])

    def parse(self,response):
      selec = Selector(response)

      #f = open('resp.txt' , 'w')
      #f.write(response.body)

      tag_div_all = selec.xpath('//div[@class="content"]//tr//td').extract()

      count = 0
      for tag_tr in tag_div_all:

        tag_tr =  tag_tr.encode('utf-8', 'ignore').strip()
        #print tag_tr
        if count > -1:
          store_name = '' ; link = ''
          if re.search(r"href=\".*?</a>",tag_tr,re.I|re.S):
            store_name = re.search(r"href=\".*?</a>",tag_tr,re.I|re.S).group()

            link = re.search(r"\".*?\"",store_name,re.I|re.S).group()
            link = re.sub(r'\"',"",link,re.I)
            link = "http://www.giftcardgranny.com" + link
            #print link

            """store_name = re.search(r">.*?<",store_name,re.I|re.S).group()
            store_name = re.sub(r'<',"",re.sub(r'>',"",store_name,re.I))
            store_name = re.sub(r'&amp;',"&",store_name,re.I)
            store_name = re.sub(r'^ ',"",re.sub(r' $',"",store_name,re.I))
            #print store_name"""

            yield Request(link, callback=self.parse_page_1, dont_filter = True)
            count += 1

    def parse_page_1(self,response):

      store_name = '' ; link = ''
      link = response.url
      #print link

      selec = Selector(response)
      title = selec.xpath('//div[@class="alert_header"]/h1/text()').extract()[0]
      title = re.sub(r'<',"",re.sub(r'Gift Cards',"",title,re.I))
      store_name = re.sub(r'^ ',"",re.sub(r' $',"",title,re.I))
      #print store_name

      tag_div_all = selec.xpath('//tbody//tr//td[@class="save"]/text()').extract()
      discount_list = []
      for value in tag_div_all:
        val = re.sub(r'%',"",str(value),re.I)
        dis = float(val)
        discount_list.append(dis)
      cash_back = max(discount_list)
      cash_back = str(cash_back)+'%'
      #print cash_back

      # Differentiating between absolute and percentage cash back
      if re.search(r"\$",cash_back,re.I):
        category = "Absolute Cash Back"
      elif re.search(r"%",cash_back,re.I):
        category = "Percentage Cash Back"
      else:
        category = "unknown"
      #
      self.opfile.writerow([store_name,cash_back,link,category])

