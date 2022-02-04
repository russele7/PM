#!/usr/bin/env python
# coding: utf-8

# In[4]:

from selenium import webdriver
import selenium
from time import sleep
import html_to_json
import pandas as pd
import numpy as np
from datetime import datetime as dt
from datetime import timedelta
import re

from itertools import chain
from dateutil.relativedelta import relativedelta

# In[5]:

class result_page:
    def __init__(self, COUNTRY, TOURNAMENT):
        self.COUNTRY = COUNTRY
        self.TOURNAMENT = TOURNAMENT
        self.MONTH_DICT = {"янв": 1,  "фев": 2,  "мар": 3, 
                          "апр": 4,  "май": 5,  "июн": 6, 
                          "июл": 7,  "авг": 8,  "сен": 9, 
                          "окт": 10, "ноя": 11, "дек": 12}
        
    def game_data_extraction(game_data, COUNTRY, TOURNAMENT):        
        team1 =   game_data[0]['a'][0]['_value']
        team2 =   game_data[2]['a'][0]['_value']
        date =    dt.strptime(game_data[3]['_value'], '%d.%m.%Y').date()
        result =  game_data[1]['a'][0]['_value']    
        return [COUNTRY, TOURNAMENT, date, team1, team2, result]   
    
    def all_games_extraction(gm_list, OBSDT, COUNTRY, TOURNAMENT):
        df = pd.DataFrame(columns = ['COUNTRY', 'TOURNAMENT', 'DATE', 'HT', 'GT',  'RESULT'])    
        i = 0

        for i, game in enumerate(gm_list):    
            try:
                df.loc[i] = result_page.game_data_extraction(game, COUNTRY, TOURNAMENT)
            except:
                pass
        return df   
        
    def download_webpage(self, URL):
        self.OBSDT = dt.today().replace(microsecond = 0)
        
        driver = webdriver.Chrome()
        driver.get(URL)
        sleep(10)
        content = driver.page_source
        driver.close()
        
        self.content_json = html_to_json.convert(content)
    
        self.web_data = self.content_json['html'][0]['body'][0]
        self.n_tours = len(self.web_data['div'][1]['div'][1]['div'][1]['div'][2]['div'])
        self.tours_list = [self.web_data['div'][1]['div'][1]['div'][1]['div'][2]['div'][i]['div'] for i in range(self.n_tours)]
        
        self.half_tours_list = [[tour[i]['table'][0]['tbody'][0]['tr']   for i in range(2)]  for tour in self.tours_list]
        # flattening
        self.half_tours_list = list(chain.from_iterable(self.half_tours_list))
        self.half_tours_len_list = [len(half) for half in self.half_tours_list]
        
#         self.games_list =  [[half[i]['td'] for  i in range(5)]  for half  in self.half_tours_list]
        self.games_list =  [[half[i]['td'] for  i in range(self.half_tours_len_list[j])]  for j, half  in 
                                                                                            enumerate(self.half_tours_list)]
        # flattening
        self.games_list = list(chain.from_iterable(self.games_list))
        
        self.df_games = result_page.all_games_extraction(self.games_list, self.OBSDT, self.COUNTRY, self.TOURNAMENT)

