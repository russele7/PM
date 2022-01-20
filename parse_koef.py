#!/usr/bin/env python
# coding: utf-8

# In[4]:


from selenium import webdriver
from time import sleep, strftime
import pause
import html_to_json
import pandas as pd
import numpy as np
from datetime import datetime as dt
from itertools import chain
from tqdm import tqdm
from dateutil.relativedelta import relativedelta
import sqlite3
import os
import re
from IPython.display import display

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pretty_html_table import build_table

def send_mail(subject, body):
    
    message = MIMEMultipart()
    message['Subject'] = 'PM_' + subject
    message['From'] = 'russele7oge@gmail.com'
    message['To'] = 'russele7oge@gmail.com'

    body_content = build_table(body, 'blue_light')
    message.attach(MIMEText(body_content, "html"))
    msg_body = message.as_string()

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(message['From'], 'vmujqiiclzpfdlxu')
    server.sendmail(message['From'], message['To'], msg_body)
    server.quit()


# In[9]:


import sys
# appending a path
sys.path.append(r'C:\Users\acer\Desktop\RUSLAN\PM')
from classes_opt import *


# In[6]:

print('abra')
CHAMPS = list(data_list.keys())
display(CHAMPS)

# In[7]:


END_DAY_TIME = dt.now().replace(hour = 23, minute = 55, second = 0, microsecond = 0)
display(f'END_DAY_TIME = {END_DAY_TIME}')


# # 1. ПАРСИНГ РАСПИСАНИЯ ИГР

# In[10]:


data_champ_list = []
for elem in CHAMPS:
    print(elem)    
    try:
        page = sport_page(COUNTRY = elem, TOURNAMENT = data_list[elem][0])
        page.download_webpage(URL = data_list[elem][1])
        data = page.df_games
        data.reset_index(inplace = True)
        data.rename(columns = {'index':'GAME_ID'}, inplace = True)
        data_champ_list.append(data)
    except:
        aa = dt.now()
        print(f"ERROR with download <{elem}> / time = {aa}")
        with open('errors.txt', 'a+') as file:
            file.write(f"ERROR with download <{elem}> / time = {aa}")
            file.close()
        del aa

# In[11]:


data = pd.concat(data_champ_list).copy()
print('parced data')
data.to_excel(f'data_parced.xlsx')
display(data)


# In[12]:


data = data[
      (data['GAME_DT'].apply(lambda x: x.toordinal()) <= END_DAY_TIME.toordinal())
      & ~(data['HT'].apply(lambda x:  'Хозяева' in x))  
      & ~(data['GT'].apply(lambda x:  'Гости' in x ))
].copy()
data.sort_values('GAME_DT', ascending = True, inplace = True)
data.reset_index(drop = True,inplace = True)
data['GAME_ID'] = data.index


# In[13]:

print('data daily')
display(data[['GAME_DT', 'HT', 'GT', 'COUNTRY', 'TOURNAMENT', 'HW_COEF', 'DR_COEF', 'GW_COEF']])
data.to_excel(f'data_daily.xlsx')

# In[14]:

if len(data) == 0:
    print(f'TODAY IS NO GAMES _ {str(dt.today())}')
    with open(f'report.txt', 'w') as f:
        f.write(f'TODAY IS NO GAMES _ {str(dt.today())}')
        f.close()
    sys.exit()


# In[15]:


data_interesting = data[(data['DR_COEF'] >= 3.) & (abs(data['HW_COEF'] - data['GW_COEF']) < 0.5 )][
    ['GAME_DT', 'HT', 'GT', 'COUNTRY', 'TOURNAMENT', 'HW_COEF', 'DR_COEF', 'GW_COEF']].copy()

print('data interesting')
display(data_interesting)

data_interesting.to_excel(f'data_interesting.xlsx')


# # 2. Пересоздаем  df_week и  помещаем туда распарсенные данные

# In[26]:


df_week = data.drop(columns = ['HW_COEF', 'DR_COEF', 'GW_COEF'])
df_week
for elem in lag_list:
    df_week[f'HWC_{elem[0]}'] = np.nan
    df_week[f'DRC_{elem[0]}'] = np.nan
    df_week[f'GWC_{elem[0]}'] = np.nan


