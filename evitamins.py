from scrapy.selector import HtmlXPathSelector
from scrapy.spider import BaseSpider
from scrapy.http import Request
from scrapy.http import FormRequest
import re
import scrapy.log
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from priceplow.items import Product, ProductLink, ProductLoader
from priceplow.spiders.base import PricePlowSpider
from priceplow.utils import cached_property, ignored

from scrapy.conf import settings

"""
@author: Zahin
"""

"""settings.overrides['CONCURRENT_REQUESTS_PER_SPIDER'] = 1
#settings.overrides['CONCURRENT_REQUESTS_PER_DOMAIN'] = 1
settings.overrides['CONCURRENT_REQUESTS_PER_IP'] = 1
settings.overrides['SCHEDULER_DISK_QUEUE'] = 'scrapy.squeue.PickleFifoDiskQueue'
settings.overrides['SCHEDULER_MEMORY_QUEUE'] = 'scrapy.squeue.FifoMemoryQueue'
settings.overrides['WEBSERVICE_ENABLED'] = True"""


class E_vitamins(BaseSpider):
  name = "evitamins"
  store_id = 14
  allowed_domains = ["evitamins.com"]
  base_url = 'http://www.evitamins.com/viewalldepartments'
  url_view_items = 'http://www.evitamins.com/viewitems?l='

  def start_requests(self):
      """Generates the starting request(s) for the store spider to begin
      crawling product listings in 'discover' mode.
      """
      yield Request(self.base_url, callback=self.parse_brands)


  def parse_brands(self,response):

    lx = SgmlLinkExtractor(restrict_xpaths=('//td[@valign="top"]'), allow=('\S+\.com'), unique=True)
    links = lx.extract_links(response)
    brands_all = set(sorted(link.text for link in links))

    self.log(u'Extracted {} brands.'.format(len(brands_all)), scrapy.log.DEBUG)

    """Traverse through all the pages to get all products"""
    """brands_alphabets = ['A','B','C','D','E','F','G','H','I',
                        'J','K','L','M','N','O','P','Q','R',
                        'S','T','U','V','W','X','Y','Z']"""
    brands_alphabets = ['A']
    for alpha in brands_alphabets:
      yield Request(self.url_view_items + str(alpha), callback=self.items_list)

  def items_list(self,response):

    selec = HtmlXPathSelector(response)

    tag_td_all = selec.select('//td[@class="newsText"][2]//tr/td/a/@href').extract()

    count = 0
    for item_url in tag_td_all:
      if count == 0:
        yield Request(item_url, callback=self.items_list_refined)
      count += 1

  def items_list_refined(self,response):
      
    selec = HtmlXPathSelector(response)

    tag_td_all = selec.select('//tr//td[@class="gridProLinks"]/a/@href').extract()
    tag_td_all = set(tag_td_all)

    count = 0
    for product_url in tag_td_all:
      if count == 0:

        yield Request('http://www.evitamins.com/malic-acid-800-mg-natures-life-451#.Uqd2Mq7FsUQ', callback=self.get_product)
      count += 1

  def get_product(self,response):
    
    selec = HtmlXPathSelector(response)

    title = selec.select('//tr//td[@valign="top"]//div//h1[@class="h1productHead"]/text()').extract()[0]

    brand = selec.select('//tr//td[@valign="top"]//tr//td//a[starts-with(@style,"text-decoration")]/text()').extract()[0]

    if re.search(re.escape(str(brand)),title,re.I|re.S):
      title = title.replace(brand+' ',"")

    flavor = 'None'
    if re.search(r'\,.*?$',title,re.I|re.S):
      flavor = re.search(r'\,.*?$',title,re.I|re.S).group()
      flavor = flavor.replace(", ","")

      title = re.search(r'.*?\,',title,re.I|re.S).group()
      title = title.replace(",","")

    size_n_unit = selec.select('//tr//td[@valign="top"]//tr//td[contains(strong/text(), "Selected Size:")]/text()').extract()[0]

    size = '1' ; unit = 'item'
    if re.search(r"[0-9]{1,5}.*?[a-zA-Z]{1,10}",size_n_unit,re.I|re.S):
      size_unit = re.search(r"[0-9]{1,5}.*?[a-zA-Z]{1,10}",size_n_unit,re.I|re.S).group()
      size = re.search(r"[0-9]{1,5}",size_unit,re.I|re.S).group()

      unit = re.search(r"[a-zA-Z]{1,10}",size_unit,re.I|re.S).group()

    upc = 'None'
    upc_ = selec.select('//tr//td[@valign="top"]//tr//td//span[starts-with(@class,"size")]/span[contains(@itemprop,"")]/text()').extract()[0]
    if len(upc_) > 0:
      upc = upc_

    our_price = 'None'
    our_price_ = selec.select('//tr//td[@valign="top"]//tr//td//span[@itemprop="price"]/text()').extract()[0]
    if len(our_price_) > 0:
      our_price = our_price_
      our_price = our_price.replace("\n","")

    image_url = selec.select('//tr//td[@valign="top"]//span/a/@href').extract()[0]
    print image_url