# In[6]:
class sport_page:
    def __init__(self, COUNTRY, TOURNAMENT):
        self.COUNTRY = COUNTRY
        self.TOURNAMENT = TOURNAMENT
        self.MONTH_DICT = {"янв": 1,  "фев": 2,  "мар": 3, 
                          "апр": 4,  "май": 5,  "июн": 6, 
                          "июл": 7,  "авг": 8,  "сен": 9, 
                          "окт": 10, "ноя": 11, "дек": 12}
        
    def game_data_extraction(gmdt, OBSDT, COUNTRY, TOURNAMENT, MONTH_DICT):

        team1 =  gmdt[0]['div'][0]['div'][1]['span'][0]['_value']
        team2 =  gmdt[0]['div'][2]['div'][1]['span'][0]['_value']       
        
        try:
            gdate =  gmdt[0]['div'][1]['div'][1]['span'][0]['_value']
            gtime =  gmdt[0]['div'][1]['div'][1]['span'][1]['_value']
        except:
            gdate =  gmdt[0]['div'][1]['div'][0]['span'][0]['_value']
            gtime =  gmdt[0]['div'][1]['div'][0]['span'][1]['_value']
        
        if gdate.lower() == 'завтра':
            gdt = dt(dt.now().year, (dt.now()+ timedelta(days = 1)).month, (dt.now()+ timedelta(days = 1)).day,
                     int(gtime[:2]), int(gtime[-2:]), 0) 
        elif gdate.lower() == 'сегодня':
            gdt = dt(dt.now().year, dt.now().month, dt.now().day,
                     int(gtime[:2]), int(gtime[-2:]), 0)
        else:
            gdt = dt(dt.now().year, MONTH_DICT[gdate[-3:]], int(gdate[:2]), int(gtime[:2]), int(gtime[-2:]), 0)
        
        if dt.today().month > gdt.month:
            gdt = gdt + relativedelta(years = 1)           

        p1 = gmdt[1]['div'][0]['div'][0]['div'][0]['div']
        x  = gmdt[1]['div'][0]['div'][0]['div'][1]['div']
        p2 = gmdt[1]['div'][0]['div'][0]['div'][2]['div']
        coef = {}
        coef[p1[0]['_value']] = float(p1[1]['div'][0]['span'][0]['_value']) #П1
        coef[x[0]['_value']] = float(x[1]['div'][0]['span'][0]['_value']) #X
        coef[p2[0]['_value']] = float(p2[1]['div'][0]['span'][0]['_value']) #П2
        
        return [gdt, OBSDT, team1, team2, COUNTRY, TOURNAMENT, coef['П1'], coef['Х'], coef['П2']]

    def get_games_list(data, OBSDT, COUNTRY, TOURNAMENT, MONTH_DICT):
        ll = []
        for i, elem in enumerate(data):
            try:
                ll.append(sport_page.game_data_extraction(elem, OBSDT, COUNTRY, TOURNAMENT, MONTH_DICT))
            except:
                print(f'ERROR in get_games_list on step {i}')    
        return ll

    def cleaning_games(raw_game_list):
        clean_game_list = []
        for elem in raw_game_list:
            try:
                clean_game_list.append(elem['a'][0]['div'])
            except:
                pass
        return clean_game_list
    
    def download_webpage(self, URL):
        self.OBSDT = dt.today().replace(microsecond = 0) #  ВРЕМЯ ИЗМЕРЕНИЯ
        driver = webdriver.Chrome()
        driver.get(URL)
        sleep(10)
        content = driver.page_source
        driver.close()
        self.content_json = html_to_json.convert(content) 

        try:       
            self.web_data = self.content_json['html'][0]['body'][0]['div'][0]['div'][1]['div'][0]['div'][2]['div'][1]['div']
            self.n_sets = len(self.web_data)
            self.sets_list = [self.web_data[i]['div'] for i in range(1, self.n_sets)]
            
            self.games_row_array = [[elem[j]['a'][0]['div']  for  j in range(len(elem))]  for elem in self.sets_list]
            self.games_row_array = list(chain.from_iterable(self.games_row_array))      
        except:
            self.web_data = self.content_json['html'][0]['body'][0]        
            self.one_set_data = self.web_data['div'][0]['div'][1]['div'][0]['div'][1]['div'][2]['div'][0]['div'][0]['div']        
            self.games_row_array = sport_page.cleaning_games(self.one_set_data)

        
        self.df_games = pd.DataFrame(sport_page.get_games_list(self.games_row_array, self.OBSDT, 
                                                                self.COUNTRY, self.TOURNAMENT, self.MONTH_DICT), 
                            columns = ['GAME_DT', 'OBSDT', 'HT', 'GT', 'COUNTRY', 'TOURNAMENT', 'HW_COEF', 'DR_COEF', 'GW_COEF'])


