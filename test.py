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


# In[5]:

import sys
# appending a path
sys.path.append(r'C:\Users\acer\Desktop\RUSLAN\PM')
from classes_opt import *


# # КОНЕЦ НЕДЕЛИ
# # Парсим результаты игр
# 

# In[22]:


df_week = pd.read_excel('df_week.xlsx', index_col = 0)
df_week.drop(columns = ['OBSDT'], inplace = True)
df_week


# In[9]:


CHAMPS = list(df_week['COUNTRY'].unique())
display(CHAMPS)


# In[10]:


res_list = []
for elem in CHAMPS:
    print(elem)
    res_page = result_page(COUNTRY = elem, TOURNAMENT = data_list[elem][0])
    res_page.download_webpage(URL = data_list[elem][2])
    df_res = res_page.df_games
    df_res['HT'] = df_res['HT'].apply(lambda x: res_names_dict[elem][x] if x in res_names_dict[elem].keys() else x)
    df_res['GT'] = df_res['GT'].apply(lambda x: res_names_dict[elem][x] if x in res_names_dict[elem].keys() else x)
    display(df_res)
    res_list.append(df_res)


# In[23]:


df_res = pd.concat(res_list).copy()
print('df_res concatenated:')
display(df_res)


# #  6. Загружаем результаты в df_week

# In[24]:


df_week_res = df_week.copy()


# In[25]:


df_week_res['DATE'] = df_week_res['GAME_DT'].dt.date


# In[26]:


df_week_res = df_week_res.merge(df_res[['HT', 'GT', 'DATE', 'RESULT']], how = 'left', on = ['HT', 'GT', 'DATE'])


# In[28]:


df_week_res['DELTA_GOALS'] = df_week_res.apply(
    lambda row: int(re.findall(r'\w*:', row['RESULT'])[0][:-1]) - int(re.findall(r':\w*', row['RESULT'])[0][1:])
                    if not pd.isnull(row['RESULT']) else np.nan, axis = 1) 


# In[29]:


df_week_res['RESULT_CODE'] = df_week_res.apply(lambda row:
                  'DR' if row['DELTA_GOALS'] == 0 else 
                      ('HW' if row['DELTA_GOALS'] > 0 else ('GW' if row['DELTA_GOALS'] < 0 else np.nan)), axis = 1)


# In[30]:


df_week_res = df_week_res[['GAME_ID',  'COUNTRY', 'TOURNAMENT', 'GAME_DT', 'HT', 'GT', 'RESULT', 'RESULT_CODE',
            'HWC_3M', 'DRC_3M', 'GWC_3M', 'HWC_6M', 'DRC_6M', 'GWC_6M',
           'HWC_30M', 'DRC_30M', 'GWC_30M'  ,'HWC_1H', 'DRC_1H', 'GWC_1H'
                  ]].copy()


# In[31]:


print('df_week_res with results')
display(df_week_res)
df_week_res.to_excel(f'df_week_res.xlsx')

df_week_res[df_week_res['RESULT'].isna()].to_excel('unknown_games.xlsx')

# # 7. Загружаем содержимое weekly_dataset в general_dataset

# In[33]:


df_general = pd.read_excel('df_general.xlsx', index_col=0, encoding = 'utf-8-sig')
df_general


# In[34]:


ID_MAX = len(df_general)
display(ID_MAX)


# In[35]:


df_week_res['GAME_ID'] = df_week_res['GAME_ID'] + ID_MAX


# In[37]:


df_general = pd.concat([df_general, df_week_res]).reset_index(drop = True)
df_general.to_excel(f'df_general.xlsx', encoding = 'utf-8-sig')


# In[39]:


aa = pd.read_excel(f'df_general.xlsx', index_col=0, encoding = 'utf-8-sig')
print('general dataset after filling')
display(aa)
del aa


# In[ ]:




