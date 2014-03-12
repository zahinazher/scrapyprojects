from scrapy.selector import Selector
from scrapy.spider import BaseSpider
from scrapy.http import Request
from scrapy.http import FormRequest
import time
import datetime
import re
import csv

from scrapy.conf import settings
#settings.overrides['CONCURRENT_REQUESTS_PER_SPIDER'] = 1
#settings.overrides['SCHEDULER_MEMORY_QUEUE'] = 'scrapy.squeue.FifoMemoryQueue'

class Fat_Wallet(BaseSpider):
    # name of spider used to run the script
    name = "raise"
    allowed_domains = ["raise.com"]
    # required urls list
    start_urls = [
        "https://www.raise.com/buy-gift-cards"
    ]

    op1="./../Results/raise.csv"
    opfile = csv.writer(open(op1, 'w'), delimiter=',')
    opfile.writerow(["Store Name","Cash Back", "Url", "Category", ""])

    def parse(self,response):
      selec = Selector(response)
      url = "https://www.raise.com/buy-gift-cards?page="

      #f = open('resp.txt' , 'w')
      #f.write(response.body)

      tag_div_all = selec.xpath('//nav[@class="pagination pagination-centered"]//li[4]/a/text()').extract()[0]
      total_pages = re.search(r"[0-9][0-9][0-9]|[0-9][0-9]|[0-9]",tag_div_all,re.I).group()

      count = 0
      for alpha in range(1,int(total_pages)+1):
        url_new = url + str(alpha)
        yield Request(url_new, callback=self.parse_page_1, dont_filter = True)

    def parse_page_1(self,response):

      selec = Selector(response)

      tag_div_all = selec.xpath('//div[@class="row-fluid"]//li[@class="product-source"]').extract()

      count = 0
      for tag_tr in tag_div_all:

        tag_tr =  tag_tr.encode('utf-8', 'ignore').strip()
        #print tag_tr

        store_name = '' ; link = ''
        if re.search(r"href=\".*?</a>",tag_tr,re.I|re.S):
          store_name = re.search(r"href=\".*?</a>",tag_tr,re.I|re.S).group()

          link = re.search(r"\".*?\"",store_name,re.I|re.S).group()
          link = re.sub(r'\"',"",link,re.I)
          link = "http://www.raise.com" + link
          #print link

          store_name = re.search(r"class=\"name\".*?<",store_name,re.I|re.S).group()
          store_name = re.search(r">.*?<",store_name,re.I|re.S).group()
          store_name = re.sub(r'>',"",re.sub(r'<',"",store_name,re.I))
          store_name = re.sub(r'\(In Store Only\)',"",re.sub(r'Gift Cards',"",store_name,re.I))
          store_name = re.sub(r'\(Online Only\)',"",re.sub(r'&amp;',"&",store_name,re.I))
          store_name = re.sub(r'^ ',"",re.sub(r'\(In Store Use Only\)',"",store_name,re.I))
          store_name = re.sub(r'^ ',"",re.sub(r' $',"",store_name,re.I))
          #print store_name

        cash_back = '' ; category = ''
        if re.search(r"class=\"info\">.*?<",tag_tr,re.I|re.S):
          cash_back = re.findall(r"class=\"info\">.*?<",tag_tr,re.I|re.S)[0]
          stock = re.search(r"\(.*?\)",cash_back,re.I|re.S).group()
          cash_back = re.search(r">.*?<",cash_back,re.I|re.S).group()
          cash_back = re.search(r"\).*?<",cash_back,re.I|re.S).group()
          cash_back = re.search(r"[0-9].*?<",cash_back,re.I|re.S).group()
          cash_back = re.sub(r'\)',"",re.sub(r'<',"",cash_back,re.I))
          cash_back = re.sub(r' $',"",re.sub(r'Off',"",cash_back,re.I))
          #print cash_back


        # Differentiating between absolute and percentage cash back
        if re.search(r"\$",cash_back,re.I):
          category = "Absolute Cash Back"
        elif re.search(r"%",cash_back,re.I):
          category = "Percentage Cash Back"
        else:
          category = "unknown"

        #------------ check for out of stock store names
        stock = re.sub(r'\(',"",re.sub(r'\)',"",stock,re.I))
        if stock != "0":
          self.opfile.writerow([store_name,cash_back,link,category])