# In[ ]:
class live_page:
    def __init__(self, COUNTRY, TOURNAMENT):
        self.COUNTRY = COUNTRY
        self.TOURNAMENT = TOURNAMENT
        self.MONTH_DICT = {"янв": 1,  "фев": 2,  "мар": 3, 
                          "апр": 4,  "май": 5,  "июн": 6, 
                          "июл": 7,  "авг": 8,  "сен": 9, 
                          "окт": 10, "ноя": 11, "дек": 12}
        
    def game_data_extraction(one_game_data, OBSDT, COUNTRY, TOURNAMENT):
        try:
            GAME_LIVE_TIME = one_game[0]['div'][1]['div'][0]['span'][0]['_value']
        except:    
            try:
                GAME_LIVE_TIME = one_game[0]['div'][1]['div'][1]['span'][0]['_value']
            except:
                GAME_LIVE_TIME = one_game[0]['div'][1]['div'][2]['span'][0]['_value']

        try:
#             print('GTIM TRY')
            GTIM =  int(re.findall('тайм \d+', GAME_LIVE_TIME)[0][5:])
        except:
            GTIM = GAME_LIVE_TIME
        TAYM =  GAME_LIVE_TIME[:1]
        COUNTRY = COUNTRY
        TOURNAMENT = TOURNAMENT

        HT = one_game_data[0]['div'][0]['div'][1]['span'][0]['_value']
        GT = one_game_data[0]['div'][2]['div'][1]['span'][0]['_value']
        
        try:
            SCORE_DATA = one_game_data[0]['div'][1]['div'][0]['div'][0]['span']
        except:
            SCORE_DATA = one_game_data[0]['div'][1]['div'][1]['div'][0]['span']
        
        SC1 = int(SCORE_DATA[0]['_value'])
        SC2 = int(SCORE_DATA[2]['_value'])
        SCORE = str(SC1) + ':' + str(SC2)
        try:
            HW_COEF = float(one_game_data[1]['div'][0]['div'][0]['div'][0]['div'][1]['div'][0]['span'][0]['_value'])
            DR_COEF = float(one_game_data[1]['div'][0]['div'][0]['div'][1]['div'][1]['div'][0]['span'][0]['_value'])
            GW_COEF = float(one_game_data[1]['div'][0]['div'][0]['div'][2]['div'][1]['div'][0]['span'][0]['_value'])
        except:
            DR_COEF, HW_COEF, GW_COEF  = np.nan, np.nan, np.nan

        return [OBSDT, GAME_LIVE_TIME, GTIM, TAYM, COUNTRY, TOURNAMENT, 
               HT, GT, SC1, SC2, SCORE, HW_COEF, DR_COEF, GW_COEF]

    def live_data_extraction(live_data, OBSDT, COUNTRY, TOURNAMENT):
        df = pd.DataFrame(columns = ['OBSDT', 'GAME_LIVE_TIME', 'GTIM', 'TAYM', 'COUNTRY', 'TOURNAMENT', 
               'HT', 'GT', 'SC1','SC2', 'SCORE', 'HW_COEF', 'DR_COEF', 'GW_COEF'])    
        
        i = 0
        for j in range(len(live_data)):
            try:
                game_data = live_data[j]['a'][0]['div']                
                df.loc[i] = live_page.game_data_extraction(game_data, OBSDT = OBSDT, COUNTRY = COUNTRY, TOURNAMENT = TOURNAMENT)
                i += 1          
            except:
                print(f'ERROR on i = {i}, country = {COUNTRY}')
                
        for col in ['GTIM', 'TAYM', 'SC1', 'SC2']:
            try:
                df[col] = df[col].astype(int)   
