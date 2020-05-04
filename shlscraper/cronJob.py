import os

#This is a cron job scheduled by either Windows Task Scheduler
#or by Linux Crontab.
os.system('Scrapy crawl liiga')
os.system('Scrapy crawl khl')
os.system('Scrapy crawl shl')