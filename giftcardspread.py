from scrapy.selector import Selector
from scrapy.spider import BaseSpider
from scrapy.http import Request
from scrapy.http import FormRequest
import time
import datetime
import re
import csv


class Fat_Wallet(BaseSpider):
    # name of spider used to run the script
    name = "giftcardspread"
    allowed_domains = ["giftcardspread.com"]
    # required urls list
    start_urls = [
        "https://giftcardspread.com/buy.aspx"
    ]

    op1="./../Results/giftcardspread.csv"
    opfile = csv.writer(open(op1, 'w'), delimiter=',')
    opfile.writerow(["Store Name","Cash Back", "Url", "Category", ""])

    def parse(self,response):
      selec = Selector(response)

      #f = open('resp.txt' , 'w')
      #f.write(response.body)

      tag_div_all = selec.xpath('//span//li').extract()

      count = 0
      for tag_tr in tag_div_all:

        tag_tr =  tag_tr.encode('utf-8', 'ignore').strip()
        #print tag_tr

        store_name = '' ; link = ''
        if re.search(r"href=\".*?</a>",tag_tr,re.I|re.S):
          store_name = re.search(r"href=\".*?</a>",tag_tr,re.I|re.S).group()

          link = re.search(r"\".*?\"",store_name,re.I|re.S).group()
          link = re.sub(r'\"',"",link,re.I)
          link = "https://giftcardspread.com/" + link
          #print link

          store_name = re.search(r"href=\".*</a>",tag_tr,re.I|re.S).group()
          store_name = re.sub(r'^href',"",store_name,re.I)
          store_name = re.search(r"href=\".*</a>",store_name,re.I|re.S).group()
          store_name = re.search(r">.*?\(",store_name,re.I|re.S).group()
          store_name = re.sub(r'>',"",re.sub(r'\(',"",store_name,re.I))
          store_name = re.sub(r'&amp;',"&",store_name,re.I)
          store_name = re.sub(r'\"',"",re.sub(r'\"',"",store_name,re.I))
          store_name = re.sub(r'^ ',"",re.sub(r' $',"",store_name,re.I))
          #print store_name


        cash_back = '' ; category = ''
        if re.search(r"<span .*?</span>",tag_tr,re.I|re.S):
          cash_back = re.findall(r"<span .*?</span>",tag_tr,re.I|re.S)[0]
          cash_back = re.search(r">.*?<",cash_back,re.I|re.S).group()
          cash_back = re.sub(r'>',"",re.sub(r'<',"",cash_back,re.I))
          cash_back = re.sub(r'OFF',"",cash_back,re.I)
          cash_back = re.sub(r'^ ',"",re.sub(r' $',"",cash_back,re.I))
          cash_back = re.sub(r' ',"",cash_back,re.I)
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