# In[27]:


print('df_week')
df_week.to_excel(f'df_week.xlsx')
display(df_week)


# In[30]:


CHAMPS = list(df_week['COUNTRY'].unique())
CHAMPS


# # 3. Берем dt игр => вычисляем dt лагов для каждой игры

# In[31]:


df_lag = data[['HT', 'GT', 'COUNTRY' , 'TOURNAMENT', 'GAME_DT']].copy()
for elem in lag_list:
    df_lag[f'LAG_DT_{elem[0]}'] = df_lag['GAME_DT'].apply(lambda x: x - elem[1])
df_lag.drop(columns = ['GAME_DT'], inplace= True)


# In[32]:


df_lag = df_lag.melt(
    id_vars=['HT', 'GT', 'COUNTRY', 'TOURNAMENT'],
    value_vars=None,
    var_name='LAG_TYPE',
    value_name='LAG_DT',
    col_level=None)


# In[33]:


print('df_lag')
df_lag.to_excel('df_lag.xlsx')
display(df_lag)


# ## 4. БЕРЕМ УНИКАЛЬНЫЕ ЗНАЧЕНИЯ времен для парсинга

# In[34]:


lag_parse_time = df_lag.pivot_table(index = 'LAG_DT', columns = 'COUNTRY', values = 'HT', aggfunc = 'count').reset_index()
lag_parse_time.rename_axis(None, axis=1, inplace = True)
lag_parse_time.rename(columns = {'LAG_DT' : 'PARSE_DT'}, inplace = True)
print('lag_parse_time')
lag_parse_time.to_excel('lag_parse_time.xlsx')
display(lag_parse_time)


# ## 5. В ТЕЧЕНИЕ НЕДЕЛИ
# ## В цикле в момент dt_lag делаем парсинг коэффициентов и помещаем их в df_week

# In[42]:


def fill_the_week(dpage, dlag, df_week_in):    
    df_slice = dpage.merge(dlag, how = 'left', on = ['HT', 'GT', 'TOURNAMENT'])
    df_slice['DELTA_SEC'] = (df_slice['OBSDT'] - df_slice['LAG_DT']).apply(lambda x: x.total_seconds())
    print('df_slice BEFORE CUT [DELTA_SEC] < 2 minutes')
    display(df_slice)    
    df_slice = df_slice[
        (df_slice['DELTA_SEC'] < 60*2.5)      # 60 * 2.5
        & (df_slice['DELTA_SEC'] >= 0)   # 0
    ].reset_index(drop = True)
    print('df_slice AFTER CUT [DELTA_SEC] < 2 minutes')
    display(df_slice)
    # Заполняем weekly значениями из slice
    df_week_out = df_week_in.copy()
    for j in range(len(df_slice)):
        row = df_slice.loc[[j]]
        pref = row['LAG_TYPE'].values[0][7:]
        df_week_out.loc[
            ( 
                (df_week_out['HT']  == row['HT'].values[0])   
              & (df_week_out['GT']  == row['GT'].values[0])
              & (df_week_out['TOURNAMENT']  == row['TOURNAMENT'].values[0])
            ),[
                f'HWC_{pref}', f'DRC_{pref}', f'GWC_{pref}']] = row[['HW_COEF', 'DR_COEF', 'GW_COEF']].values 
#     display(df_week_out)
    return df_week_out


# In[43]:


