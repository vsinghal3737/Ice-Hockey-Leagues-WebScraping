# Ice-Hockey-Leagues-WebScraping
## ASU Software Engineering Capstone Team 

### Web Scraping
- WebScraping a new directory is added in the project, which is scraping 3 Ice Hockey Leagues, SHL, LIIGA, KHL leagues
- Scrapy, a web scraping framework is used and psycopg2 is used to push scraped data into AWS PostgreSQL Database

### Project Setup to run Web Scraper

1.	To download Python: [click here](https://www.python.org/downloads/)  
	Install the software as mentioned in it, and add its path to the system environment variable

2. 	To download Pip: [click here](https://bootstrap.pypa.io/get-pip.py)  
	Save the file `ctrl+s` (file should save in .py format)<br>
	Open command prompt in the download location: `python get-pip.py`

3.	To install Libraries that used in the project; under this dir: \rosterdata\WebSraping
    Open command prompt: `pip install -r requirements.txt`

4.	To check if everything installed properly
	In command prompt: `python`<br>
	In Python console: `import scrapy, psycopg2`<br>
	**If you get no error, Project Setup is Done**

5.	To run the project:<br>
    under this dir: \shlscraper <br>
	Open Command Prompt and type:
    - scrapy crawl shl       # to scrape data from shl website <br>
    - scrapy crawl liiga     # to scrape data from liiga website <br>
    - scrapy crawl khl       # to scrape data from khl website <br>
    
    **data will be updated and pushed to database in AWS PostgreSQL** <br>