#                 print(f'TRY {COUNTRY} / column = {col}')
            except:
                pass 
        return df
    
    def download_webpage(self, URL):
        self.OBSDT = dt.today().replace(microsecond = 0) #  ВРЕМЯ ИЗМЕРЕНИЯ
        driver = webdriver.Chrome()
        driver.get(URL)
        sleep(10)
        content = driver.page_source
        driver.close()
        
        self.content_json = html_to_json.convert(content)  
        
        try:
            self.games = self.content_json['html'][0]['body'][0]['div'][0]['div'][1]['div'][0]['div'][2]['div'][1]['div'][1]['div']                      
        except:
            self.games = self.content_json['html'][0]['body'][0]['div'][0]['div'][1]['div'][0]['div'][1]['div'][2]['div'][0]['div'][0]['div']
                              
        self.df_games = live_page.live_data_extraction(
            self.games, self.OBSDT, self.COUNTRY, self.TOURNAMENT)

# In[ ]:

data_list = \
        {'england': ['ПРЕМЬЕР-ЛИГА',      
                     'https://www.parimatch.ru/ru/football/premier-league-7f5506e872d14928adf0613efa509494/prematch',
                     'https://terrikon.com/football/england/championship/matches',
                    'https://www.parimatch.ru/ru/football/championship-eeb107510b84417f833551f3b6e2351c/live'], 
        'germany':  ['БУНДЕСЛИГА',        
                     'https://www.parimatch.ru/ru/football/bundesliga-966112317e2c4ee28d5a36df840662d6/prematch',
                     'https://terrikon.com/football/germany/championship/matches',
                    'https://www.parimatch.ru/ru/football/bundesliga-966112317e2c4ee28d5a36df840662d6/live'],
        'spain': ['ЛА ЛИГА', 
                   'https://www.parimatch.ru/ru/football/laliga-d84ce93378454b0fa61d58b2696a950b/prematch',
                   'https://terrikon.com/football/spain/championship/matches',
                 'https://www.parimatch.ru/ru/football/laliga-d84ce93378454b0fa61d58b2696a950b/live'],
        'italy': ['СЕРИЯ А',
                   'https://www.parimatch.ru/ru/football/serie-a-6d80f3f3fa35431b80d50f516e4ce075/prematch',
                   'https://terrikon.com/football/italy/championship/matches',
                 'https://www.parimatch.ru/ru/football/serie-a-6d80f3f3fa35431b80d50f516e4ce075/live'], 
        'france': ['ЛИГА 1',
                    'https://www.parimatch.ru/ru/football/ligue-1-254e4ecf1eb84a73b37b9cedffac646d/prematch',
                    'https://terrikon.com/football/france/championship/matches',
                  'https://www.parimatch.ru/ru/football/ligue-1-254e4ecf1eb84a73b37b9cedffac646d/live'], 
        'belgium': ['ПЕРВЫЙ ДИВИЗИОН А', 
                     'https://www.parimatch.ru/ru/football/first-division-a-e5bdb73049d54f40a61723262068f462/prematch',
                     'https://terrikon.com/football/belgium/championship/matches',
                   'https://www.parimatch.ru/ru/football/first-division-a-e5bdb73049d54f40a61723262068f462/live'],
        'netherlands': 
                    ['ERIDIVISIE',
                      'https://www.parimatch.ru/ru/football/eredivisie-00bf4eb20b8d4ad8b43b46fa5dda5be1/prematch',
                      'https://terrikon.com/football/netherlands/championship/matches',
                    'https://www.parimatch.ru/ru/football/eredivisie-00bf4eb20b8d4ad8b43b46fa5dda5be1/live'],
        'portugal': ['ПРИМЕЙРА-ЛИГА',
                      'https://www.parimatch.ru/ru/football/primeira-liga-c2fc983af0c643be85e60663d28585ce/prematch',
                      'https://terrikon.com/football/portugal/championship/matches',
                    'https://www.parimatch.ru/ru/football/primeira-liga-c2fc983af0c643be85e60663d28585ce/live'], 
        'turkey': ['СУПЕРЛИГА',
                    'https://www.parimatch.ru/ru/football/super-league-5af164b314434cd4a4e8a30b0724eeab/prematch',
                    'https://terrikon.com/football/turkey/championship/matches',
                  'https://www.parimatch.ru/ru/football/super-league-5af164b314434cd4a4e8a30b0724eeab/live'],
        'czech': ['ПЕРВАЯ ЛИГА',
                   'https://www.parimatch.ru/ru/football/1-liga-7c390835c0624753ba812b92215af16c/prematch',
                   'https://terrikon.com/football/czech/championship/matches',
                 'https://www.parimatch.ru/ru/football/1-liga-7c390835c0624753ba812b92215af16c/live'],
         'poland': ['EKSTRAKLASA', 
                   'https://www.parimatch.ru/ru/football/ekstraklasa-c930c57556f4413d8805cb9ae8d4d5a1/prematch',
                   'https://terrikon.com/football/poland/championship/matches',
                   'https://www.parimatch.ru/ru/football/ekstraklasa-c930c57556f4413d8805cb9ae8d4d5a1/live'],                   
        'greece': ['СУПЕРЛИГА 1',
                    'https://www.parimatch.ru/ru/football/super-league-1-abcb0f035b2b4d5b90ee2dd481487c98/prematch',
                    'https://terrikon.com/football/greece/championship/matches',
                  'https://www.parimatch.ru/ru/football/super-league-1-abcb0f035b2b4d5b90ee2dd481487c98/live'],
        'scotland': ['ПРЕМЬЕРШИП',
                    'https://www.parimatch.ru/ru/football/premiership-10bed6b95e4e4d63a272f05aeab0980d/prematch',
                    'https://terrikon.com/football/scotland/championship/matches',
                    'https://www.parimatch.ru/ru/football/premiership-10bed6b95e4e4d63a272f05aeab0980d/live'],
        'swiss': ['СУПЕРЛИГА',
                    'https://www.parimatch.ru/ru/football/super-league-b9ca937509c1440aaaacb4fd7c593b80/prematch',
                    'https://terrikon.com/football/swiss/championship/matches',
                 'https://www.parimatch.ru/ru/football/super-league-b9ca937509c1440aaaacb4fd7c593b80/live']
                   }

