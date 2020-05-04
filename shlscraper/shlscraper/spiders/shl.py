# -*- coding: utf-8 -*-
'''
    Author   : Vaibhav Singhal, Sumanth Paranjape
    Function : implementing Scraper for SHL website
    Version  : V1
    Email    : vsingha5@asu.edu
'''


import scrapy
import json
from copy import deepcopy


class ShlSpider(scrapy.Spider):
    name = 'shl'

    start_urls = ['https://www.shl.se/statistik/']
    mainurl = 'https://www.shl.se'

    Teams = {}
    links = []
    LinksTemp = []
    TeamData = {}

    listofQueries = []

    columnsMapper = {
        '-/+': 'minus_plus',
        '+': 'plus',
        '-': 'minus',
        '+/-': 'plus_minus',
        '3P': 'three_P',
        '2P': 'two_P',
        '1P': 'one_P',
        '0P': 'zero_P',
        'TOI/GP': 'TOI_GP',
    }
    TestingStatus = False

    def parse(self, response):
        '''
            Parse is used to get scraping started which calls other methods to get the desired values
            for self.Teams and self.allPlayers
        '''

        # if int(input('\n\npress 1 for testing or 0 to push to database:\t')) == 1:
        #     self.TestingStatus = True

        self.Teams = self._getTeams(response)

        self.links = self._getLinks(response)
        self.LinksTemp = deepcopy(self.links)

        self.LinksTemp = [self.links[0]]

        if self.LinksTemp:
            link = self.LinksTemp.pop(0)
            yield response.follow(link, callback=self._getTeamData)

    def _getTeams(self, response):
        '''
            This method is used to get all main information of the league's teams, which
            can be seen in first page of statistics on liiga website
        '''

        data = response.xpath('//*[@class="rmss_t-stat-table rmss_t-scrollable-table"]')
        datahead = data.xpath('//thead')
        databody = data.xpath('//tbody')

        Teams = {
            'title': datahead.xpath('//tr')[0].xpath('//th').css('span::text').extract(),
            'teamdata': []
        }

        rawData = \
            list(
                filter(
                    lambda x: x.css('tr::attr(class)').extract()[0].split()[0] == 'rmss_t-stat-table__row',
                    databody.xpath('//tr')
                )
            )

        for j in range(len(rawData)):
            row = []
            for i in range(len(rawData[j].xpath('td//text()'))):
                currentVal = rawData[j].xpath('td//text()')[i].extract()
                if currentVal.strip() not in ['\n', '']:
                    row.append(currentVal)
            Teams['teamdata'].append(row[:])

        Teams['teamdata'].insert(0, Teams['title'])
        del Teams['title']

        for i in range(1, len(Teams['teamdata'])):
            del Teams['teamdata'][i][2]

        return Teams

    def _getLinks(self, response):
        '''
            It is used to get all the links of all teams present in the league
            by fetching data from <a href> html tag
        '''

        data = response.xpath('//*[@class="rmss_t-stat-table rmss_t-scrollable-table"]')
        databody = data.xpath('//thead')

        rawData = \
            list(
                filter(
                    lambda x: x.css('tr::attr(class)').extract()[0].split()[0] == 'rmss_t-stat-table__row',
                    databody.xpath('//tr')
                )
            )

        return [rawData[i].css('a::attr(href)').extract()[0] for i in range(len(rawData))]

    def _getTeamData(self, response):
        '''
            This method is used to get all the player's information in all the teams within liiga league
            it adds all the player values in row format with the key, as team name in instance self.TeamData

            This is done by popping every link fetched from self._getLinks,
            and in every recurssion the first link is poped and fed to this method
            and this method starts fetching values for new link
        '''

        statistics = list(filter(lambda x: 'statistics' in x, response.css('a.rmss_t-menu__inline-items-item-link::attr(href)').getall()))
        if statistics:
            statistics = self.mainurl + statistics[0]
            yield response.follow(statistics, callback=self._getDataFromSubLink)
        else:
            if self.LinksTemp:
                link = self.LinksTemp.pop(0)
                yield response.follow(link, callback=self._getTeamData)
            else:
                if self.TestingStatus:
                    with open('json/shlLeague.json', 'w') as file:
                        json.dump(self.Teams, file)
                    yield self.Teams
                else:
                    self.genQueries()

    def _getDataFromSubLink(self, response):
        '''
            this method is further used to handle some exceptions and
            add subdata values for team players from the league website
        '''

        TeamName = \
            response.\
            css('div.rmss_c-squad__team-header-name header.rmss_c-squad__team-header-name-h::text').\
            extract()[0]

        data = response.xpath('//*[@class="rmss_t-stat-table rmss_t-scrollable-table"]')
        datahead = data.xpath('//thead')
        databody = data.xpath('//tbody')

        title = datahead.xpath('//tr')[0].xpath('//th').css('span::text').extract()[1:3]
        title.extend(datahead.xpath('//tr')[0].xpath('//th').css('a::text').extract()[:14])
        title[0] = 'Names'

        currentTeam = []
        for row in range(len(databody.css('tr.rmss_t-stat-table__row'))):
            count = 0
            temp = []
            for i in databody.css('tr.rmss_t-stat-table__row')[row].css('td'):
                if count == 1:
                    x = i.css('span::text').extract()[0]
                    if x[0] == '*':
                        x = x[1:]
                    temp.append(x)
                else:
                    temp.extend(i.css('td::text').extract())
                count += 1
            currentTeam.append(temp[1:])

        standard = len(title)

        currentTeam = list(filter(lambda x: len(x) == standard, currentTeam))

        self.TeamData[TeamName] = [title] + currentTeam

        if self.LinksTemp:
            link = self.LinksTemp.pop(0)
            yield response.follow(link, callback=self._getTeamData)
        else:
            if self.TestingStatus:
                with open('json/shlLeague.json', 'w') as file:
                    json.dump(self.Teams, file)
                yield self.Teams
            else:
                self.genQueries()

    def ColumnMapper(self, val):
        val = val.upper()
        return self.columnsMapper[val].upper() if val in self.columnsMapper else val

    def genQueries(self):
        '''
            genQueries is used to convert the data from self.Teams & self.TeamData into list of string,
            each string is used to execute sql queries to push, delete, create entries in the PostgreSQL database
        '''

        self.Teams['teamdata'][0][1] = 'LEAGUES'
        # STORING DATA IN JSON
        '''
        with open('shlLeague.json', 'w') as file:
            json.dump(self.Teams, file)

        with open('shlTeams.json', 'w') as file:
            json.dump(self.TeamData, file)
        '''

        # Pringting Values
        '''
        for i in self.Teams['teamdata']:
            print(i)
        print()
        print()
        for i in self.TeamData:
            print(i)
            for j in self.TeamData[i]:
                print(j)
        '''

        # DATABASE LEAGUE QUERIES
        dropLeagueTable = "DROP TABLE IF EXISTS shlLeagues"
        createLeagueTable = \
            "CREATE TABLE shlLeagues ({}, PRIMARY KEY ({}))".\
            format(
                ' varchar(255), '.join(list(map(self.ColumnMapper, self.Teams['teamdata'][0]))) + ' varchar(255)',
                self.Teams['teamdata'][0][1]
            )
        AddLeagueValues = [
            'INSERT INTO shlLeagues VALUES ({})'.
            format(
                ', '.join(list(map(lambda x: "'{}'".format(str(x)), self.Teams['teamdata'][i]))))
            for i in range(1, len(self.Teams['teamdata']))
        ]

        # print(dropLeagueTable)
        # print(createLeagueTable)
        # for i in AddLeagueValues:
        #     print(i)

        # # DATABASE TEAMDATA QUERIES
        dropTeamsTable = "DROP TABLE IF EXISTS shlTeams"

        titles = list(map(self.ColumnMapper, self.TeamData[list(self.TeamData.keys())[0]][0]))
        titles.insert(1, 'TEAM')
        createTeamsTable = \
            "CREATE TABLE shlTeams (id SERIAL, {}, PRIMARY KEY (id));".\
            format(' varchar(255), '.join(titles) + ' varchar(255)')

        AddTeamsValues = \
            [
                [
                    'INSERT INTO shlTeams ({}) VALUES ({})'.
                    format(
                        ', '.join(titles),
                        ', '.join(list(map(lambda x: "'{}'".format(str(x)), [row[0]] + [key] + row[1:])))
                    )
                    for row in self.TeamData[key]
                ] for key in self.TeamData.keys()
            ]

        # print(dropTeamsTable)
        # print(createTeamsTable)
        # for i in AddTeamsValues:
        #     for j in i:
        #         print(j)

        self.listofQueries.append(dropLeagueTable)
        self.listofQueries.append(createLeagueTable)
        self.listofQueries.extend(AddLeagueValues)

        self.listofQueries.append(dropTeamsTable)
        self.listofQueries.append(createTeamsTable)
        for i in AddTeamsValues:
            self.listofQueries.extend(i)

        # for i in self.listofQueries:
        #     print(i)

        self.pushToDatabase()

    def pushToDatabase(self):
        '''
            pushToDatabase is used to execute all the queries generated by genQueries
            it creates a connection object with the database,
            and starts executing all the queries one by one 
        '''

        import sys
        sys.path.append('./shlscraper/database/')
        import dbconnect as db

        print("=======Connecting to database===========")
        connection = db.get_db_connection()
        cursor = connection.cursor()
        print("===Creating SQL statements===")
        for query in self.listofQueries:
            print(query)
            cursor.execute(query)
        connection.commit()
        print("===Queries executed successfully===")
        cursor.close()
        connection.close()


def rem(func):
    return list(filter(lambda x: x[0] != '_', func))
