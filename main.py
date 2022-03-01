import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import glob
from pathlib import Path
from datetime import datetime
import urllib3
# from numba import jit

import yfinance as yahooFinance
import investpy

import kit as kit

pd.options.mode.chained_assignment = None  # default='warn'
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Asset:

    def __init__(self, ticker, name, source):
        self.ticker = ticker.upper()
        self.name = name
        self.source = source
        
    def get_asset_yahoo(self, ticker):
  
        ind = yahooFinance.Ticker(ticker).history(period="max")
        ind = ind["Close"]
        ind.name = ticker.split('.', 1)[0]

        return ind

    def get_asset_investing(self, ticker, name, date_beg='01/01/2009'):

        search = investpy.search_quotes(text=name, n_results=1)
        ind = search.retrieve_historical_data(from_date=date_beg, to_date=datetime.today().strftime('%d/%m/%Y'))["Close"]
        ind.name = ticker

        return ind

    def get_asset_local(self, ticker):

        ind = pd.read_csv(asset, sep=";", decimal=',').set_index('Date')
        ind.index = pd.to_datetime(ind.index, format="%d/%m/%Y")

        return ind

    def get_asset(self):
        
        if self.source.lower() == "yahoo":           
            prices = self.get_asset_yahoo(self.ticker)
        elif self.source.lower() == "investing":      
            prices = self.get_asset_investing(self.ticker, self.name)
        elif self.source.lower() == "csv":        
            prices = self.get_asset_local(self.ticker)
        else:
            raise ValueError(f"{self.source} is not a valid asset source")
        
        return pd.DataFrame(prices)
    
    