# В цикле перебираем упорядоченные по времени начала моменты времени для парсинга 
for i in range(len(lag_parse_time)):
    print(f"i = {i} / lag_parse_time = {lag_parse_time.loc[i]['PARSE_DT']}" )
    if dt.now() < lag_parse_time.loc[i]['PARSE_DT']:
        print(f'DO IF / current_time = {dt.now().replace(microsecond = 0)}')
        # Выжидаем до момента парсинга
        pause.until(lag_parse_time.loc[i]['PARSE_DT'])
        print(f'time after waiting = {dt.now().replace(microsecond = 0)}')

        # Выделяем чемпионаты в которых есть нужные игры по времени  PARSE_DT 
        bb = lag_parse_time.loc[i][CHAMPS].to_frame().reset_index()
        parse_list = list(bb[~bb[i].isna()]['index'])
        print(f'parse_list = {parse_list}')
        
         # Делаем парсинг
        data_champ_list2 = []
        for elem in parse_list:
        	try:
	            page2 = sport_page(COUNTRY = elem, TOURNAMENT = data_list[elem][0])
	            page2.download_webpage(URL = data_list[elem][1])
	            data2 = page2.df_games    
	            data2.reset_index(inplace = True)
	            data2.rename(columns = {'index':'GAME_ID'}, inplace = True)
	            data_champ_list2.append(data2)
	        except:
	        	aa = lag_parse_time.loc[i]['PARSE_DT']
	        	print(f"ERROR with download <{elem}> / time = {aa}")
	        	with open('errors.txt', 'a+') as file:
	        		file.write(f"ERROR with download <{elem}> / time = {aa}")
	        		file.close()
	        	del aa

        data2 = pd.concat(data_champ_list2).copy()
        data2 = data2.loc[data2['GAME_DT'] < END_DAY_TIME].copy()
        data2.reset_index(drop = True,inplace = True)
        data2.reset_index(inplace = True)
        data2.drop(columns = ['GAME_ID'], inplace = True)
        data2.rename(columns = {'index':'GAME_ID'}, inplace = True)
        
        # Дополняем weekly спарсенными значениями
        df_week = fill_the_week(dpage = data2, dlag = df_lag, df_week_in = df_week)
        
        print('df_week')
        display(df_week)
        print('df_week_short')
        display(df_week[['GAME_DT', 'HT', 'GT', 'COUNTRY', 'HWC_3M', 'DRC_3M', 'GWC_3M']])
        df_week.to_excel(f'df_week.xlsx')

        # Рассылка email интересных матчей        
        df_int = df_week[
                    (df_week['DRC_3M'] >= 3.) 
                   & (abs(df_week['HWC_3M'] - df_week['GWC_3M']) <= 0.15)
                   & ((df_week['GAME_DT'] - lag_parse_time.loc[i]['PARSE_DT']).apply(lambda x: x.total_seconds()) <= 60*3)
                   & ((df_week['GAME_DT'] - lag_parse_time.loc[i]['PARSE_DT']).apply(lambda x: x.total_seconds()) > 0)
                        ][['GAME_DT', 'HT', 'GT', 'COUNTRY', 'HWC_3M', 'DRC_3M', 'GWC_3M']].copy()
        df_int.to_excel(f'df_int.xlsx')
        print('df_int')
        display(df_int)
        
        display(r"(df_week['DRC_3M'] >= 3.)")
        display((df_week['DRC_3M'] >= 3.))

        display(r"(abs(df_week['HWC_3M'] - df_week['GWC_3M']) <= 0.15)")
        display((abs(df_week['HWC_3M'] - df_week['GWC_3M']) <= 0.15))

        display(r"((df_week['GAME_DT'] - lag_parse_time.loc[i]['PARSE_DT']).apply(lambda x: x.total_seconds()) <= 60*3)")
        display(((df_week['GAME_DT'] - lag_parse_time.loc[i]['PARSE_DT']).apply(lambda x: x.total_seconds()) <= 60*3))

        display(r"((df_week['GAME_DT'] - lag_parse_time.loc[i]['PARSE_DT']).apply(lambda x: x.total_seconds()) == 60*3)")
        display(((df_week['GAME_DT'] - lag_parse_time.loc[i]['PARSE_DT']).apply(lambda x: x.total_seconds()) == 60*3))

        display(r"((df_week['GAME_DT'] - lag_parse_time.loc[i]['PARSE_DT']).apply(lambda x: x.total_seconds()) > 0)")
        display(((df_week['GAME_DT'] - lag_parse_time.loc[i]['PARSE_DT']).apply(lambda x: x.total_seconds()) > 0))



        if (len(df_int) > 0):
            send_mail(subject = '_'.join(df_int['COUNTRY'].to_list()), body = df_int)
            print('EMAIL with df_int delivered')