res_names_dict = {
    'england': {'Манчестер Юн': 'Манчестер Юнайтед',   'Кристал П': 'Кристал Пэлас',   'Арсенал': 'Арсенал Лондон'},
 
 'germany': {'Боруссия М': 'Боруссия Мёнхенгладбах',   'Арминия': 'Арминия Билефельд',   'Унион': 'Унион Берлин',
   'Байер': 'Байер Леверкузен',   'Боруссия Д': 'Боруссия Дортмунд',   'А.Франкфурт': 'Айнтрахт Франкфурт'},
 
 'spain': {'Реал': 'Реал Мадрид',   'Атлетико М': 'Атлетико Мадрид',   'Атлетик Б': 'Атлетик Бильбао'},
 
 'italy': {'Интер': 'Интер Милан'},
 
 'france': {'Марсель': 'Марсель'},
 
 'belgium': {'ОХ Левен': 'Ауд-Хеверле Лёвен',   'Зюлте-Варегем': 'Зюльте-Варегем',   'Сент-Трюйден': 'Сент-Трёйден',
   'Сен-Жилуаз': 'Юнион Сен-Жилуаз',   'Серкль': 'Серкль Брюгге'},
 
 'netherlands': {'Гоу Эхед Иглс': 'Гоу Эхед Иглз',   'Фортуна': 'Фортуна Ситтард',   'АЗ': 'АЗ Алкмар',
   'ПСВ Эйндховен': 'ПСВ',   'Спарта Р': 'Спарта Роттердам'},
 
 'portugal': {'Спортинг': 'Спортинг Лиссабон',   'Гимарайнш': 'Витория Гимарайнш',   'Брага': 'Спортинг Брага',
   'Портимоненше': 'Портимоненси',   'Санта Клара': 'Санта-Клара',   'Белененсеш': 'Белененсиш'},
 
 'turkey': {'Карагюмрюк': 'Фатих Карагюмрюк СК',   'Алтай': 'Алтай Измир',   'Башакшехир': 'Истанбул Башакшехир',
   'Газиантеп': 'ФК Газиантеп',   'Малатьяспор': 'Йени Малатьяспор'}
   # 'Аданадемирспор': 
   ,

'czech': {'Градец-Кралове': 'Градец Кралове', 'Богемианс 1905': 'Богемианс 1905', 'Виктория': 'Виктория Пльзень', 'Млада Болеслав': 'Млада-Болеслав', 
          'Пардубице': 'Пардубице', 'Карвина': 'Карвина', 'Слован Л': 'Слован Либерец', 'Словацко': 'Словацко', 
          'Яблонец': 'Яблонец', 'Баник': 'Баник Острава', 'Динамо Ч-Б': 'Динамо Ческе-Будеёвице', 'Теплице': 'Теплице', 
          'Спарта П': 'Спарта Прага', 'Сигма': 'Сигма', 'Злин': 'Злин', 'Славия П': 'Славия Прага'},

'poland': {'Лех': 'Лех Познань',   'Гурник Л': 'Гурник Ленчна',   'Легия': 'Легия Варшава',   'Радомяк': 'Радомьяк Радом', 'Лехия': 'Лехия Гданьск',
           'Висла П': 'Висла Плоцк',  'Шленск': 'Шлёнск Вроцлав',   'Погонь': 'Погонь Щецин',  'Висла К': 'Висла Краков',   'Ракув': 'Ракув Ченстохова',   
           'Варта': 'Варта Познань',     'Гурник': 'Гурник Забже',  'Заглембе Л': 'Заглембе Любин', 'Термалица': 'Нецеча','Пьяст': 'Пяст Гливице'},

'greece': {'Астерас': 'Астерас Триполис', 'АЕК': 'АЕК Афины', 'Олимпиакос': 'Олимпиакос Пирей', 'Арис': 'Арис Салоники', 
           'Атромитос': 'Атромитос Афины'},
            # 'Волос': '',  'Аполлон': ''

'scotland': {'Данди': 'Данди ФК'},

'swiss': {'Базель': 'Базель'}
                }

