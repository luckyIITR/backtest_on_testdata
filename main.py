
import datetime as dt
import pandas as pd
import numpy as np
import time
import yfinance as yf
import matplotlib.pyplot as plt

def get_intra_data(symbol,n):
    data = yf.download(tickers=symbol, interval="5m", period=f"{n}d", end=dt.datetime.now())
    data.index = data.index.tz_localize(None)
    data.drop(["Adj Close", 'Volume'], axis=1, inplace=True)
    return data


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



tickers = ['GUJGASLTD.NS', 'ADANITRANS.NS', 'CONCOR.NS', 'M&M.NS',
       'DALBHARAT.NS', 'RAMCOCEM.NS', 'TATAMOTORS.NS', 'HINDALCO.NS',
       'EXIDEIND.NS', 'ADANIENT.NS', 'AUBANK.NS', 'NAUKRI.NS', 'SAIL.NS',
       'SHREECEM.NS', 'MOTHERSUMI.NS', 'COFORGE.NS', 'M&MFIN.NS',
       'BHARATFORG.NS', 'HDFCAMC.NS', 'AMARAJABAT.NS', 'IRCTC.NS',
       'VOLTAS.NS', 'MPHASIS.NS', 'GSPL.NS', 'MINDTREE.NS', 'PGHH.NS',
       'JSWSTEEL.NS', 'BAJAJFINSV.NS', 'BERGEPAINT.NS', 'ASHOKLEY.NS',
       'PEL.NS', 'CASTROLIND.NS', 'APOLLOTYRE.NS', 'INDHOTEL.NS',
       'INFY.NS', 'ADANIPORTS.NS', 'TATAPOWER.NS', 'BHARTIARTL.NS',
       'BATAINDIA.NS', 'GAIL.NS', 'SRTRANSFIN.NS', 'BOSCHLTD.NS',
       'POLYCAB.NS', 'BALKRISIND.NS', 'TECHM.NS', 'TATASTEEL.NS',
       'WIPRO.NS', 'COROMANDEL.NS', 'ICICIBANK.NS', 'MGL.NS', 'LT.NS',
       'ACC.NS', 'JINDALSTEL.NS', 'CHOLAFIN.NS', 'POWERGRID.NS',
       'GODREJPROP.NS', 'ZEEL.NS', 'DLF.NS', 'TITAN.NS', 'AXISBANK.NS',
       'ESCORTS.NS', 'HINDPETRO.NS', 'SIEMENS.NS', 'GRASIM.NS',
       'DMART.NS', 'TCS.NS', 'ASIANPAINT.NS', 'EDELWEISS.NS', 'IOC.NS',
       'BAJAJHLDNG.NS', 'ABCAPITAL.NS', 'JUBLFOOD.NS', 'HAVELLS.NS',
       'TVSMOTOR.NS', 'ONGC.NS', 'TATACHEM.NS', 'MFSL.NS',
       'IDFCFIRSTB.NS', 'INDUSTOWER.NS', 'HEROMOTOCO.NS', 'INDIGO.NS',
       'AUROPHARMA.NS', 'IGL.NS', 'PFC.NS', 'RELIANCE.NS', 'EICHERMOT.NS',
       'TORNTPOWER.NS', 'JSWENERGY.NS', 'HCLTECH.NS', 'HUDCO.NS',
       'NMDC.NS', 'MUTHOOTFIN.NS', 'SRF.NS', 'IBULHSGFIN.NS',
       'DRREDDY.NS', 'INDUSINDBK.NS', 'BEL.NS', 'HINDZINC.NS', 'BPCL.NS',
       'YESBANK.NS', 'LICHSGFIN.NS', 'AMBUJACEM.NS', 'MARUTI.NS',
       'MARICO.NS', 'GMRINFRA.NS', 'TATACONSUM.NS', 'IPCALAB.NS',
       'NTPC.NS', 'RECLTD.NS', 'ICICIPRULI.NS', 'CUB.NS', 'PRESTIGE.NS',
       'HDFCBANK.NS', 'SBIN.NS', 'OIL.NS', 'NATIONALUM.NS',
       'CUMMINSIND.NS', 'SANOFI.NS', 'HDFC.NS', 'PIDILITIND.NS',
       'BANDHANBNK.NS', 'SYNGENE.NS', 'NESTLEIND.NS', 'LALPATHLAB.NS',
       'ULTRACEMCO.NS', 'ICICIGI.NS', 'FORTIS.NS', 'TRENT.NS',
       'SBICARD.NS', 'AJANTPHARM.NS', 'APLLTD.NS', 'COALINDIA.NS',
       'UPL.NS', 'HDFCLIFE.NS', 'BIOCON.NS', 'MRF.NS', 'L&TFH.NS',
       'ABBOTINDIA.NS', 'GLENMARK.NS', 'DHANI.NS', 'OBEROIRLTY.NS',
       'ATGL.NS', 'RAJESHEXPO.NS', 'TORNTPHARM.NS', 'BAJAJ-AUTO.NS',
       'CIPLA.NS', 'AARTIIND.NS', 'LUPIN.NS', 'EMAMILTD.NS',
       'SUNPHARMA.NS', 'MCDOWELL-N.NS', 'FEDERALBNK.NS', 'BANKINDIA.NS',
       'ISEC.NS', 'COLPAL.NS', 'LTI.NS', 'NATCOPHARM.NS', 'CADILAHC.NS',
       'CESC.NS', 'NAM-INDIA.NS', 'ITC.NS', 'PAGEIND.NS', 'PIIND.NS',
       'APOLLOHOSP.NS', 'GICRE.NS', 'DABUR.NS', 'ENDURANCE.NS',
       'PFIZER.NS', 'CROMPTON.NS', 'SBILIFE.NS', 'SUNTV.NS', 'UBL.NS',
       'PETRONET.NS', 'BAJFINANCE.NS', 'NAVINFLUOR.NS', 'LTTS.NS',
       'DIVISLAB.NS', 'RBLBANK.NS', 'BANKBARODA.NS', 'FRETAIL.NS',
       'VBL.NS', 'GODREJIND.NS', 'KOTAKBANK.NS', 'ALKEM.NS',
       'HINDUNILVR.NS', 'ABFRL.NS', 'OFSS.NS', 'BBTC.NS', 'CANBK.NS',
       'ADANIGREEN.NS', 'BRITANNIA.NS', 'GODREJAGRO.NS', 'WHIRLPOOL.NS',
       'GODREJCP.NS', 'MANAPPURAM.NS', 'UNIONBANK.NS', 'IDEA.NS',
       'VGUARD.NS', 'PNB.NS', 'BHEL.NS']
