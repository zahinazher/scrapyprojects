from scrapy.selector import Selector
from scrapy import Spider
from scrapy.http import Request
from scrapy.http import FormRequest
from scrapy.http.cookies import CookieJar
import time
import datetime
import logging
import re
import csv
from scrapy.conf import settings
#settings.overrides['CONCURRENT_REQUESTS_PER_SPIDER'] = 1
#settings.overrides['CONCURRENT_REQUESTS_PER_DOMAIN'] = 1
settings.overrides['CONCURRENT_REQUESTS_PER_IP'] = 1
settings.overrides['SCHEDULER_DISK_QUEUE'] = 'scrapy.squeue.PickleFifoDiskQueue'
settings.overrides['SCHEDULER_MEMORY_QUEUE'] = 'scrapy.squeue.FifoMemoryQueue'
settings.overrides['WEBSERVICE_ENABLED'] = True


settings.overrides['SCHEDULER_DISK_QUEUE'] = 'scrapy.squeue.PickleFifoDiskQueue'

# Scrapy uses a LIFO queue for storing pending requests, which basically means that it crawls in DFO order
# Default encoding: 'utf-8'


op1="pentair.csv"
opfile = csv.writer(open(op1, 'w'), delimiter=',')
opfile.writerow(["JOB TITLE","JOB ID","JOB LOCATION","JOB SUMMARY","JOB REQUIREMENTS",""])

