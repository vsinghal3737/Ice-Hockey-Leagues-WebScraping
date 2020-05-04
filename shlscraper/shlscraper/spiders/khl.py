# -*- coding: utf-8 -*-
'''
    Author   : Vaibhav Singhal
    Function : implementing Scraper for KHL website
    Version  : V1
    Email    : vsingha5@asu.edu
'''


import scrapy
from scrapy.selector import Selector
from copy import deepcopy
import json


class EconomistItem(scrapy.Item):
    title = scrapy.Field()
    link = scrapy.Field()
    desc = scrapy.Field()


class KhlSpider(scrapy.Spider):
    name = 'khl'

    # allowed_domains = ['en.khl.ru']
    start_urls = ['https://en.khl.ru/stat/teams/']

    Teams = {}
    TeamData = {}

    links = []
    LinksTemp = []

    listofQueries = []

    columnsMapper = {
        '№': 'Number',
        '%SV': 'sv_percentage',
        '-/+': 'minus_plus',
        '+': 'plus',
        '-': 'minus',
        '+/-': 'plus_minus',
        '%SOG': 'SOG_percentage',
        'S/G': 'S_G',
        '%FO': 'FO_percentage',
        'TOI/GP': 'TOI_GP',
        'TOI/G': 'TOI_G',
        'SFT/G': 'SFT_G',
        'УП': 'YN',
        '%УП': 'YN_percentage',
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

        # self.LinksTemp = [self.links[0]]

        if self.LinksTemp:
            yield response.follow(self.LinksTemp.pop(0), callback=self._getTeamData)

    def _getTeams(self, response):
        '''
            This method is used to get all main information of the league's teams, which
            can be seen in first page of statistics on liiga website
        '''

        data = response.selector.xpath('//*[@id="teams_dataTable"]')[0]

        datahead = data.xpath('thead')
        databody = data.xpath('tbody')

        teams = {
            'title': datahead.xpath('tr')[0].xpath('th').xpath('text()').extract(),
            'teamdata': []
        }

        for row in databody.xpath('tr'):
            teams['teamdata'].append(list(filter(lambda x: x.strip() != '', row.xpath('td//text()').extract())))

        teams['title'] = list(map(self.ColumnMapper, teams['title']))
        teams['teamdata'].insert(0, teams['title'])
        del teams['title']
        return teams

    def _getLinks(self, response):
        '''
            It is used to get all the links of all teams present in the league,
            by fetching data from <a href> html tag
        '''

        data = response.selector.xpath('//*[@id="teams_dataTable"]')[0]
        databody = data.xpath('tbody')

        return databody.xpath('tr').xpath('td').xpath('a/@href').extract()

    def _getTeamData(self, response):
        '''
            This method is used to get all the player's information in all the teams within liiga league
            it adds all the player values in row format with the key, as team name in instance self.TeamData

            This is done by popping every link fetched from self._getLinks,
            and in every recurssion the first link is poped and fed to this method
            and this method starts fetching values for new link
        '''

        Positions = {'Goalkeepers': 'G', 'Defensemen': 'D', 'Forwards': 'F'}
        position = []
        for i in response.selector.xpath('//*[@class="s-ajax_statistics_leaders"]/div'):
            position.append(Positions[i.xpath('div')[0].xpath('h4/text()').extract()[0]])

        data = response.selector.xpath('//*[@class="s-ajax_statistics_leaders"]/div')

        Goalkeepers = list(map(lambda x: [x[0]] + ['G'] + x[1:], self._getSubData(position[0], 'goalies_dataTable', data[0])))
        Defensemen = list(map(lambda x: [x[0]] + ['D'] + x[1:], self._getSubData(position[1], 'defenses_dataTable', data[1])))
        Forwards = list(map(lambda x: [x[0]] + ['F'] + x[1:], self._getSubData(position[2], 'forwards_dataTable', data[2])))

        del Goalkeepers[0][1]
        del Defensemen[0][1]
        del Forwards[0][1]

        teamName = str(response.url).split("/")[-2]

        Goalkeepers[0] = list(map(self.ColumnMapper, Goalkeepers[0]))
        Defensemen[0] = list(map(self.ColumnMapper, Defensemen[0]))
        Forwards[0] = list(map(self.ColumnMapper, Forwards[0]))

        self.TeamData[teamName] = {
            'Goalkeepers': Goalkeepers,
            'Defensemen': Defensemen,
            'Forwards': Forwards
        }
        if self.LinksTemp:
            link = self.LinksTemp.pop(0)
            yield response.follow(link, callback=self._getTeamData)
        else:
            if self.TestingStatus:
                with open('json/khlLeague.json', 'w') as file:
                    json.dump(self.Teams, file)
                yield self.Teams
            else:
                self.genQueries()

    def _getSubData(self, pos, table, data):
        '''
            this method is further used to handle some exceptions and
            add subdata values for team players from the league website
        '''

        datahead = data.xpath('*[@id="{}"]/thead'.format(table))
        title = ['Player', 'Pos'] + datahead.xpath('tr')[0].xpath('th').xpath('text()').extract()
        title = list(map(self.ColumnMapper, title))
        javascript = data.css('script::text')[0].get().split('var {}_Table'.format(table.split('_')[0]))[0].strip()[12 + len(table.split('_')[0]):-1]
        rows = eval(javascript)
        rows = list(map(self.__namesplit, map(lambda x: self.__deletecel(table.split('_')[0], x), rows)))
        for i in range(len(rows)):
            rows[i] = list(map(lambda x: x.replace("'", "''"), rows[i]))
        return [title] + rows

    def __namesplit(self, row):
        new = deepcopy(row)
        new[2] = new[2].split(' ')[0]
        return new

    def __deletecel(self, Type, row):
        temp = deepcopy(row)
        x = temp.pop(0)
        temp[1] = Selector(text=temp[1]).css('a::attr(title)').extract()[0]
        new = temp[:-4] if Type == 'goalies' else temp[:-1]
        return Selector(text=x).css('b::text').extract() + new

    def ColumnMapper(self, val):
        val = val.upper()
        return self.columnsMapper[val].upper() if val in self.columnsMapper else val

    def genQueries(self):
        '''
            genQueries is used to convert the data from self.Teams & self.TeamData into list of string,
            each string is used to execute sql queries to push, delete, create entries in the PostgreSQL database
        '''

        # STORING DATA IN JSON
        # with open('khlLeague.json', 'w') as file:
        #     json.dump(self.Teams, file)

        # with open('khlTeams.json', 'w') as file:
        #     json.dump(self.TeamData, file)

        # Printing Values
        # for i in self.Teams['teamdata']:
        #     print(i)
        # print()
        # print()

        # for Team in self.TeamData:
        #     print(Team)
        #     for Type in self.TeamData[Team]:
        #         for row in self.TeamData[Team][Type]:
        #             print(row)
        #         print()
        #     print()
        #     print()

        # ______________________________________________________________________________________
        # DATABASE LEAGUE QUERIES
        dropLeagueTable = "DROP TABLE IF EXISTS khlLeagues"
        createLeagueTable = "CREATE TABLE khlLeagues (id Serial, {}, PRIMARY KEY (id))".\
            format(' varchar(255), '.join(self.Teams['teamdata'][0]) + ' varchar(255)')

        AddLeagueValues = [
            'INSERT INTO khlLeagues ({}) VALUES ({})'.
            format(
                ', '.join(self.Teams['teamdata'][0]),
                ', '.join(list(map(lambda x: "'{}'".format(str(x)), self.Teams['teamdata'][i]))))
            for i in range(1, len(self.Teams['teamdata']))
        ]

        # print(dropLeagueTable)
        # print(createLeagueTable)
        # for i in AddLeagueValues:
        #     print(i)

        # DATABASE TEAMDATA QUERIES
        Type = ['Goalkeepers', 'Defensemen', 'Forwards']

        dropTeamsTable = [
            "DROP TABLE IF EXISTS khl{}".format(i)
            for i in Type
        ]

        createTeamsTable = [
            "CREATE TABLE khl{} (id Serial, {}, PRIMARY KEY (id))".
            format(i, ' varchar(255), '.join(self.TeamData[list(self.TeamData.keys())[0]][i][0]) + ' varchar(255)')
            for i in Type
        ]

        AddTeamsValues = {'Goalkeepers': [], 'Defensemen': [], 'Forwards': []}

        for team in self.TeamData:
            for key in self.TeamData[team]:
                AddTeamsValues[key].extend(
                    [
                        'INSERT INTO khl{} ({}) VALUES ({})'.
                        format(
                            key, ', '.join(self.TeamData[team][key][0]), row
                        ) for row in list(map(lambda x: ', '.join(list(map(lambda y: "'" + y + "'", x))), self.TeamData[team][key][1:]))
                    ]
                )

        # for i in dropLeagueTable:
        #     print(i)
        # for i in createTeamsTable:
        #     print(i)
        # for i in AddTeamsValues:
        #     for j in i:
        #         print(j)

        self.listofQueries = []

        self.listofQueries.append(dropLeagueTable)
        self.listofQueries.append(createLeagueTable)
        self.listofQueries.extend(AddLeagueValues)

        self.listofQueries.extend(dropTeamsTable)
        self.listofQueries.extend(createTeamsTable)
        for keys in AddTeamsValues:
            self.listofQueries.extend(AddTeamsValues[keys])

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
