# -*- coding: utf-8 -*-
'''
    Author   : Vaibhav Singhal
    Function : implementing Scraper for LIIGA website
    Version  : V1
    Email    : vsingha5@asu.edu
'''


import scrapy
from copy import deepcopy
import json


class LiigaSpider(scrapy.Spider):
    name = 'liiga'
    # allowed_domains = ['liiga.fi/fi/tilastot/2019-2020/runkosarja/joukkueet']
    start_urls = ['http://liiga.fi/fi/tilastot/2019-2020/runkosarja/joukkueet/']

    playersLink = 'https://liiga.fi/fi/tilastot/2019-2020/runkosarja/pelaajat/'
    teamLink = '/fi/tilastot/2019-2020/runkosarja/pelaajat'

    Teams = []
    allPlayers = {}

    listofQueries = []

    columnsMapper = {
        'P/O': 'P_O',
        'YV%': 'Y_V',
        'AV%': 'A_V',
        '+': 'plus',
        '-': 'minus',
        'Â±': 'plus_minus',
        'L%': 'L_percent',
        'A%': 'A_percent',
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

        yield response.follow(self.teamLink, callback=self._getAllPlayers)

    def _getTeams(self, response):
        '''
            This method is used to get all main information of the league's teams, which
            can be seen in first page of statistics on liiga website
        '''

        data = response.xpath('//*[@class="team-table"]')
        Teams = {
            'title': ['Team'] + data.xpath('//tr').css('a::text').extract()[1:],
        }

        teamRawData = data.xpath('//tbody').xpath('//tr')

        teamdata = []
        for i in range(1, len(teamRawData)):
            x = list(filter(lambda x: x != '', map(lambda x: x.strip().replace(',', '.'), teamRawData[i].css('tr td::text').getall())))[1:]
            x.insert(8, teamRawData[i].css('tr td strong::text').getall()[0])
            teamdata.append(x)

        Teams['teamdata'] = deepcopy(teamdata)

        return Teams

    def _getAllPlayers(self, response):
        '''
            This method is used to get all the player's information in all the teams within liiga league
            it adds all the player values in row format with the key, as team name in instance self.allPlayers
        '''

        thead = response.xpath('//*[@class="tight"]//thead//text()')
        tbody = response.xpath('//*[@class="tight"]//tbody//tr')

        title = ['Name', 'Team'] + list(filter(lambda x: x is not None and x != '', map(lambda x: x.strip(), thead.getall())))[3:-1] + ['Time']

        for i in range(len(tbody)):
            row = tbody[i].xpath('td//text()').getall()
            row = list(filter(lambda x: x is not None and x != '', (map(lambda x: x.strip(), row))))

            if row[1] == '#':
                row.pop(1)
            if row[2] in ['*', '!']:
                row.pop(2)

            if row[2] in self.allPlayers:
                self.allPlayers[row[2]].append(row[1:])
            else:
                self.allPlayers[row[2]] = [title] + [row[1:]]
        if self.TestingStatus:
            with open('json/liigaLeague.json', 'w') as file:
                json.dump(self.Teams, file)
            print(self.Teams)
            yield self.Teams
        else:
            self.genQueries()

    def ColumnMapper(self, val):
        return self.columnsMapper[val.upper()].upper() if val in self.columnsMapper else val.upper()

    def genQueries(self):
        '''
            genQueries is used to convert the data from self.Teams & self.allPlayers into list of string,
            each string is used to execute sql queries to push, delete, create entries in the PostgreSQL database
        '''

        # STORING DATA IN JSON
        '''
        with open('liigaLeague.json', 'w') as file:
            json.dump(self.Teams, file)

        with open('liigaTeams.json', 'w') as file:
            json.dump(self.allPlayers, file)
        '''

        # Printing Values
        '''
        print(self.Teams['title'])
        for i in self.Teams['teamdata']:
            print(i)

        for i in self.allPlayers:
            for j in self.allPlayers[i]:
                print(j)
            print()
        print()
        print()
        '''

        # DATABASE LEAGUE QUERIES
        dropLeagueTable = "DROP TABLE IF EXISTS liigaLeagues"
        createLeagueTable = \
            "CREATE TABLE liigaLeagues (id SERIAL, {}, PRIMARY KEY (id))".\
            format(
                ' varchar(255), '.join(list(map(self.ColumnMapper, self.Teams['title']))) + ' varchar(255)'
            )
        AddLeagueValues = [
            'INSERT INTO liigaLeagues ({}) VALUES ({});'.
            format(
                ', '.join(list(map(self.ColumnMapper, self.Teams['title']))),
                ', '.join(list(map(lambda x: "'{}'".format(str(x)), row)))
            ) for row in self.Teams['teamdata']
        ]

        # print(dropLeagueTable)
        # print(createLeagueTable)
        # for i in AddLeagueValues:
        #     print(i)

        # DATABASE TEAMDATA QUERIES
        dropTeamsTable = "DROP TABLE IF EXISTS liigaTeams"

        createTeamsTable = \
            "CREATE TABLE liigaTeams (id SERIAL, {}, PRIMARY KEY (id))".\
            format(' varchar(255), '.join(list(map(self.ColumnMapper, self.allPlayers[list(self.allPlayers.keys())[0]][0]))) + ' varchar(255)')

        AddTeamsValues = \
            [
                [
                    'INSERT INTO liigaTeams ({}) VALUES ({})'.
                    format(
                        ', '.join(list(map(self.ColumnMapper, self.allPlayers[list(self.allPlayers.keys())[0]][0]))),
                        ', '.join(list(map(lambda x: "'{}'".format(str(x)), self.allPlayers[list(self.allPlayers.keys())[0]][i]))))
                    for i in range(1, len(self.allPlayers[list(self.allPlayers.keys())[0]]))
                ] for key in self.allPlayers.keys()
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

        self.pushToDatabase()
        # for i in self.listofQueries:
        #     print(i)

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