class Portfolio:
    
    def __init__(self, name, asset_list):
        self.name = name
        self.asset_list = asset_list

    ##### LOAD ####    
    def load(self):
        
        p = pd.concat([asset.get_asset() for asset in self.asset_list],axis=1)
        
        return p
    
    #### TRACK ####
    def frame_returns(self, p):
    
        r = p.pct_change()

        return r
    
    def create_trades(self):
    
        t = pd.DataFrame(columns=["Date", "Ticker", "Amount"])
        
        t = t.append({"Date": "07-01-2021","Ticker":"4GLD", "Amount":300.88}, ignore_index=True)
        t = t.append({"Date": "07-01-2021","Ticker":"XDEM", "Amount":3728.27}, ignore_index=True)
        t = t.append({"Date": "28-03-2021","Ticker":"4GLD", "Amount":-282.40}, ignore_index=True)
        t = t.append({"Date": "29-03-2021","Ticker":"4GLD", "Amount":273.24}, ignore_index=True)
        t = t.append({"Date": "14-07-2021","Ticker":"PRUD", "Amount":700.00}, ignore_index=True)
        t = t.append({"Date": "15-07-2021","Ticker":"FSMI", "Amount":2800.00}, ignore_index=True)
        t = t.append({"Date": "13-10-2021","Ticker":"WCOA", "Amount":2240.10}, ignore_index=True)
        t = t.append({"Date": "02-11-2021","Ticker":"ZPRS", "Amount":1494.57}, ignore_index=True)
        t = t.append({"Date": "02-11-2021","Ticker":"EUNZ", "Amount":1991.72}, ignore_index=True)
        t = t.append({"Date": "08-12-2021","Ticker":"BTC-EUR", "Amount":584.46}, ignore_index=True)
        t = t.append({"Date": "28-01-2022","Ticker":"4GLD", "Amount":518.20}, ignore_index=True)
        t = t.append({"Date": "28-01-2022","Ticker":"BRYN", "Amount":2487.15}, ignore_index=True)
        t = t.append({"Date": "11-02-2022","Ticker":"EUA", "Amount":624.00}, ignore_index=True)     

        return t

    def join_trades(self, r, t):
    
        t["Date"] = pd.to_datetime(t["Date"], format="%d-%m-%Y")
        t = t.set_index(["Ticker","Date"]).rename(columns={'Amount':'Trades'})
        r_stack = r.stack().reset_index().rename(columns={'level_1':'Ticker', 0: 'Returns'}).set_index(["Ticker", "Date"])
        rt = r_stack.join(t).unstack(level=0)
        rt.loc[:,"Trades"].fillna(0, inplace = True)

        return rt
    
    # @jit(nopython=True)
    def roll(self, a, b):
        res = np.empty(b.shape)
        res[0] = b[0]
        for i in range(1, res.shape[0]):
            res[i] = res[i-1] * (1 + a[i]) + b[i]
        return res

    def compute_wealth(self, rt):

        rtw = rt.copy()

        for i in rtw["Trades"].columns:
            rtw[("Total", i)] = self.roll(*np.nan_to_num(rtw[[("Returns", i), ("Trades", i)]].values.T))

        return rtw
    
    def portfolio_rets_weights(self, rtw):
    
        w = rtw["Total"].div(rtw["Total"].sum(axis=1), axis=0)   
        r = rtw["Returns"]   
        r['PORT'] =  (w * r).sum(axis=1) 

        return r, w
    
    def rolling_vol(self, r, time_period = 90, col_drop_plot = None):
    
        if col_drop_plot == None:
            roll_vol = r.rolling(time_period, min_periods = int(time_period*0.2)).apply(kit.annualize_vol)       
        else:
            roll_vol = r.drop(columns = col_drop_plot).rolling(time_period, min_periods = int(time_period*0.2)).apply(kit.annualize_vol)   
            
        roll_vol.plot(figsize=(16,5), title = '{}-periods rolling volatility'.format(time_period))
    
        return roll_vol

    def portfolio_report(self, df, weights = None, date_beg = None, date_end = None, col_drop_plot = None, time_period = 90):

        if date_end == None:
            date_end = df.index[-1]

        if col_drop_plot == None:
            (1+df.dropna())[date_beg:date_end].cumprod().plot(figsize=(16,5), title = 'Cumulative returns') #Plot wealth
            df.dropna()[date_beg:date_end].apply(lambda r: kit.drawdown(r).Drawdown).plot(figsize=(16,5), title = 'Drawdown') #Plot drawdown
        else:
            (1+df.drop(columns = col_drop_plot).dropna())[date_beg:date_end].cumprod().plot(figsize=(16,5), title = 'Cumulative returns') #Plot wealth
            df.drop(columns = col_drop_plot).dropna()[date_beg:date_end].apply(lambda r: kit.drawdown(r).Drawdown).plot(figsize=(16,5), title = 'Drawdown') #Plot drawdown

        stats = kit.summary_stats(df.dropna()[date_beg:date_end], riskfree_rate=0)
    #     roll_vol = rolling_vol(df.dropna()[date_beg:date_end], time_period = time_period, col_drop_plot = col_drop_plot)
    
        if weights is not None:
            weights.dropna().plot(figsize=(16,5), title = 'Portfolio weights')

        return stats
    
    def track(self):
        
        p = self.load()
        r = self.frame_returns(p)
        t = self.create_trades()
        rt = self.join_trades(r, t)
        self.rtw = self.compute_wealth(rt)
        self.r, self.w = self.portfolio_rets_weights(self.rtw)
        self.stats = self.portfolio_report(self.r, weights = self.w, date_beg = "2021-01-06", col_drop_plot = ["BTC-EUR", "EUA"])
        roll_vol = self.rolling_vol(self.r.dropna()["2021-01-06":], time_period = 90, col_drop_plot = ["BTC-EUR", "EUA"])
        
        return self.stats
    
    def backtest(self, freq = None, time_period = 90):
        '''
        freq: "W", "M", "B", default None
        '''
        
        w = self.w.copy()
        w.iloc[:-1,:]=np.nan
        w = w.fillna(method="bfill")

        r = self.rtw["Returns"] 
        if freq is not None:         
            r = r.resample(freq).apply(kit.compound)
        r['PORT'] = (w * r).sum(axis=1) 

        col_drop_plot = ["PRUD", "BTC-EUR", "ZPRS", "WCOA", "EUNZ", "4GLD", "FSMI", "BRYN", "EUA"]

        self.stats_long = self.portfolio_report(r, date_beg = "2017-12", weights = w, col_drop_plot = col_drop_plot, time_period = time_period)
        roll_vol = self.rolling_vol(r.dropna()["2017-12":], col_drop_plot = col_drop_plot, time_period = time_period)
        
        return self.stats_long
    
    def rolling_corr(self, r, time_period = 90, col= 'XDEM'):
    
        corr = r.rolling(time_period).corr()[col].unstack(level = 1)
        corr.plot(figsize=(16,5), title = '{}-periods rolling correlation'.format(time_period))
        
        return pd.DataFrame(corr.mean().sort_values(ascending = True)).T