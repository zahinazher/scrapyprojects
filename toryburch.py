# coding: utf-8        # for special characters in python code

# Fetches all products from all the available countries
from scrapy.selector import Selector
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import Rule
from scrapyproduct.spiderlib import SSBaseSpider
from scrapyproduct.items import ProductItem, SizeItem
from scrapy.http.request import Request
from scrapy import log
from scrapyproduct import toolbox

import time
import datetime
import urllib
import re
import copy
import json
import csv
import os
import urlparse
import urllib
#from scrapy.conf import settings

''' parameters changed to scrape data efficiently'''
#settings.overrides['CONCURRENT_REQUESTS_PER_DOMAIN'] = 1
#settings.overrides['CONCURRENT_REQUESTS_PER_IP'] = 1
#settings.overrides['DEPTH_PRIORITY'] = 1
#settings.overrides['SCHEDULER_DISK_QUEUE'] = 'scrapy.squeue.PickleFifoDiskQueue'
#settings.overrides['SCHEDULER_MEMORY_QUEUE'] = 'scrapy.squeue.FifoMemoryQueue'
#** For multithreading scraping comment out depth priority and mem queue ***#


# This is the base class of Toryburch crawler
class Toryburch(SSBaseSpider):

    # name of spider used to run the script
    name = "toryburch"
    long_name = "toryburch.com"
    base_url = "http://www.toryburch.com/tory"

    #auto_register = True  # if more than 1 country then do not set it
    spider_args = ""  # no spider arguments
    # if full stock level information available use max_stock_level=9999
    max_stock_level = 9999  # if > 0 then register warehouselocation

    crawl_countries = 'all'  # input string us or all
    use_mini_item = 'yes' # input yes or no

    seen_prod_countries = dict() # Maintaining sets of seen products for each country

    start_urls = [
    "http://www.toryburch.com/global/international-shipping.html"
    ]

    url_ignore_list = [
    "http://www.toryburch.com","http://www.toryburch.com/home/",
    "http://www.toryburch.com/home/view-all/"
    ]

    country_codes_lookup = {'argentina':'ar','united states':'us','it':'ITA'}
    currency_lookup = {'at':'EUR','us':'USD','uk':'GBP','de':'EUR','it':'EUR',
                      'fr':'EUR','jp':'JPY','eu':'EUR'}
    language_lookup = {'at':'de','us':'en','uk':'en','de':'de','eu':'en',
                      'it':'it','fr':'fr','jp':'jp'}

    country_codes_lukup_us_eu = {'argentina':'ar','australia':'au','canada':'ca',
    'chile':'cl','china':'cn', 'colombia':'co','costa-rica':'cr',
    'ecuador':'ec','el-salvador':'sv','india':'in','israel':'il',
    'jamaica':'jm','malta':'mt','new-zealand':'nz','norway':'no',
    'panama':'pa','switzerland':'ch','united-states':'us',
    'uruguay':'uy','belgium':'be','czech-republic':'cz',
    'denmark':'dk','estonia':'ee','finland':'fi',
    'greece':'gr','hungary':'hu','ireland':'ie','latvia':'lv',
    'luxembourg':'lu','netherlands':'nl','poland':'pl',
    'portugal':'pt','slovakia':'sk','slovenia':'si','spain':'es',
    'sweden':'se'
    }

    gender = "women"

    def parse(self,response):
        selec = Selector(response)

        country_urls = selec.xpath('//div[@id="content"]//div[@class="internal-container"]\
        //div[@class="flag-container"]//a/@href').extract()

        if len(country_urls) > 0:
            # Get all country names
            coun_names_usd = selec.xpath('//div[@id="content"]//div[@class="column"][1]\
            //div[@class="flag-container"]//div/@class').extract()
            coun_names_eur = selec.xpath('//div[@id="content"]//div[@class="column"][2]\
            //div[@class="flag-container"]//div/@class').extract()
            count = 0
            check_jp = False

            base_meta = dict()

            #country_urls_ = counry_urls[2:] + country_urls[:2]
            for link in country_urls:
                # at=0;uk=1;us=2;de=3;eu=4;fr=5;it=6;jp=7
                if count >= 0:
                    country_code = re.sub(r'/','',re.sub(r'\/','',link,re.I))
                    country_code = re.search(r'[a-z]{2}$',
                                  country_code,re.I).group().lower()

                    if str(country_code).lower() == 'jp':
                        check_jp = True
                    # print "Country Url:",country_code.upper(),link
                    currency = self.currency_lookup[country_code].upper()
                    language = self.language_lookup[country_code]

                    base_meta['country_code'] = country_code
                    base_meta['language'] = language
                    base_meta['currency'] = currency
                    base_meta['check_jp'] = check_jp
                    base_meta['cookiejar'] = country_code

                    # if country_code != 'eu' and country_code != 'us' and country_code != 'uk':
                    if country_code == 'ddus':
                        count += 1; continue

                    if country_code == 'eu' and self.crawl_countries.lower() == 'all':
                        coun_list_eu = []
                        for c_name_eur in coun_names_eur:
                            country_code_new = self.country_codes_lukup_us_eu[c_name_eur]
                            coun_list_eu.append(country_code_new)

                        toolbox.register_deliveryregion(
                        self,
                        country_code,
                        currency,
                        coun_list_eu,
                        link
                        )
                        toolbox.register_warehouselocation(self, country_code)

                    self.seen_prod_countries[country_code] = set()
                    if self.crawl_countries.lower() == 'all':
                        if str(country_code) == 'us':
                            pass
                        else:
                            toolbox.register_deliveryregion(
                            self,
                            country_code,
                            currency,
                            [],
                            link
                            )
                            # register as max_stock_level > 0
                            toolbox.register_warehouselocation(self, country_code)

                            yield Request(
                            url=link, callback=self.parse_main_page, dont_filter=True, meta=copy.deepcopy(base_meta)
                            )

                    if country_code == 'us':
                        coun_list_us = []
                        for c_name_usd in coun_names_usd:
                            country_code_new = self.country_codes_lukup_us_eu[c_name_usd]
                            coun_list_us.append(country_code_new)
                        toolbox.register_deliveryregion(
                        self,
                        country_code,
                        currency,
                        coun_list_us,
                        link
                        )
                        toolbox.register_warehouselocation(self, country_code)
                        # print country_code,link
                        yield Request(
                        url=link, callback=self.parse_main_page, dont_filter=True, meta=copy.deepcopy(base_meta)
                        )
                count += 1

    def parse_main_page(self,response):
        selec = Selector(response)
        check_jp = response.meta["check_jp"]

        # category_list is used to keep categories language independent across countries
        category_list = ['clothing','swim','shoes','handbags','accessories',
        'watches','home','beauty','musthaves','gift-guide','sale']

        subcategory_escape_list = ['mini-bags','tech-accessories','small-accessories',
        'the-robinson-collection','the-thea-collection','crossbody-bags','flip-flops',
        'torys-shoe-guide','cold-weather','view-all']

        category_list_jp = ['new-arrivals','clothing','shoes','handbags','watches','Torys-Must-Haves']
        category_menu_jp = ['menu1','menu2','menu3','menu4','menu0','menu0']

        if check_jp:
            category_list = category_list_jp
        c_categ = 0  # Category countcheck
        for cat in category_list:
            if c_categ >= 0:
                if check_jp:
                    menu_jp = str(category_menu_jp[c_categ])
                    links = selec.xpath('//div[@id="gNav"]//div[@id="'+re.escape(menu_jp)+'"]//li//a|\
                    //div[@id="gNav"]//li//a[contains(@href,"/'+str(cat)+'/")]')
                    # if not links:
                    #     links = selec.xpath('//div[@id="gNav"]//li//a[contains(@href,"/'+str(cat)+'/")]')
                    # sub_categ = selec.xpath('//div[@id="gNav"]//div[@id="'+re.escape(menu_jp)+'"]//li//a/text()|\
                    # //div[@id="gNav"]//li//a[contains(@href,"/'+str(cat)+'/")]/text()').extract()
                else:
                    links = selec.xpath('//div[@id="navigation"]//ul[starts-with(@class,"menu-category")]\
                    //li[@class="'+re.escape(str(cat))+'"]//li[contains(span/text(),"Categories")]//ul//li')
                    if not links: # to cater musthave category
                        links = selec.xpath('//div[@id="navigation"]//ul[starts-with(@class,"menu-category")]\
                    //li[@class="'+re.escape(str(cat))+'"]//ul//li')
                    # sub_categ = selec.xpath('//div[@id="navigation"]//ul[starts-with(@class,"menu-category")]\
                    # //li[@class="'+re.escape(str(cat))+'"]//ul//li/@class').extract()

                if 'home' in cat:
                    c_categ += 1; continue

                ### check if this works without the below lines
                # if cat != 'sale':
                #     while len(links) != len(sub_categ):
                #         sub_categ.append('')

                # links = links[:len(sub_categ)]

                check_watches = False
                # For primary categories like watches and beauty that do not have subcategories
                if len(links) == 0:
                    links = links = selec.xpath('//div[@id="navigation"]//ul[starts-with(@class,"menu-category")]\
                    //li[@class="'+re.escape(cat)+'"]//a')
                    if not links:
                        links = selec.xpath('//li[@class="'+re.escape(cat)+'"]//a')
                    sub_categ = ['']
                    check_watches = True
                # print c_categ,cat

                c_link = 0 # Subcategory count check
                for link_ in links:
                    if c_link >= 0:
                        if check_watches:
                            link = link_.xpath('./@href').extract()[0]
                            if sub_categ[c_link]:
                                sub_cat = str(sub_categ[c_link].encode('utf-8'))
                            else:
                                sub_cat = ''
                        else:
                            if check_jp:
                                if not link_.xpath('./@href'):
                                    continue
                                link = link_.xpath('./@href').extract()[0]
                                sub_cat = str((link_.xpath('.//text()').extract()[0]).encode('utf-8'))
                            else:
                                if not link_.xpath('.//a/@href'):
                                    continue
                                link = link_.xpath('.//a/@href').extract()[0]
                                if link_.xpath('./@class').extract():
                                    sub_cat = str((link_.xpath('./@class').extract()[0]).encode('utf-8'))
                                else:
                                    if link_.xpath('.//a/text()').extract():
                                        sub_cat = str((link_.xpath('.//a/text()').extract()[0]).encode('utf-8'))
                                    else:
                                        sub_cat = ''

                        link = link.encode('utf-8','ignore').strip()
                        sub_cat = re.sub(re.escape(str(cat))+'-','',sub_cat,re.I)
                        sub_cat = re.sub('-',' ',sub_cat,re.I)
                        sub_cat = self.remove_newlines(sub_cat)
                        if sub_cat in subcategory_escape_list:
                            sub_cat = [sub_cat]
                        else:
                            if cat == 'sale':
                                sub_cat = sub_cat.replace(' sale','')
                            sub_cat = sub_cat.split("-")
                            if len(sub_cat) > 0:
                                while '' in sub_cat:
                                    sub_cat.remove('')
                                if not check_watches:
                                    if not sub_cat:
                                        sub_cat = link_.xpath('./@title').extract()
                                if sub_cat:
                                    if 'home' in sub_cat[0].lower():
                                       c_link += 1; continue
                            else:
                                sub_cat = []
                        response.meta['check_pagin'] = False
                        if check_jp:
                            domain = "http://www.toryburch.jp"
                            response.meta['check_pagin'] = True
                            if 'http' not in link:
                                link = domain + link

                        if response.meta['country_code'] == 'fr':
                            if sub_cat:
                                # log.msg(sub_cat[0], level=log.ERROR)
                                sub_cat = [" ".join(sub_cat).decode('utf-8')]
                        response.meta["sub_cat"] = sub_cat
                        response.meta["categ"] = cat
                        # print " ",c_link,"sub categ:",sub_cat,link
                        yield Request(
                        link, callback=self.parse_overview_page, dont_filter=True, meta=copy.deepcopy(response.meta)
                        )
                    c_link += 1
            c_categ += 1

    def parse_overview_page(self,response):
        selec = Selector(response)
        check_jp = response.meta["check_jp"]
        c_code = response.meta["country_code"]

        if check_jp and response.meta['check_pagin']:
            links_p = selec.xpath('//div[@id="search-set"]//div[@class="pagerArea"]'\
            '//ul[starts-with(@class,"pageList")]//li//a//@href').extract()
            response.meta['check_pagin'] = False
            links_p = set(links_p)
            for link in links_p:
                if 'http' not in link:
                    link = "http://www.toryburch.jp" + link
                yield Request(
                link, callback=self.parse_overview_page, dont_filter=True, meta=copy.deepcopy(response.meta)
                )
        links = selec.xpath('//div[@class="product producttile"]//div[@class="name"]//a/@href').extract()

        # extract skus from image urls for Japan
        img_links = selec.xpath('//div[@class="product producttile"]\
        //div[@class="image"]//div[@class="productimage"]//img/@data-src').extract()

        if len(links) > 0:
            count = 0
            price_ref = selec.xpath('//div[@id="search"]//div[@class="product producttile"]//div[@class="price"]\
            //div[@class="salesprice"]/text()').extract()
            price_ref_jp = selec.xpath('//div[@id="search-set"]//div[@class="product producttile"]//div[@class="price"]\
            //div[@class="salesprice"]//i//text()').extract()

            sku_all = selec.xpath('//body')
            sku_all = sku_all.re("ac.pi\({id:\'(.*)\'}\)")

            check = False
            if len(sku_all) == 0:
                check = True

            # Iterates over second hierarchy
            for link in links:
                if count >= 0:
                    link_s = str(link.encode('utf-8','ignore').strip())

                    gender = self.gender
                    categ_ = response.meta["categ"]
                    sub_cat_ = response.meta["sub_cat"]
                    if check_jp:
                        if selec.xpath('//div[@id="search-set"]//div[@class="productresultareaheader"]//h1/text()'):
                                sub_cat = selec.xpath('//div[@id="search-set"]\
                                //div[@class="productresultareaheader"]//h1/text()').extract()[0]
                                cat_iden = [gender] + [categ_] + [sub_cat]
                        else:
                            cat_iden = [gender] + [categ_]
                    else:
                        if len(sub_cat_) > 0:
                            cat_iden = [gender] + [categ_] + sub_cat_
                        else:
                            cat_iden = [gender] + [categ_]
                    response.meta["categ_iden"] = cat_iden

                    if check: # if skus cannot be fetched thru ac.pi
                        if check_jp:    # if country is Japan
                            img_link = img_links[count]
                            try:
                                sku = str(img_link.encode('utf-8','ignore').strip())
                                if re.search(r'product\/.*?\/',sku,re.I):
                                    sku = re.search(r'product\/.*?\/',sku,re.I).group()
                                    base_sku = re.sub(r'product','',re.sub(r'\/','',sku,re.I))
                                    #print "SKU for Japan->",base_sku
                                    sku_all = img_links
                            except Exception as e:
                                log.msg("In case get base_sku from url",str(e), level=log.DEBUG)
                                sku_all = []
                        else:
                            if re.search(r'[0-9]{8,10}',link_s):
                                base_sku = re.search(r'[0-9]{8,10}',link_s).group()
                            elif re.search(r'dwvar_(.*?)_',link_s):
                                base_sku = re.search(r'dwvar_(.*?)_',link_s).group(1)
                            else:
                                count += 1; continue
                    else:
                        base_sku = sku_all[count]
                    base_sku = base_sku.lower()

                    if self.use_mini_item.lower() == "yes":
                        # create a mini item for every product
                        if check_jp:
                            domain = "http://www.toryburch.jp"
                            link_ = domain + link
                        else:
                            link_ = link
                        mini_prod = ProductItem()
                        mini_prod['base_sku'] = base_sku
                        mini_prod['category_identifiers'] = cat_iden
                        mini_prod['category_names'] = cat_iden
                        mini_prod['country_code'] = c_code
                        mini_prod['language_code'] = response.meta['language']
                        mini_prod['url'] = link_
                        mini_prod['referer_url'] = response.url
                        yield mini_prod

                    response.meta["base_sku"] = base_sku

                    # If a product base_sku is already scraped for any country then it's detail page is not requested
                    if base_sku in self.seen_prod_countries[c_code]:
                        count += 1; continue
                    self.seen_prod_countries[c_code].update({base_sku})

                    if check_jp:
                        domain = "http://www.toryburch.jp"
                        link = domain + link
                        # print "url 4 Japan:",base_sku,link
                        response.meta["price_ref"] = 'NA'
                        response.meta["size_infos"] = []
                        response.meta["size_infos_dict"] = []
                        response.meta["check_pps"] = False
                        yield Request(
                        link, callback=self.parse_product_page,dont_filter=True, meta=copy.deepcopy(response.meta)
                        )
                    else:
                        # get quantity info from ajax callback
                        url = str(link.encode('utf-8').strip())

                        host = re.search(r'http:\/\/.*?\/',url).group()
                        host = re.sub(r'\/$','',host)
                        uri = selec.xpath('//head')
                        uri = uri.re("app.URLs.getVariants .*\"(.*)\"")[0]
                        link_q = host + uri + '?pid=' + base_sku + '&format=json'
                        response.meta["prod_link"] = link
                        if not price_ref:
                            response.meta["price_ref"] = 'NA'
                        else:
                            response.meta["price_ref"] = price_ref[count]

                        # print base_sku,cat_iden,'qlink '+link_q,'\nlink:',link
                        yield Request(
                        link_q, callback=self.parse_quantity_page, dont_filter=True, meta=copy.deepcopy(response.meta)
                        )
                count += 1

    def get_title(self,selec):
        title = selec.xpath('//div[@id="content"]//div[@itemprop="name"]/h1//text()|\
        //div[@id="content"]//div[contains(@class, "collectionName")]/text()|\
        //div[@id="detailTxt"]//dl[@class="itemDate"]//dt//text()').extract()
        while '' in title:
            title = title.remove('')
        return title

    def get_sku(self,selec,url):
        sku = selec.xpath('//div[@id="content"]//div[@class="panelContent"]\
        //div[@class="styleNum"]/span/text()').extract()
        if len(sku) > 0:
            sku = sku[0]
        else:
            url = url.encode('utf-8','ignore').strip()
            if re.search(r'[0-9]{8}',str(url),re.I):
                sku = re.search(r'[0-9]{8}',str(url),re.I).group()
        if len(sku) == 0: # for Japan
            sku = selec.xpath('//div[@id="detailTxt"]//div[@id="kihonTxt"]//p\
            //text()').extract()
            sku = sku[-1]
            sku = str(sku.encode('utf-8','ignore').strip())
            sku = re.sub(r'Style Number: ','',sku,re.I)
        return sku

    def get_price(self,selec):
        price_all = selec.xpath('//div[@id="content"]//div[starts-with(@class,"productdetailcolumn")]\
        //div[@class="price"][1]//div//span/text()').extract()
        if len(price_all) > 0:
            price_new = "-".join(price_all)
        else:
            # id detailTxt is for Japan
            price_new = selec.xpath('//div[@id="content"]//div[starts-with(@class,"productdetailcolumn")]\
            //div[@class="price"][1]//div[starts-with(@class,"salesprice")]/text()').extract()[:1]
            if not price_new:
                price_new = selec.xpath('//div[@id="detailTxt"]//dl[@class="itemDate"]//dd[1]\
                //span/text()').extract()[:1]
            if len(price_new) == 0:
                price_new = selec.xpath('//div[@id="detailTxt"]//dl[@class="itemDate"]\
                //dd[1]/text()').extract()[:1]
        price = selec.xpath('//div[@id="content"]//div[starts-with(@class,"productdetailcolumn")]\
        //div[@class="price"][1]//div[starts-with(@class,"standardprice")]/text()').extract()[:1]

        if not price:
            price = selec.xpath('//div[@id="content"]\
                //div[@class="price"][1]//div[starts-with(@class,"salesprice standard")]/text()').extract()[:1]
            if not price:
                price = selec.xpath('//div[@id="content"]\
                //div[@class="price"][1]//div[starts-with(@class,"standardprice")]/text()').extract()[:1]

            if not price_new:
                price_new = selec.xpath('//div[@id="content"]//div[@class="price"][1]\
                            //div[@itemprop="price"]/text()').extract()[:1]
            # print selec.xpath('//div[@id="content"]//div[@class="price"][1]\
            #                 //div[@itemprop="price"]/text()').extract()[:1]
        price_new = price if len(price_new) == 0 else price_new
        price = price_new if len(price) == 0 else price
        return price,price_new

    def remove_newlines(self,string):
        return (((string.replace('\t','')).replace('\r','')).replace('\n','')).replace('\r\n\t','')

    def get_category_list(self,selec):
        categ_list = []; n = 2
        categ = selec.xpath('//div[@id="content"]//span[@itemprop="breadcrumb"]\
        //a['+re.escape(str(n))+']/text()').extract()
        if len(categ) > 0:
            categ_s = categ[0].encode('utf-8','ignore').strip()
            if "home" in str(categ_s).lower():
                n = 3
                categ = selec.xpath('//div[@id="content"]\
                //span[@itemprop="breadcrumb"]//a['+re.escape(str(n))+']\
                /text()').extract()
                if len(categ) > 0:
                    categ = categ[0]

            n += 1
            categ = selec.xpath('//div[@id="content"]\
            //span[@itemprop="breadcrumb"]//a['+re.escape(str(n))+']\
            /text()').extract()
            if len(categ) > 0:
                categ = categ[0]
                categ_list.append(categ)
                n += 1
                categ = selec.xpath('//div[@id="content"]\
                //span[@itemprop="breadcrumb"]//a['+re.escape(str(n))+']\
                /text()').extract()
                if len(categ) > 0:
                    categ = categ[0]
                    categ_list.append(categ)
        return categ_list

    def get_description(self,selec):
        desc = selec.xpath('//div[starts-with(@class,"collapsibleDetails")]\
        //div[starts-with(@class,"detailsPanel")]//text()|\
        //div[@id="detailTxt"]//div[@id="kihonTxt"]//text()|\
        //div[@id="detailTxt"]//div[@id="sizeTxt"]//text()|\
        //div[@id="detailTxt"]//div[@id="sozaiTxt"]//text()').extract()
        if len(desc) == 0:
            desc = "no description available"
        elif len(desc) == 1:
            try:
                desc_ = str(desc[0].encode('utf-8','ignore'))
                desc_ = self.remove_newlines(desc_)
                if len(desc_) == 0:
                    desc = "no description available"
            except:
                log.msg('encoding description if not available')
        return desc

    def get_primary_image(self,selec):
        link = selec.xpath('//div[@id="content"]//div[@id="izView"]/img/@src').extract()
        if not link:
            link = selec.xpath('//div[@class="productimage-static"]//img[@itemprop="image"]//@src').extract()
        uri_part = "?op_sharpen=1&rgn=384,768,1920,1920&op_sharpen=1&fmt=jpeg"
        if link:
            link = [re.sub(r'\?.*',uri_part,link[0])]
        return link

    def get_images_links(self,data,img_ajax_link,color_code_curr):
        links = []
        base_url = re.search(r'.*image/',img_ajax_link).group()
        images = data['IMAGE_SET']
        images = images.split(',')
        count = 0

        # uri_part = "?op_sharpen=1&rgn=384,768,1920,1920&op_sharpen=1&fmt=jpeg"
        uri_part = "?$trb_pdp_main_v3$"
        for link in images:
            if count == 0:
                count += 1; continue
            link = link.split(';')[0]
            if not re.search(r'_%s_'%color_code_curr,link):
                count += 1; continue
            link = base_url + link + uri_part
            links.append(link)
            count += 1
        return links

    def get_images_links_jp(self,selec):
        links = selec.xpath('//div[@id="detailTxt"]//ul[@class="inlineList"][2]//li//img')
        links_jp = []; links_jp_dict = dict()
        for link_ in links:
            link = str(link_.xpath('.//@src').extract()[0].encode('utf-8','ignore').strip())
            link = re.sub(r'_[0-9]{2,4}x[0-9]{2,5}','',link,re.I)
            links_jp.append(link)

        links_one_prim = selec.xpath('//div[@id="detailTxt"]//ul[@class="inlineList"][3]//li//img')
        for link_ in links_one_prim:
            link = str(link_.xpath('./@src').extract()[0].encode('utf-8','ignore').strip())
            link = re.sub(r'_[0-9]{2,4}x[0-9]{2,5}','',link,re.I)
            if 'http' not in link and 'sysimg' in link:
                link = 'http://www.toryburch.jp' + link

            col_name = link_.xpath('.//@title').extract()[0].lower()
            links_jp_dict[col_name] = link
        return links_jp, links_jp_dict

    def get_images_per_color(self,images_link,color_code_curr,color_code):
        img_links = []
        for link in images_link:
            # print color_code,color_code_curr,link
            link = re.sub(r'_%s_'%color_code_curr,'_%s_'%color_code,link)
            link = re.sub(r'_%s\?'%color_code_curr,'_%s?'%color_code,link)
            img_links.append(link)
        return img_links

    def get_size_info(self,data,c_code,url):
        variations = data['variations']['variants']
        count = 0; pos_price = ''; color_list = []
        size_infos_dict = dict()
        price_list = [] # used to check if price varies per size
        check_pps = False # check if price varies per size

        for v in variations:
            ats = 0 ; size = '' ; price = '0'; col = 'nocol'
            try:
                ats = v['ATS']
            except:
                log.msg(
                "ATS is not available for " + url , level=log.ERROR
                )
            try:
                col_code = v['attributes']['color']
                if col_code not in color_list:# create a new list if col code does not exist
                    color_list.append(col_code)
                    size_infos_dict[col_code] = list()
                size = v['attributes']['size']
            except:
                log.msg(
                "Size is not available for " + url , level=log.ERROR
                )
            try:
                price_new = v['pricing']['sale']
            except:
                price_new = ''
            try:
                price = v['pricing']['standard']
            except:
                price = ''

            if float(price) > 0:
                pos_price = price
            price_new = price if len(price_new) == 0 or price_new == '0.0' else price_new
            price = price_new if len(price) == 0 or price == '0.0' else price
            if price == '0.0':
                price = price_new = pos_price
            size_s = size.encode('utf-8','ignore').strip()

            if re.search(r'[a-z]{2}',str(size_s),re.I):
                pass
            else:
                if len(size_s) > 0:
                    size = str(size_s)

            size_obj = SizeItem()
            size_obj['size_identifier'] = size
            size_obj['size_name'] = str(c_code).upper() + ' ' + size
            size_obj["stock"] = int(ats)
            size_obj["size_current_price_text"] = price_new
            size_obj["size_original_price_text"] = price
            # print "color",col_code
            # print size_obj
            (size_infos_dict[col_code]).append(size_obj)
            price_list.append(price)
            count += 1
        price_list = list(set(price_list))
        if len(price_list) > 1:
            check_pps = True
        return (size_infos_dict,check_pps)

    def get_size_info_jp(self,data,price,price_old,stock):
        price = re.search(r'[0-9.,]{1,9}',price[0]).group()
        price_old = re.search(r'[0-9.,]{1,9}',price_old[0]).group()
        data = data['size']
        sizes = data.split('\n')
        size_infos = []
        if len(sizes) > 0:
            count = 0
            for size in sizes:
                size = re.search(r'\'>.*',size,re.I).group()
                size = re.sub(r'\'','',re.sub('>','',size,re.I))
                size_obj = SizeItem()
                size_obj['size_identifier'] = size
                size_obj['size_name'] = 'JP ' + size
                size_obj["stock"] = stock
                size_obj["size_current_price_text"] = price
                size_obj["size_original_price_text"] = price_old
                size_infos.append(size_obj)
                count += 1
        return size_infos

    def get_color_codes(self,selec,check_jp):
        color_names = [];color_codes = []; color_urls_dict = dict(); color_code_curr='999'; c_n_curr='nocolor'
        if check_jp:
            color_names = selec.xpath('//div[@id="condition"]\
            //div[@class="colorArea"]//select//option/text()').extract()
            color_codes = selec.xpath('//div[@id="condition"]\
            //div[@class="colorArea"]//select//option/@value').extract()
            colors = selec.xpath('//div[@id="condition"]\
            //div[@class="colorArea"]//select//option/@value').extract()
        else:
            colors = selec.xpath('//div[@id="content"]//div[@class="productattributes"]')[:1]
            colors = colors.xpath('.//ul[@id="swatchesselect"]//li')
            for color in colors:
                color_code = color.xpath('.//div/text()').extract()[0]
                color_name = color.xpath('.//span/text()').extract()[0]
                color_url = color.xpath('.//a/@name').extract()[0]
                select = color.xpath('./@class').extract()[0]
                color_codes.append(color_code)
                color_names.append(color_name)
                color_urls_dict[color_code] = color_url
                if 'selected' in select:
                    color_code_curr = color_code
        return color_names,color_codes,color_urls_dict,color_code_curr,c_n_curr

    def get_keywords(self,selec):
        return selec.xpath('//meta[@name="keywords"]/@content').extract()

    def parse_quantity_page(self,response):
        selec = Selector(response)
        link = response.meta['prod_link']
        if not selec.xpath('//body//div'): # sizes are present
            data = toolbox.load_javascript(response.body)
            c_code = response.meta['country_code']
            check_jp = response.meta['check_jp']
            (size_infos_dict,check_pps) = self.get_size_info(data,c_code,response.url)
            response.meta["size_infos_dict"] = size_infos_dict
            response.meta["check_pps"] = check_pps
            yield Request(
            link, callback=self.parse_product_page, dont_filter=True, meta=copy.deepcopy(response.meta)
            )
        else:
            response.meta["size_infos_dict"] = []
            response.meta["check_pps"] = False
            yield Request(
            link, callback=self.parse_product_page, dont_filter=True, meta=copy.deepcopy(response.meta)
            )

    def parse_product_page(self,response):
        url = response.url

        try:
            log.msg(
                  "Parsing product page " + response.url, level=log.DEBUG
            )

            selec = Selector(response)
            title = self.get_title(selec)
            sku = response.meta["base_sku"]

            if len(title) > 0:
                prod = ProductItem()
                prod['language_code'] = response.meta['language']
                c_code = response.meta['country_code']
                prod['country_code'] = c_code
                prod['currency'] = response.meta['currency']
                price_ref = response.meta["price_ref"]
                categ_iden = response.meta["categ_iden"]
                size_infos_dict = response.meta['size_infos_dict']
                check_pps = response.meta["check_pps"]
                # if check_pps:
                #     prod['use_size_level_prices'] = True

                check_jp = response.meta['check_jp']
                prod['title'] = title
                price_old,price = self.get_price(selec)

                try:
                    if not check_jp:
                        price_s = price[0].encode('utf-8','ignore').strip()
                        if re.search(r'[0-9]',str(price_s),re.I):
                            prod['new_price_text'] = price
                            prod['full_price_text'] = price_old
                            #prod['old_price_text'] = price
                        else:
                            price = price_old = [price_ref]
                            prod['available'] = False
                            prod['new_price_text'] = '0'
                    else:
                        prod['new_price_text'] = price
                        prod['full_price_text'] = price_old
                except Exception as e:
                    log.msg('price encoding for countries except Japan sku=%s url %s'%(sku,url), level=log.INFO)
                # For Japan
                if selec.xpath('//span[@class="sale-status"]').re('SOLD OUT'):
                    stock = 0 ;
                    prod["available"] = False
                    if 'new_price_text' not in prod:
                        prod['new_price_text'] = '0'
                else:
                    stock = 1

                desc = self.get_description(selec)
                prod['description_text'] = desc
                prod['keywords'] = self.get_keywords(selec)
                prod['base_sku'] = sku
                prod['url'] = url
                prod['referer_url'] = response.request.headers.get('Referer', None)
                prod['brand'] = "Tory Burch"

                categ_iden = categ_iden
                prod['category_identifiers'] = categ_iden
                prod['category_names'] = categ_iden
                # prod['gender_names'] = self.gender
                # prod['gender_identifiers'] = self.gender

                primary_image = self.get_primary_image(selec)

                color_names,color_codes,color_urls_d,color_code_curr,c_n_curr = self.get_color_codes(selec,check_jp)

                if c_code == 'uk':
                    sizes = selec.xpath('//div[contains(@class,"variantdropdown size")]//div//select//option//text()')[1:]
                    s_i_d = response.meta['size_infos_dict']
                    size_infos_dict_uk = dict(); check_us_size = False
                    for col in s_i_d:
                        c = -1; sz_obj_list = []
                        if check_us_size:
                            break
                        for sz in s_i_d[col]:
                            c += 1
                            if check_us_size:
                                break
                            for size in sizes:
                                # print size
                                # size = size_.xpath('.//text()')
                                if not size.re('(.*?) ') or not size.re('Size (.*)'):
                                    check_us_size = True; break
                                size_uk = size.re('(.*?) ')[0]
                                size_us = size.re('Size (.*)')[0]
                                if size_us == sz['size_identifier'].replace('UK ',''):
                                    response.meta['size_infos_dict'][col][c]['size_identifier'] = 'UK ' + size_uk
                                    response.meta['size_infos_dict'][col][c]['size_name'] = 'UK ' + size_uk
                                    sz['size_identifier'] = sz['size_name'] = 'UK ' + size_uk
                                    sz_obj_list.append(sz)
                                    break
                        if not check_us_size:
                            size_infos_dict_uk[col] = sz_obj_list
                    response.meta['size_infos_dict'] = size_infos_dict_uk

                body = selec.xpath('//body')
                # If image ajax callback url is present
                if body.re("var pViewerBaseUrl .*\"(.*)\""):
                    ajax_url = body.re("var pViewerBaseUrl .*\"(.*)\"")[0]
                    ajax_uri = body.re("pViewerImageUrl .*\"(.*)\"")[0]
                    img_ajax_link = ajax_url+ajax_uri+'_S'+'?req=imageset,json&callback=s7jsonResponse'

                    response.meta['size_infos_dict'] = size_infos_dict
                    response.meta["prod"] = prod
                    response.meta['img_ajax_link'] = img_ajax_link
                    response.meta['primary_image'] = primary_image
                    response.meta['color_codes'] = color_codes
                    response.meta['color_names'] = color_names
                    response.meta['color_code_curr'] = color_code_curr
                    response.meta['color_urls_d'] = color_urls_d
                    # img_ajax_link = "http://s7d5.scene7.com/is/image/ToryBurchLLC/TB_56NF01_000_S?req=imageset,json&callback=s7jsonResponse"
                    yield Request(img_ajax_link, callback=self.parse_image_ajax_page, dont_filter=True,
                    meta=copy.deepcopy(response.meta)
                    )
                else: # For JP
                    # pViewerBaseUrl var is not present in JP website
                    if check_jp:
                        links_img, links_img_dict = self.get_images_links_jp(selec)
                        #prod["size_infos"] = self.get_size_info_jp(selec,price)
                        if re.search(r'shop_product_id\/.*?\/',str(url)):
                            shop_id = re.search(r'shop_product_id\/.*?\/',str(url)).group()
                            shop_id = re.sub(r'shop_product_id','',re.sub(r'\/','',shop_id,re.I))
                        elif re.search(r'shop_product_id\/[0-9]{4,7}',str(url)):
                            shop_id = re.search(r'shop_product_id\/[0-9]{4,7}',str(url)).group()
                            shop_id = re.sub(r'shop_product_id','',re.sub(r'\/','',shop_id,re.I))
                        url_jp = "http://www.toryburch.jp/"
                        link_size_jp = url_jp + "item/ajax_input_color/shop_product_id/"
                        link_size_jp = link_size_jp + shop_id + "/color_id/"
                        #print "shop_prod_id:",shop_id
                    else:
                        prod['image_urls'] = primary_image

                    if color_names:
                        count = 0
                        for color_code in color_codes:
                            prod_new = copy.deepcopy(prod)
                            # if count != 0:
                            #     if links_img_dict:
                            #         prod_new['image_urls'] = links_img_dict[color_names[count].lower()]
                            #     else:
                            #         prod_new['image_urls'] = links_img
                            # else:
                            #     prod_new['image_urls'] = links_img
                            if len(color_codes) == 1:
                                prod_new['image_urls'] = links_img
                            else:
                                prod_new['image_urls'] = links_img_dict[color_names[count].lower()]
                            if isinstance(size_infos_dict, dict):
                                size_infos = size_infos_dict[color_code]
                            else:
                                size_infos = size_infos_dict
                            prod["size_infos"] = size_infos
                            prod['use_size_level_prices'] = True if size_infos else False
                            sku_color = sku + '_' + color_code
                            prod_new['color_code'] = color_code
                            prod_new['color_name'] = color_names[count]
                            prod_new['sku'] = sku_color
                            prod_new['identifier'] = sku_color
                            count += 1
                            if check_jp:
                                link = link_size_jp + color_code
                                #print "url_size_ajax_jp",link
                                response.meta["prod_new"] = prod_new
                                response.meta["stock"] = stock
                                yield Request(link, callback=self.parse_size_ajax_page_jp, dont_filter=True,
                                meta=copy.deepcopy(response.meta)
                                )
                            else:
                                yield prod_new
                    else:
                        if isinstance(size_infos_dict, dict):
                            size_infos = size_infos_dict
                            if len(size_infos) == 0:
                                size_infos = []
                            else:
                                size_infos = size_infos_dict.popitem()[1]
                        else:
                            size_infos = []
                        prod["size_infos"] = size_infos
                        prod['use_size_level_prices'] = True if size_infos else False
                        prod['image_urls'] = links_img
                        prod['sku'] = sku
                        prod['identifier'] = sku
                        yield prod
        except Exception as e:
            log.msg('Exception occured at %s' %url, level=log.ERROR)
            log.msg(str(e), level=log.ERROR);raise

    def parse_size_ajax_page_jp(self,response):
        url = response.url
        try:
            selec = Selector(response)
            prod_new = response.meta['prod_new']
            price = prod_new['new_price_text']
            price_old = prod_new['full_price_text']
            stock = response.meta['stock']
            if selec.re("\{(.*)\}"):
                data = selec.re("\{(.*)\}")[0]
                data = re.sub(r'<a .*?>','',re.sub(r'<a .*?>','',str(data),re.I))
                data = toolbox.load_javascript('{'+str(data)+'}')
                size_infos = self.get_size_info_jp(data,price,price_old,stock)

                prod_new['size_infos'] = size_infos
                prod_new['use_size_level_prices'] = True if size_infos else False
            yield prod_new
        except Exception as e:
            log.msg('Exception occured at JP size func %s' %url, level=log.ERROR)
            log.msg(str(e), level=log.ERROR)

    def parse_image_ajax_page(self,response):
        url = response.url
        try:
            selec = Selector(response)
            prod = response.meta['prod']
            sku = prod['base_sku']
            img_ajax_link = response.meta['img_ajax_link']
            primary_image = response.meta['primary_image']
            color_names = response.meta['color_names']
            color_codes = response.meta['color_codes']
            color_code_curr = response.meta['color_code_curr']
            color_urls_d = response.meta['color_urls_d']
            size_infos_dict = response.meta['size_infos_dict']

            images_link = []
            if selec.re("\{(.*)\}"):
                data = selec.re("\{(.*)\}")[0]
                data = toolbox.load_javascript('{'+str(data)+'}')
                images_link = self.get_images_links(data,img_ajax_link,color_code_curr)
            else:
                images_link = primary_image
            if len(images_link) == 0:
                images_link = primary_image
            else: # add primary image if not already present in image_urls set
                images_link += primary_image if primary_image[0] not in images_link else []
                pr_i = re.sub(r'\?.*',"",primary_image[0])
                images_link += primary_image if pr_i not in images_link else []

            prod['image_urls'] = images_link

            if color_names:
                count = 0
                for color_code in color_codes:
                    prod_new = copy.deepcopy(prod)
                    if color_code_curr != color_code:
                        prod_new['image_urls'] = self.get_images_per_color(images_link,color_code_curr,color_code)
                        prod_new['url'] = color_urls_d[color_code]
                    else:
                        prod_new['image_urls'] = images_link

                    if isinstance(size_infos_dict, dict):
                        size_infos = prod_new["size_infos"] = size_infos_dict[color_code]
                    else:
                        size_infos = size_infos_dict
                    prod_new['use_size_level_prices'] = True if size_infos else False
                    sku_color = sku + '_' + color_code
                    prod_new['color_code'] = color_code
                    prod_new['color_name'] = color_names[count]
                    prod_new['sku'] = sku_color
                    prod_new['identifier'] = sku_color
                    count += 1
                    yield prod_new
            else:
                if isinstance(size_infos_dict, dict):
                    size_infos = size_infos_dict
                    if len(size_infos) == 0:
                        size_infos = []
                    else:
                        if prod['new_price_text'] == '0':
                            return
                        size_infos = size_infos_dict.popitem()[1]
                else:
                    size_infos = []
                prod["size_infos"] = size_infos
                prod['use_size_level_prices'] = True if size_infos else False
                prod['sku'] = sku
                prod['identifier'] = sku
                yield prod
        except Exception as e:
            log.msg('Exception occured at %s sku:%s url %s' %(url,sku,prod['url']), level=log.ERROR)
            log.msg(str(e), level=log.ERROR);raise
