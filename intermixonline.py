# coding: utf-8
'''
@author: Zahin
'''

from scrapy.selector import Selector
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import Rule
from scrapyproduct.spiderlib import SSBaseSpider
from scrapyproduct.items import ProductItem, SizeItem
from scrapy.http.request import Request
from scrapy.http import FormRequest
from scrapy import log
from scrapyproduct import toolbox
from scrapy.http.cookies import CookieJar

from scrapy.conf import settings

#settings.set('COOKIES_ENABLED', False, priority='cmdline')
#settings.set('COOKIES_DEBUG', True, priority='cmdline')
#settings.overrides['COOKIES_DEBUG'] = True

import time
import datetime
import urllib
import re
import copy
import json
import csv
import sys
import random
import os
import urlparse
import urllib

# This is the base class of Intermixonline crawler
class Intermixonline(SSBaseSpider):

    # name of spider used to run the script
    name = "intermix"
    long_name = "intermixonline.com"
    ajax_url = "http://www.intermixonline.com/categoryproductviewall.do?subCategoryCode="
    ajax_url_chic = "http://www.intermixonline.com/trendlooksandproducts.do?subCategoryId="
    base_url = "http://www.intermixonline.com"
    url_change_country = "http://www.intermixonline.com/basket.do?method=updateCountry&loc=landing"
    url_home = "http://www.intermixonline.com/home.do"

    gender = "women"

    #auto_register = True   # if more than 1 country then do not set it

    seen_prod_countries = dict() # Maintaining sets of seen products for each country

    spider_args = ""  # no spider arguments
    max_stock_level = 1  # if > 1 then register warehouselocation
    #spider.proxy_location = 'us'
    crawl_countries = 'all'  # input string-> 'us' or 'all'
    
    same_price_countries = ['at','be','cy','ee','fi','fr','gf','de','gr','gp','is',
                            'ie','it','lv','lu','mt','mq','mc','nl','pt','re','sk',
                            'si','es'
                        ]
    use_mini_item = 'yes' # input yes or no

    currency_lookup = {
    'AG':'USD','AW':'USD','AU':'AUD','AT':'EUR','BH':'BHD','BD':'BDT',
    'BB':'BBD','BE':'EUR','BZ':'BZD','BM':'USD','BO':'BOB','BR':'USD',
    'BN':'USD','BG':'BGN','KH':'KHR','CA':'CAD','KY':'KYD','CL':'CLP',
    'CN':'CNY','CO':'COP','CR':'CRC','HR':'HRK','CY':'EUR','CZ':'CZK',
    'DK':'DKK','DM':'USD','DO':'DOP','EC':'USD','EG':'EGP','SV':'USD',
    'EE':'EUR','FI':'EUR','FR':'EUR','GF':'EUR','DE':'EUR','GI':'GBP',
    'GR':'EUR','GD':'USD','GP':'EUR','GT':'GTQ','GG':'GBP','HN':'HNL',
    'HK':'HKD','HU':'HUF','IS':'EUR','IN':'INR','ID':'IDR','IE':'EUR',
    'IL':'ILS','IT':'EUR','JM':'JMD','JP':'JPY','JE':'GBP','JO':'JOD',
    'KR':'KRW','KW':'KWD','LV':'EUR','LI':'CHF','LT':'LTL','LU':'EUR',
    'MO':'GKD','MV':'MVR','MT':'EUR','MQ':'EUR','MX':'MXN','MC':'EUR',
    'MS':'USD','NL':'EUR','NZ':'NZD','NI':'NIO','NO':'NOK','OM':'OMR',
    'PK':'PKR','PA':'PAB','PY':'PYG','PE':'PEN','PH':'PHP','PL':'PLN',
    'PT':'EUR','QA':'QAR','RO':'RON','RU':'RUB','RE':'EUR','KN':'USD',
    'LC':'USD','SA':'SAD','SG':'SGD','SK':'EUR','SI':'EUR','ZA':'ZAR',
    'ES':'EUR','LK':'LKR','SE':'SEK','CH':'CHF','TW':'TWD','TH':'THB',
    'TT':'USD','TR':'TRY','TC':'USD','AE':'AED','GB':'GBP','US':'USD',
    }
    
    url_ignore_list = [
    ]
    
    def start_requests(self):
        meta = dict()
        meta['reuse_proxy'] = True
        language = 'en'
        check_us = True
        count = 0
        link = self.url_change_country
        for country_code in self.currency_lookup:
            if str(country_code).lower() in self.top5_countries:
                if count >= 0:# and count < 4: # countcheck >= 0
                    if str(country_code).lower() == 'us':
                        check_us = False

                    if self.crawl_countries.lower() == 'us':
                        count += 1
                        continue
                    country_code = country_code.lower()
                    #print "c_code:",country_code
                    currency = self.currency_lookup[str(country_code).upper()].upper()
                    
                    if country_code != 'gb' and country_code != 'jp' and country_code != 'us':
                        count += 1
                        continue
                    
                    self.seen_prod_countries[country_code] = set()
                    meta_new = copy.deepcopy(meta)
                    meta_new["country"] = country_code
                    meta_new["currency"] = currency
                    meta_new["language"] = language
                    meta_new['cookiejar'] = country_code
                    # Set dont_filter = True in first request to distinguish a country
                    yield Request(link, callback=self.change_country, dont_filter = True,
                    meta = meta_new
                    )
            count += 1
        
        # if US is not in the above country list but it present then
        if check_us:
            meta_new = copy.deepcopy(meta)
            currency = 'USD'
            country_code = 'us'
            self.seen_prod_countries[country_code] = set()
            meta_new["country"] = country_code
            meta_new["currency"] = currency
            meta_new["language"] = language
            meta_new['cookiejar'] = country_code
            yield Request(link, callback=self.change_country, dont_filter = True,
            meta = meta_new
            )

    def change_country(self,response):
        selec = Selector(response)
        response.meta['gender'] = 'Women'
        country_code = response.meta['country']
        currency = response.meta['currency']
        link = self.url_change_country

        request = FormRequest(url=link,
        formdata={'e4xCountry': country_code,
        'e4xCurrency': currency, 'submit': 'Update'},
        callback=self.parse_home_page, meta = copy.deepcopy(response.meta),
        dont_filter = False # keep it True bcaz each country's url is same but diff Form data
        )
        yield request
    
    def parse_home_page(self,response):
        
        selec = Selector(response)
        links = selec.xpath('//div[@class="leftCategoryNavContainer"]\
        //ul[@class="sf-menu"]//li/div')

        # Get links of all the major categories
        count = 0
        for link_cat in links:
            # 1='clothing';3='bags';4='shoes';5='accessories';sale=7
            if count >= 0:# and count <=4: # 3
                link = link_cat.xpath('./a/@href').extract()[0]
                category = link_cat.xpath('./a/text()').extract()[0]
                c_id = link_cat.xpath('./@id').extract()[0]
                c_id = c_id.replace('tnc_','')
                
                link_s = str(link.encode('utf-8','ignore'))
                if 'what+to+wear' in link_s or 'designer' in link_s or 'personal+styling' in link_s or\
                'in-the-mix' in link_s or 'stores' in link_s or 'blog' in link_s:
                    count += 1
                    continue
            
                category = str(category)
                response.meta["category"] = category ; response.meta["sub_cat"] = []
                response.meta["count_cat"] = count ; response.meta["cat_id"] = c_id
                response.meta['link_ref'] = link

                #print "categ->",category,link
                yield Request(link, callback=self.parse_category_page, dont_filter = True,
                meta = copy.deepcopy(response.meta)
                )

                response.meta['check_chic'] = False
                response.meta['ssub_cat'] = ''
                yield Request(link, callback=self.parse_overview_page, dont_filter = True,
                meta = copy.deepcopy(response.meta)
                )
            count += 1

    def parse_category_page(self,response):
        selec = Selector(response)
        cnt = response.meta["count_cat"]
        links = selec.xpath('//div[@class="leftCategoryNavContainer"]//ul[@class="sf-menu"]\
        //li['+re.escape(str(cnt+1))+']//ul//li/a')

        if len(links) > 0:
            count = 0
            for link_a in links:
                if count >= 0:# and count <=5: # totes=4; backpack=5; scarves=15
                    link = link_a.xpath('./@href').extract()[0]
                    sub_category = link_a.xpath('.//text()').extract()[0]
                    c_id = link_a.xpath('./@id').extract()[0]
                    # If all is present then it means that it is the main category
                    response.meta["sub_cat"] = sub_category
                    response.meta["cat_id"] = c_id ; response.meta['link_ref'] = link

                    response.meta['check_chic'] = False
                    sc_l = sub_category.lower()
                    if 'chic this week' in sc_l or 'style 3 ways' in sc_l or 'chic escape' in sc_l \
                    or 'resort report' in sc_l:
                        response.meta['check_chic'] = True
                    # Category 'SPRING LOOK BOOK' displays brands and not products hence ignored
                    if 'spring look book' in sc_l:
                        count += 1
                        continue
                    #print "sub category:",sub_category,link
                    yield Request(link, callback=self.parse_overview_page, dont_filter = False,
                    meta = copy.deepcopy(response.meta)
                    )
                count += 1

    # Overview page 60 items are displayed per page
    def parse_overview_page(self,response):
        selec = Selector(response)
        cat_id = response.meta["cat_id"]
        # to cater sub categories like scarf
        if selec.re(r'CurrentCat=([0-9]{2,8})'):
            c_id = selec.re(r'CurrentCat=([0-9]{2,8})')[0]
        elif toolbox.load_json_variable(selec,"currentSubCategoryCode"):
            c_id = toolbox.load_json_variable(selec,"currentSubCategoryCode")
        else:
            # response.meta["cat_id"] is used when request comes directly from the home page
            c_id = cat_id
        r = str(random.uniform(0,1))
        #print "categ id:",c_id
        # The Chic category demands separate ajax url request to deal with
        if response.meta['check_chic']:
            c_id_all = selec.xpath('//div[starts-with(@id,"DirectoryViewWrapper")]//div[@class="dirAction"]\
            //div[starts-with(@id,"viewAll")]/@id').re(r'viewAll_(.*)')
            ssub_cat_all = selec.xpath('//div[starts-with(@id,"DirectoryViewWrapper")]\
            //div[@class="productSubCategoryName"]//text()').extract()
            c = 0
            for c_id in c_id_all:
                if c >= 0:
                    link = self.ajax_url_chic + str(c_id) + "&ajaxRequest=true&r="+r
                    ssub_cat = str(ssub_cat_all[c].encode('utf-8','ignore'))
                    ssub_cat = self.remove_newlines(ssub_cat)
                    #print "cat id",ssub_cat,c_id,link
                    response.meta['ssub_cat'] = ssub_cat.decode('utf-8')
                    yield Request(link, callback=self.parse_subcategory_fullpage,
                    dont_filter = False, meta = copy.deepcopy(response.meta)
                    )
                    c += 1
        elif selec.xpath('//div[@id="master"]//div[starts-with(@id,"STR")]'):
            # Category 'How We Style > Spring trend report' is handled here
            links = selec.xpath('//div[@id="master"]//div[starts-with(@id,"STR")]')
            c = 0
            for link_a in links:
                if c >= 0:
                    link = link_a.xpath('.//a/@href').extract()[0]
                    ssub_cat = re.search(r'.*\/(.*?)\.',link).group(1)
                    ssub_cat = ssub_cat.replace('+',' ')
                    link = link.replace('\n','')
                    link = self.base_url + link if 'http' not in link else link
                    response.meta['ssub_cat'] = ssub_cat
                    response.meta['r'] = r
                    yield Request(link, callback=self.parse_sub_subcategory_page,
                    dont_filter = False, meta = copy.deepcopy(response.meta)
                    )
                c += 1
        elif selec.xpath('//div[@id="nDiv"]//div[starts-with(@class,"directoryProduct")]'):
            ref_link = response.url
            response.meta['ssub_cat'] = ''
            for pg in range(1,14): #14 handle callback ajax pages How We Look category ; 8 per page
                link = re.search(r'.*?\?',ref_link).group() + 'filterCategoryId='+c_id+'&page='+str(pg)
                yield Request(link, callback=self.parse_subcategory_fullpage,
                dont_filter = True, meta = copy.deepcopy(response.meta)
                )
        else:
            response.meta['ssub_cat'] = ''
            for pg in range(1,11): #11 handle callback ajax 10 pages ; 60 per page
                link = self.ajax_url+str(c_id)+"&ajaxRequest=true&r="+r+"&page="+str(pg)
                #print "overview ajax link:",link
                yield Request(link, callback=self.parse_subcategory_fullpage,
                dont_filter = False, meta = copy.deepcopy(response.meta)
                )
            #headers = {"Referer": response.url,
            #"X-Requested-With": "XMLHttpRequest"},

    def parse_sub_subcategory_page(self,response):
        # Category 'How We Style > Spring trend report' is handled here
        selec = Selector(response)
        #r = str(random.uniform(0,1))
        r = response.meta['r']
        if selec.re("id=\"DirGridCat_(.*)\""):
            c_id = selec.re("id=\"DirGridCat_(.*)\"")[0]
            for pg in range(1,10): #10 handle callback ajax pages 60 per page
                link = self.ajax_url+str(c_id)+"&ajaxRequest=true&r="+r+"&page="+str(pg)
                #print "subsub",link
                yield Request(link, callback=self.parse_subcategory_fullpage,
                dont_filter = False, meta = copy.deepcopy(response.meta)
                )

    def parse_subcategory_fullpage(self,response):
        selec = Selector(response)
        links = selec.xpath('//div[starts-with(@id,"nDiv")]//div[@class="directoryProductRow2"]/a/@href').extract()
        sku_all = links
        if len(sku_all) == 0:
            #links = selec.xpath('//div[starts-with(@id,"all")]//div[@class="thumbdiv"]//a/@href').extract()
            sku_all = selec.xpath('//div[starts-with(@id,"all")]//div[@class="thumbdiv"]//a//img//@src').extract()
        if len(links) == 0:
            links = selec.xpath('//div[starts-with(@id,"all")]//div[@class="thumbInfo"]\
            //div[@class="thumbheader"]//a//@href').extract()

        c_code = response.meta['country']
        #print "total",response.meta['sub_cat'],response.meta['ssub_cat'],len(links)
        count = 0  # the main problem arises when the category gets mixed up
        for link in links:
            if count >= 0:
                link = self.base_url + link if 'http' not in link else link
                if link in self.url_ignore_list:
                    count += 1
                    continue
                #print "prod url",str(count),":",link
                base_sku = str(sku_all[count].encode('utf-8','ignore').strip())
                if re.search(r'Intermix\/(.*?)\?',base_sku,re.I):
                    base_sku = re.search(r'Intermix\/PROD_(.*?)_',base_sku,re.I).group(1)
                    #base_sku = re.sub(r'PROD_','',base_sku,re.I)
                    #base_sku = re.sub(r'_[0-9]{2,6}$','',base_sku,re.I)
                elif selec.xpath('//div[starts-with(@id,"nDiv")]//div[@class="directoryProductRow2"]/a/img/@id'):
                    b = selec.xpath('//div[starts-with(@id,"nDiv")]//div[@class="directoryProductRow2"]/a/img/@id')
                    base_sku = b.re(r'.*_(.*)')[count]
                # To keep base_sku consistent across different categories
                base_sku = base_sku[:10]

                category = response.meta["category"]
                sub_cat = response.meta["sub_cat"]
                ssub_cat = response.meta['ssub_cat']
                gender = response.meta['gender']

                link_ref = response.meta['link_ref']

                if len(sub_cat) > 0:
                    if len(ssub_cat) > 0:
                        cat_iden = [gender.lower()] + [category.lower()] + [sub_cat.lower()] + [ssub_cat.lower()]
                        cat_names = [gender.title()] + [category.title()] + [sub_cat.title()] + [ssub_cat.title()]
                    else:
                        cat_iden = [gender.lower()] + [category.lower()] + [sub_cat.lower()]
                        cat_names = [gender.title()] + [category.title()] + [sub_cat.title()]
                else:
                    cat_iden = [gender.lower()] + [category.lower()]
                    cat_names = [gender.title()] + [category.title()]

                if self.use_mini_item.lower() == "yes":
                    # create a mini item for every product
                    mini_prod = ProductItem()
                    mini_prod['base_sku'] = base_sku
                    mini_prod['category_identifiers'] = cat_iden
                    mini_prod['category_names'] = cat_names
                    mini_prod['country_code'] = response.meta['country']
                    mini_prod["language_code"] = response.meta["language"]
                    mini_prod['url'] = link
                    mini_prod['referer_url'] = response.url
                    yield mini_prod

                # If a product base_sku is already scraped for any country
                # then it's detail page is not requested
                if base_sku in self.seen_prod_countries[c_code]:
                    count += 1
                    continue
                self.seen_prod_countries[c_code].update({base_sku})

                response.meta["cat_iden"] = cat_iden ; response.meta["cat_names"] = cat_names
                response.meta["base_sku"] = base_sku

                #print "product link:",cat_iden,base_sku,link
                yield Request(link, callback=self.parse_product_page, dont_filter = False,
                meta = copy.deepcopy(response.meta)
                )
            count += 1
    
    def get_title(self,selec):
        title = '' ; brand = 'unknown'
        title = selec.xpath('//div[@class="contentContainer"]\
        //div[@itemprop="name"]//text()').extract()
        if selec.xpath('//div[@class="contentContainer"]\
            //div[@itemprop="brand"]//text()').extract():
            brand = selec.xpath('//div[@class="contentContainer"]\
            //div[@itemprop="brand"]//a//text()').extract()
            if len(brand) == 0:
                brand = selec.xpath('//div[@class="contentContainer"]\
                //div[@itemprop="brand"]//text()').extract()
        #print title
        return title, brand

    def get_sku(self,selec):
        sku = ''
        sku = selec.xpath('//div[@class="contentContainer"]\
        //div[@itemprop="productId"]/text()|\
        //div[@class="contentContainer"]//div[@class="productCode"]/text()\
        ').extract()[1]
        sku = re.sub(r'\n','',re.sub(r'\n','',str(sku),re.I))
        return sku
    
    def remove_newlines(self,string):
        string = string.replace('\t','')
        string = string.replace('\r','')
        string = string.replace('\n','')
        return string

    def get_price(self,selec):
        price = ''
        price = selec.xpath('//div[@class="contentContainer"]\
        //div[@class="productPrice"]//span[@class="pricewas"]//text()').extract()
        if not price:
            price = selec.xpath('//div[@class="contentContainer"]\
            //div[@class="productPrice"]//span[@id="productPricing"]//text()').extract()
        price_new = selec.xpath('//div[@class="contentContainer"]\
        //div[@class="productPrice"]//span[@class="pricesale"]//text()').extract()
        if not price_new:
            price_new = selec.xpath('//div[@class="contentContainer"]\
            //div[@class="productPrice"]//span[@id="productPricing"]//text()').extract()
        price = [self.remove_newlines("".join(price))]
        price_new = [self.remove_newlines("".join(price_new))]
        if len(price_new) == 0:
            price_new = price
        if len(price) == 0:
            price = price_new
        return price,price_new

    def get_description(self,selec):
        desc = ''
        desc = selec.xpath('//div[@class="contentContainer"]\
        //div[@id="productDesc"]//div[@itemprop="description"]/text()').extract()
        
        if len(desc) == 0:
            desc = "no description available"
        elif len(desc) == 1:
            try:
                desc_ = str(desc[0].encode('utf-8','ignore'))
                desc_ = desc_.replace('\r\n','')
                desc_ = desc_.replace('\t','')
                if len(desc_) == 0:
                    desc = 'no description available'
            except:
                log.msg('encoding description if not available')
        return desc

    def get_keywords(self,selec):
        kw = selec.xpath('//meta[@name="keywords"]\
        /@content').extract()
        return kw
    
    def get_images_links(self,data):
        data = data.split(',')
        links = []
        uri_part = "http://intermix.scene7.com/is/image/"
        for link in data:
            link = link.split(';')[0]
            link = uri_part + link
            if 'http://intermix.scene7.com/is/image/' == link:
                continue
            links.append(link)
        return links
    
    def get_primary_image(self,selec):
        link = []
        link = selec.xpath('//div[@class="contentContainer"]\
        //div[@id="flyoutLargeImage_id"]//img/@src').extract()[0]
        link = re.sub(r'^//','',str(link),re.I)
        if 'http' not in link:
            link = "http://" + link
        link = [link]
        return link

    def size_info_object(self,size_infos, size, stock, c_code, price, price_new):        
        size_obj = SizeItem()
        size_obj['size_identifier'] = size
        size_obj['size_name'] = c_code.upper()+ ' ' + size
        size_obj["stock"] = stock
        size_obj["size_current_price_text"] = price_new
        size_obj["size_original_price_text"] = price
        size_infos.append(size_obj)
        return size_infos

    def get_size_infos(self,selec,price,c_code,price_new):
        color_codes = []; color_names = []; col_ids = []
        size_infos_dict = dict(); check_pps_dict = dict()
        # sizes = selec.xpath('//div[starts-with(@class,"pdpRight")]\
        # //div[@class="rowRight"]//span/@alt').extract()

        # menu_objects contains sizes and color information
        # There is no menuObject if the product is not available
        if selec.re('buildDependentOptionMenuObjects\((.*?)\)'):
            menu_objects = selec.re('buildDependentOptionMenuObjects\((.*?)\)')[0]
            menu_objects = re.sub('\\\/','/',menu_objects)
            menu_objects = toolbox.load_javascript(menu_objects)
            # size_id and size lookup
            size_lookup = dict()
            aOptionTypes = menu_objects['aOptionTypes']
            options = aOptionTypes['1']['options']
            for op in options:
                sz = options[op]['sOptionName']
                sz_id = options[op]['iOptionPk']
                size_lookup[sz_id] = sz
            aOptionSkus = menu_objects['aOptionSkus']

            color_codes_t = selec.xpath('//div[starts-with(@class,"pdpRight")]\
            //img[starts-with(@class,"swatch")]')

            for code in color_codes_t:
                # color code is contained in onclick class
                color_code = code.xpath('./@onclick').re('changeAltImages\(.*?,\'(.*?)\'\)')[0]
                color_codes.append(color_code)
                color_name = code.xpath('./@title').extract()[0]
                color_names.append(color_name)
                col_id = code.re('swatchClicked\((.*?)\)')[0]
                col_ids.append(col_id)
                size_infos = []; price_list = []
                check_pps = False # check if price varies per size
                for b in aOptionSkus:
                    a = aOptionSkus[b]
                    iSkuPk = a['iSkuPk']
                    price = a['skuPrice']
                    price_new = a['skuPrice']
                    inStock = a['inStock']
                    skuOptions = a['skuOptions']
                    iOptionPk = skuOptions['1']['iOptionPk']
                    iOptionPk_col = skuOptions['0']['iOptionPk']
                    size = size_lookup[iOptionPk]
                    if col_id == iOptionPk_col:
                        price_list.append(price_new)
                        #print iOptionPk,iOptionPk_col,inStock,iSkuPk,price_new,size
                        stock = 0
                        if str(inStock).lower() == 'true':
                            stock = 1
                        size_infos = self.size_info_object(size_infos, size, stock, c_code, price, price_new)

                price_list = list(set(price_list))
                if len(price_list) >= 1: # > 1
                    check_pps = True
                size_infos_dict[color_code] = size_infos
                check_pps_dict[color_code] = check_pps

        return size_infos_dict,color_codes,color_names,check_pps_dict
    
    def get_color_codes(self,selec):
        color_names = selec.xpath('//div[starts-with(@class,"pdpRight")]\
        //img[starts-with(@class,"swatch")]/@title').extract()
        color_codes_t = selec.xpath('//div[starts-with(@class,"pdpRight")]\
        //img[starts-with(@class,"swatch")]/@onclick')
        color_codes = []
        # color code is contained in onclick class
        for code in color_codes_t:
            code = code.re('changeAltImages\(.*?,\'(.*?)\'\)')[0]
            color_codes.append(code)
        return color_names,color_codes

    def parse_product_page(self,response):
        try:
            selec = Selector(response)
            url = response.url

            (title, brand) = self.get_title(selec)
            #sku = self.get_sku(selec)
            sku = response.meta["base_sku"]

            if len(title) > 0 and len(sku) > 0:
                log.msg(
                      "Parsing product page %s" %url, level=log.DEBUG
                )
                url = response.url
                prod = ProductItem()

                prod['language_code'] = response.meta['language']
                prod['category_identifiers'] = response.meta['cat_iden']
                prod['category_names'] = response.meta['cat_names']
                prod['country_code'] = response.meta['country']
                link_ref = response.meta['link_ref']
                prod['title'] = title
                prod['currency'] = response.meta['currency']
                (price, price_new) = self.get_price(selec)
                try:
                    if re.search(r'[0-9,.]',str(price_new),re.I):
                        pp = re.search(r'[0-9,.]{1,7}',str(price_s),re.I).group()[0]
                        if pp == '0' or pp == '.' or pp == ',':
                            prod['available'] = False
                            price_new = ['0']
                            price = ['0']
                        else:
                            pass
                    else:
                        prod['available'] = False
                        price = ['0']
                        price_new = ['0']
                except:
                    pass
                preorder = selec.xpath('//div[@class="productName badgeIds"]//text()').extract()
                if preorder:
                    prod['available'] = False if 'preorder' in preorder[0].lower() else True
                elif selec.xpath('//span[@class="messagealert"]'):
                    prod['available'] = False

                prod['new_price_text'] = price_new
                prod['full_price_text'] = price
                desc = self.get_description(selec)
                prod['description_text'] = desc
                prod['keywords'] = self.get_keywords(selec)
                
                prod['base_sku'] = sku
                prod['url'] = url
                prod['referer_url'] = response.request.headers.get('Referer', None)
                prod['brand'] = brand
                prod['gender_names'] = self.gender
                
                #color_names,color_codes = self.get_color_codes(selec)
                size_infos_dict,color_codes,color_names,check_pps_dict = \
                self.get_size_infos(selec,price,prod['country_code'],price_new)

                primary_img = self.get_primary_image(selec)

                img_ajax_link = "http://intermix.scene7.com/is/image/"
                body = selec.xpath('//body')
                apc = body.re("assetProductCode = \"(.*)\"")[0]
                ijl_ = img_ajax_link + apc + "?req=imageset,javascript"
                
                if color_names:
                    count = 0
                    for color_code in color_codes:
                        prod['size_infos'] = size_infos_dict[color_code]
                        # check if price varies per size of each product color
                        if check_pps_dict[color_code]:
                            prod['use_size_level_prices'] = True
                        prod_new = copy.deepcopy(prod)
                        sku_color = str(sku) + "_" + str(color_code)
                        prod_new['color_code'] = color_code
                        prod_new['color_name'] = color_names[count]
                        prod_new['sku'] = sku_color
                        prod_new['identifier'] = sku_color
                        c_c0 = color_codes[0]
                        ijl_ = re.sub(r'_[0-9]{3,4}'+"\?","_"+color_code+"?",ijl_)
                        ijl = ijl_
                        request = Request(
                        ijl, callback=self.parse_ajax_img_page, dont_filter = True
                        )
                        request.meta["prod_new"] = prod_new
                        request.meta['img_ajax_link'] = ijl
                        request.meta['primary_img'] = primary_img
                        request.meta['color_name'] = color_names[count]
                        request.meta['color_code'] = color_code
                        yield request
                        count += 1
                else:
                    prod['sku'] = sku
                    prod['identifier'] = sku
                    prod['available'] = False
                    prod_new = copy.deepcopy(prod)

                    request = Request(
                    ijl_, callback=self.parse_ajax_img_page, dont_filter = True
                    )
                    request.meta['primary_img'] = primary_img
                    request.meta['prod_new'] = prod_new
                    yield request

        except Exception as e:
            log.msg('Exception occured at %s' %url, level=log.ERROR)
            log.msg(str(e), level=log.ERROR)
            raise

    def parse_ajax_img_page(self,response):
        url = response.url
        try:
            selec = Selector(response)
            # img_ajax_link = response.meta['img_ajax_link']
            # color_name = response.meta['color_name']
            # color_code = response.meta['color_code']
            primary_img = response.meta['primary_img']
            prod_new = response.meta['prod_new']
            sku = prod_new['base_sku']
            if selec.re("\'(.*)\'"):
                data = selec.re("\'(.*)\'")[0]
                images_links = self.get_images_links(data)
                if images_links:
                    prod_new['image_urls'] = images_links
                else:
                    prod_new['image_urls'] = primary_img
            else:
                prod_new['image_urls'] = primary_img
            yield prod_new
            
        except Exception as e:
            log.msg('Exception occured at %s' %url, level=log.ERROR)
            log.msg(str(e), level=log.ERROR)
            raise