TRNT_DICT = {
 'england': 0,
 'germany': 1,
 'spain': 2,
 'italy': 3,
 'france': 4,
 'belgium': 5,
 'netherlands': 6,
 'portugal': 7,
 'turkey': 8,
 'czech': 9,
 'poland': 10,
 'greece': 11}

lag_list = \
    [
    ['3M',  relativedelta(minutes = 3)],
    ['6M',  relativedelta(minutes = 6)],
#     ['10M', relativedelta(minutes = 10)],
#     ['15M', relativedelta(minutes = 15)],
#     ['20M', relativedelta(minutes = 20)],
#     ['25M', relativedelta(minutes = 25)],
    ['30M', relativedelta(minutes = 30)],
    ['1H',  relativedelta(hours = 1)   ]
#     ['2H',  relativedelta(hours = 2)   ],
#     ['3H',  relativedelta(hours = 3)   ]
    ]

lag_live_list = \
    [
    ['2M',    relativedelta(minutes = 2)],
    ['5M',    relativedelta(minutes = 5)],
    # ['15M',   relativedelta(minutes = 15)],
    ['30M',   relativedelta(minutes = 30)],
    # ['TIMEOUT', relativedelta(hours = 1) ],
    ['60M',    relativedelta(minutes = 60 + 18)],
    # ['75M',   relativedelta(minutes = 75 + 18)],
    # ['90M',   relativedelta(minutes = 90 + 18)]
    ]


