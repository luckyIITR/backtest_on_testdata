import pandas as pd
import os
import sqlite3
import datetime as dt
dbd = r'F:\Database\5min_data'
#Connecting to Database
db = sqlite3.connect(os.path.join(dbd,"NSEEQ.db"))

def get_intra_data(symbol):
    symbol_check = {'3MINDIA': 'MINDIA',
                    'BAJAJ-AUTO': 'BAJAJAUTO',
                    'J&KBANK': 'JKBANK',
                    'L&TFH': 'LTFH',
                    'M&MFIN': 'MMFIN',
                    'M&M': 'MM',
                    'NAM-INDIA': 'NAMINDIA',
                    'MCDOWELL-N': 'MCDOWELLN'}
    symbol = symbol[:-3]
    if symbol in list(symbol_check.keys()):
        symbol = symbol_check[symbol]

    df = pd.read_sql('''SELECT * FROM %s;''' % symbol, con=db)
    df.set_index('time', inplace=True)
    df.reset_index(inplace=True)
    df['time'] = pd.to_datetime(df['time'])
    df.set_index("time", drop=True, inplace=True)
    df.index[0]
    df.drop(["oi", 'Volume'], axis=1, inplace=True)
    return df

df = get_intra_data("SBIN.NS")
df = df[df.index.date >= dt.datetime(2020,11,1,0,0).date()]
db.close()