class Pentair_spider(Spider):
  name = "pentair"
  allowed_domains = ["careers.pentair.com"]
  start_urls = [
      "https://careers.pentair.com/psc/PNRP1PH/EMPLOYEE/HRMS/c/HRS_HRAM.HRS_CE.GBL"
  ]

  now = datetime.datetime.now()
  logging.basicConfig(filename='logs.log')
  logging.critical('Date: '+str(now))
  
  icsid = ''

  count_job_tot = 0
  count_p2 = -1 # id for each job, starts after 1 incr i.e 0

  total_job = 1

  def parse(self,response):
   selec = Selector(response)
   url = "https://careers.pentair.com/psc/PNRP1PH/EMPLOYEE/HRMS/c/HRS_HRAM.HRS_CE.GBL"
   yield Request(url, callback=self.parse_page_1, dont_filter = True)

  def parse_page_1(self,response):
    #f = open('resp.txt' , 'w')
    #f.write(response.body)
    selec = Selector(response)
    
    job_id_all = selec.xpath('//div/span/a[starts-with(@id,"POSTINGTITLE$")]').extract()
    #print "len(job_id_all)",len(job_id_all)

    icsid = selec.xpath('//input[@id="ICSID"]/@value').extract()[0]
    #print "icsid",icsid
    self.icsid = icsid
    
    url1 = "https://careers.pentair.com/psc/PNRP1PH/EMPLOYEE/HRMS/c/HRS_HRAM.HRS_CE.GBL"
    self.total_job = len(job_id_all)
    i = 0
    while (i < (len(job_id_all)*3.5)):
    #while (i<1):
      time.sleep(1.5)
      yield Request(url1, callback=self.parse_page_2, dont_filter = True)
      i += 1

  def parse_page_2(self,response):

    selec = Selector(response)
    icsid_new = selec.xpath('//input[@id="ICSID"]/@value').extract()[0]
    #print "icsid",icsid_new

    url2 = "https://careers.pentair.com/psc/PNRP1PH/EMPLOYEE/HRMS/c/HRS_HRAM.HRS_CE.GBL"

    self.count_p2 += 1

    if self.count_p2 >= 0:
      inaction = 'POSTINGTITLE$' + str(self.count_p2)
      #print inaction

      yield FormRequest(url=url2,
            formdata={
              'ICType':'Panel',
              'ICElementNum':'0',
              'ICAction':'POSTINGTITLE$' + str(self.count_p2),
              'ICXPos':'0',
              'ResponsetoDiffFrame':'-1',
              'TargetFrameName':'None',
              'ICFocus':'',
              'ICSaveWarningFilter':'0',
              'ICChanged':'-1',
              'ICResubmit':'1',
              'ICSID':self.icsid,
              'ICModalWidget':'0',
              'ICZoomGrid':'0',
              'ICZoomGridRt':'0',
              'ICModalLongClosed':'',
              'ICActionPrompt':'false',
              'ICFind':'',
              'ICAddCount':'',
              'HRS_CE_JO_EXT_I$hnewpers$0':'0|0|0|0|0|20|0#1|0|0|0|0|83|0#2|0|0|0|0|182|0#3|0|0|0|0|83|0#6|0|0|0|0|193|0#',
              'DERIVED_RESUME_LANGUAGE_CD':'ENG',
              'HRS_APPL_WRK_HRS_OPRNAME':'',
              'HRS_APPL_WRK_HRS_OPRPSWD':'',
              'HRS_APP_SRCHDRV_HRS_APP_KEYWRD':'',
              'HRS_APP_SRCHDRV_HRS_POSTED_WTN':'A'
              },
              callback=self.parse_page_3, dont_filter = True)

  def parse_page_3(self,response):

    #print "fetch" + str(self.count_job_tot)

    ####################Count check for total jobs###############
    if self.count_job_tot < self.total_job:
    ####################Count check for total jobs###############

      selec = Selector(response)

      # JOB ID
      job_id = ''
      job_id_ = selec.xpath('//div/span[starts-with(@id,"HRS_JO_WRK_HRS_JOB_OPENING_ID$")]/text()').extract()[0]
      if len(job_id_) > 0:
        job_id = job_id_
        #print job_id

      # JOB TITLE
      job_title = ''
      job_title_ = selec.xpath('//div/span[starts-with(@id,"HRS_JO_WRK_POSTING_TITLE$")]/text()').extract()[0]
      if len(job_title_) > 0:
        job_title = job_title_
        #print job_title

      # JOB LOCATION
      job_loc = ''
      job_loc_ = selec.xpath('//div/span[starts-with(@id,"HRS_CE_WRK2_HRS_CE_JO_LCTNS$")]/text()').extract()[0]
      if len(job_loc_) > 0:
        job_loc = job_loc_
        #print job_loc

      # JOB DESCRIPTION
      desc = ''
      job_desc_ = selec.xpath('//div[starts-with(@id,"HRS_JO_PDSC_VW_DESCRLONG$2")]//div/text()|\
                              //div[starts-with(@id,"HRS_JO_PDSC_VW_DESCRLONG$2")]//p/text()|\
                              //div[starts-with(@id,"HRS_JO_PDSC_VW_DESCRLONG$2")]//p//span//font/text()|\
                              //div[starts-with(@id,"HRS_JO_PDSC_VW_DESCRLONG$2")]//li/text()|\
                              //div[starts-with(@id,"HRS_JO_PDSC_VW_DESCRLONG$2")]//li//span/text()|\
                              //div[starts-with(@id,"HRS_JO_PDSC_VW_DESCRLONG$2")]//p//span/text()|\
                              //div[starts-with(@id,"HRS_JO_PDSC_VW_DESCRLONG$2")]//p//span/strong/text()|\
                              //div[starts-with(@id,"HRS_JO_PDSC_VW_DESCRLONG$2")]//p/strong/text()').extract()
      for job_desc in job_desc_:
        job_desc =  job_desc.encode('utf-8', 'ignore').strip()
        desc += str(job_desc) + '\n'
      #print desc

      # JOB REQUIRMENTS
      req = ''
      job_req_ = selec.xpath('//div[starts-with(@id,"HRS_JO_PDSC_VW_DESCRLONG$3")]//div/text()|\
                              //div[starts-with(@id,"HRS_JO_PDSC_VW_DESCRLONG$3")]//p/text()|\
                              //div[starts-with(@id,"HRS_JO_PDSC_VW_DESCRLONG$3")]//p//span//font/text()|\
                              //div[starts-with(@id,"HRS_JO_PDSC_VW_DESCRLONG$3")]//li/text()|\
                              //div[starts-with(@id,"HRS_JO_PDSC_VW_DESCRLONG$3")]//li//span/text()|\
                              //div[starts-with(@id,"HRS_JO_PDSC_VW_DESCRLONG$3")]//p//span/text()|\
                              //div[starts-with(@id,"HRS_JO_PDSC_VW_DESCRLONG$3")]//p//span/strong/text()|\
                              //div[starts-with(@id,"HRS_JO_PDSC_VW_DESCRLONG$3")]//p/strong/text()').extract()
      for job_req in job_req_:
        job_req =  job_req.encode('utf-8', 'ignore').strip()
        req += str(job_req) + '\n'

      # Exporting scraped result to a csv
      opfile.writerow([str(job_title),
          str(job_id),
          str(job_loc),
          str(desc),
          str(req)
          ])

    self.count_job_tot += 1



    
