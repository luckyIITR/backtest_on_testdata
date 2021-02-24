
import datetime as dt
import pandas as pd
import numpy as np
import time
import yfinance as yf
import matplotlib.pyplot as plt
import os
import sqlite3

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
    df = df[df.index.date >= dt.datetime(2020, 11, 1, 0, 0).date()]
    return df

# def get_intra_data(symbol):
#     daily = yf.download(tickers=symbol,  interval="5m", period="4d")
#     daily.index = daily.index.tz_localize(None)
#     daily.drop(["Adj Close", 'Volume'], axis=1, inplace=True)
#     daily["pre_close"] = daily['Close'].shift(1)
#     daily["pre_low"] = daily['Low'].shift(1)
#     daily["pre_high"] = daily['High'].shift(1)
#     return daily


def atr(DF,n):
    "function to calculate True Range and Average True Range"
    df = DF.copy()
    df['H-L']=abs(df['High']-df['Low'])
    df['H-PC']=abs(df['High']-df['Close'].shift(1))
    df['L-PC']=abs(df['Low']-df['Close'].shift(1))
    df['TR']=df[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
    df['ATR'] = df['TR'].ewm(com=n,min_periods=n).mean()
    return df['ATR']


def supertrend(DF,n,m):
    """function to calculate Supertrend given historical candle data
        n = n day ATR - usually 7 day ATR is used
        m = multiplier - usually 2 or 3 is used"""
    df = DF.copy()
    df['ATR'] = atr(df,n)
    df["B-U"]=((df['High']+df['Low'])/2) + m*df['ATR']
    df["B-L"]=((df['High']+df['Low'])/2) - m*df['ATR']
    df["U-B"]=df["B-U"]
    df["L-B"]=df["B-L"]
    ind = df.index
    for i in range(n,len(df)):
        if df['Close'][i-1]<=df['U-B'][i-1]:
            df.loc[ind[i],'U-B']=min(df['B-U'][i],df['U-B'][i-1])
        else:
            df.loc[ind[i],'U-B']=df['B-U'][i]
    for i in range(n,len(df)):
        if df['Close'][i-1]>=df['L-B'][i-1]:
            df.loc[ind[i],'L-B']=max(df['B-L'][i],df['L-B'][i-1])
        else:
            df.loc[ind[i],'L-B']=df['B-L'][i]
    df['Strend']=np.nan
    for test in range(n,len(df)):
        if df['Close'][test-1]<=df['U-B'][test-1] and df['Close'][test]>df['U-B'][test]:
            df.loc[ind[test],'Strend']=df['L-B'][test]
            break
        if df['Close'][test-1]>=df['L-B'][test-1] and df['Close'][test]<df['L-B'][test]:
            df.loc[ind[test],'Strend']=df['U-B'][test]
            break
    for i in range(test+1,len(df)):
        if df['Strend'][i-1]==df['U-B'][i-1] and df['Close'][i]<=df['U-B'][i]:
            df.loc[ind[i],'Strend']=df['U-B'][i]
        elif  df['Strend'][i-1]==df['U-B'][i-1] and df['Close'][i]>=df['U-B'][i]:
            df.loc[ind[i],'Strend']=df['L-B'][i]
        elif df['Strend'][i-1]==df['L-B'][i-1] and df['Close'][i]>=df['L-B'][i]:
            df.loc[ind[i],'Strend']=df['L-B'][i]
        elif df['Strend'][i-1]==df['L-B'][i-1] and df['Close'][i]<=df['L-B'][i]:
            df.loc[ind[i],'Strend']=df['U-B'][i]
    return df['Strend']


def st_dir_refresh(ohlc,ticker,e,shifted):
    """function to check for supertrend reversal"""
    global st_dir
    if ohlc.loc[e,"st1"] > ohlc.loc[e,"Close"] and shifted.loc[e,"st1"] < shifted.loc[e,"Close"]:
        st_dir[ticker][0] = "red"
    if ohlc.loc[e,"st1"] < ohlc.loc[e,"Close"] and shifted.loc[e,"st1"] > shifted.loc[e,"Close"]:
        st_dir[ticker][0] = "green"

def sl_price(ohlc,e):
    """function to calculate stop loss based on supertrends"""
    st = ohlc.loc[e,['st1','st2','st3']]
    if st.min() > ohlc.loc[e,"Close"]:
        sl = (0.6*st.sort_values(ascending = True)[0]) + (0.4*st.sort_values(ascending = True)[1])
    elif st.max() < ohlc.loc[e,"Close"]:
        sl = (0.6*st.sort_values(ascending = False)[0]) + (0.4*st.sort_values(ascending = False)[1])
    else:
        sl = st.mean()
    return round(sl,1)

def get_para():
    df = pd.read_csv('Nifty50.csv', header=0, index_col=0)
    return df


# tickers = ['PNB.NS']

def main():
    p_l = []
    para = get_para()
    n = 50
    tickers = ['AXISBANK.NS', 'BAJAJFINSV.NS', 'BAJFINANCE.NS', 'COALINDIA.NS',
       'DRREDDY.NS', 'GRASIM.NS', 'HCLTECH.NS', 'HDFC.NS', 'HDFCBANK.NS',
       'HEROMOTOCO.NS', 'HINDALCO.NS', 'ICICIBANK.NS', 'INDUSINDBK.NS',
       'IOC.NS', 'KOTAKBANK.NS', 'LT.NS', 'M&M.NS', 'MARUTI.NS', 'ONGC.NS',
       'POWERGRID.NS', 'SBIN.NS', 'TATAMOTORS.NS', 'TATASTEEL.NS', 'UPL.NS',
       'WIPRO.NS']
    # tickers = ['PNB.NS']
    # ticker = tickers[0]
    # tickers to track - recommended to use max movers from previous day
    capital = 3000  # position size
    global st_dir
    st_dir = {}  # directory to store super trend status for each ticker


    for ticker in tickers:
        st_dir[ticker] = ["None"]
        print("starting passthrough for.....",ticker)
        ohlc = get_intra_data(ticker)
        ohlc["st1"] = supertrend(ohlc, para.loc[ticker,'p'], para.loc[ticker,'q'])
        # ohlc["st1"] = supertrend(ohlc, p, m)
        # ohlc["st2"] = supertrend(ohlc, q, n)
        # ohlc["st3"] = supertrend(ohlc, r, o)
        ohlc.dropna(inplace=True)

        # today[["st1","st2","st3"]].plot()

        pos = 0
        percentchange = []
        st_dir[ticker] = ["None"]
        # today = get_only_today_data(ohlc, g)
        today = ohlc
        shifted = ohlc[['Close','st1']].shift(1)
        for e in today.index:
            if e == today.index[0]:
                continue
            if e.time() == dt.datetime(2020, 2, 5, 15, 25).time() or e.time() == dt.datetime(2020, 2, 5, 15, 20).time():
                pos = 0
                continue
            # sl = sl_price(today, e)
            st_dir_refresh(today, ticker, e, shifted)
            # if st_dir[ticker] == ["green", "green", "green"]: break
            quantity = int(capital / today.loc[e, "Close"])
            if pos == 0 and e.time() != dt.datetime(2020, 2, 5, 15, 15).time():
                if st_dir[ticker] == ["green"]:
                    pos = 1
                    bp = today.loc[e, "Close"]
                    # print(f"Buying at : {bp}  time : {e}")
                    continue
                if st_dir[ticker] == ["red"]:
                    pos = -1
                    sp = today.loc[e, "Close"]
                    # print(f"Selling at : {sp}  time : {e}")
                    continue
            if pos == 1 and st_dir[ticker] == ["red"] and e.time() != dt.datetime(2020, 2, 5, 15,15).time():
                sp = today.loc[e, "Close"]
                pos = -1
                pc = (sp / bp - 1) * 100
                # print(f"Selling at : {sp}  time : {e} and pc : {pc}")
                percentchange.append(pc)
                continue
            if pos == -1 and st_dir[ticker] == ["green"] and e.time() != dt.datetime(2020, 2, 5, 15,15).time():
                bp = today.loc[e, "Close"]
                pos = 1
                pc = (1 - (bp / sp)) * 100
                # print(f"Buying at : {bp}  time : {e} and pc : {pc}")
                percentchange.append(pc)
                continue
            if pos == 1 and e.time() == dt.datetime(2020, 2, 5, 15, 15).time():
                pos = 0
                sp = today.loc[e, "Open"]
                pc = (sp / bp - 1) * 100
                # print(f"**Selling at : {sp}  time : {e} and pc : {pc}")
                percentchange.append(pc)
                continue
            elif pos == -1 and e.time() == dt.datetime(2020, 2, 5, 15, 15).time():
                pos = 0
                bp = today.loc[e, "Open"]
                pc = (1 - (bp / sp)) * 100
                # print(f"***Buying at : {bp}  time : {e} and pc : {pc}")
                percentchange.append(pc)
                continue

        print(f"{ticker} : {np.array(percentchange).cumsum()[-1]}%")
        p_l.append(np.array(percentchange).cumsum()[-1])
        # plt.plot(np.array(percentchange).cumsum())
st_dir = {}
main()