tickers = ['PNB.NS']

def main():
    n = 50

    tickers = ['PNB.NS']
    # ticker = tickers[0]
    # tickers to track - recommended to use max movers from previous day
    capital = 3000  # position size
    global st_dir
    st_dir = {}  # directory to store super trend status for each ticker


    for ticker in tickers:
        st_dir[ticker] = ["None"]
        print("starting passthrough for.....",ticker)
        ohlc = get_intra_data(ticker,50)
        ohlc["st1"] = supertrend(ohlc, 5, 4)
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
                    print(f"Buying at : {bp}  time : {e}")
                    continue
                if st_dir[ticker] == ["red"]:
                    pos = -1
                    sp = today.loc[e, "Close"]
                    print(f"Selling at : {sp}  time : {e}")
                    continue
            if pos == 1 and st_dir[ticker] == ["red"] and e.time() != dt.datetime(2020, 2, 5, 15,15).time():
                sp = today.loc[e, "Close"]
                pos = -1
                pc = (sp / bp - 1) * 100
                print(f"Selling at : {sp}  time : {e} and pc : {pc}")
                percentchange.append(pc)
                continue
            if pos == -1 and st_dir[ticker] == ["green"] and e.time() != dt.datetime(2020, 2, 5, 15,15).time():
                bp = today.loc[e, "Close"]
                pos = 1
                pc = (1 - (bp / sp)) * 100
                print(f"Buying at : {bp}  time : {e} and pc : {pc}")
                percentchange.append(pc)
                continue
            if pos == 1 and e.time() == dt.datetime(2020, 2, 5, 15, 15).time():
                pos = 0
                sp = today.loc[e, "Open"]
                pc = (sp / bp - 1) * 100
                print(f"**Selling at : {sp}  time : {e} and pc : {pc}")
                percentchange.append(pc)
                continue
            elif pos == -1 and e.time() == dt.datetime(2020, 2, 5, 15, 15).time():
                pos = 0
                bp = today.loc[e, "Open"]
                pc = (1 - (bp / sp)) * 100
                print(f"***Buying at : {bp}  time : {e} and pc : {pc}")
                percentchange.append(pc)
                continue

        print(np.array(percentchange).cumsum()[-1])
        plt.plot(np.array(percentchange).cumsum())
st_dir = {}
main()