# -*- coding: utf-8 -*-
"""
Created on Thu Feb 10 18:24:36 2022

@author: laurachen
"""
import requests
from time import sleep
import json

API_KEY = {'X-API-key': '2VX1D73B'}
fee = 0.02
ARB_ENTER_THRESHOLD = 0.2

class ApiException(Exception):
    pass

def get_tick(session):
    resp = session.get('http://localhost:9999/v1/case')
    if resp.ok:
        case = resp.json()
        return case['tick']
    raise ApiException('Authorization error. Please check API key.')

def ticker_bid_ask(session, ticker):
    payload = {'ticker': ticker}
    resp = session.get('http://localhost:9999/v1/securities/book', params=payload)
    if resp.ok:
        book = resp.json()
        return (book['bids'][0]['price'], book['asks'][0]['price'])
    raise ApiException('Authorization error. Please check API key.')

def make_order(ticker, orderType, quantity, action):
    with requests.Session() as s:
        s.headers.update(API_KEY)
        mkt_buy_params = {'ticker': ticker, 'type': orderType, 'quantity': quantity,
                   'action': action}
        resp = s.post('http://localhost:9999/v1/orders', params=mkt_buy_params)
        if resp.ok:
            mkt_order = resp.json()
            id = mkt_order['order_id']
            print('The market buy order was submitted and has ID', id)
        else:
            print('The order was not successfully submitted!')
            
def check_arbitrage(s):
    USDbid, USDask = ticker_bid_ask(s, 'USD')
    RITCbid, RITCask = ticker_bid_ask(s, 'RITC')
    Bullbid, Bullask = ticker_bid_ask(s, 'BULL')
    Bearbid, bearask = ticker_bid_ask(s, 'BEAR')
    ETF_overvalue = USDbid * RITCbid - Bullask - bearask - fee * 2 - fee * USDask
    stock_overvalue = Bullbid + Bearbid - USDask * RITCask - fee * 2 - fee * USDbid
    
    if ETF_overvalue > ARB_ENTER_THRESHOLD:
        return -1, 1 # sell ETF, buy stocks
    elif stock_overvalue > ARB_ENTER_THRESHOLD:
        return 1, -1 # Buy ETF sell stocks
    else: 
        return 0, 0
    
def main():   
    while True:
        with requests.Session() as s:
            s.headers.update(API_KEY)
            tick = get_tick(s)
            ETF_overvalue, stock_overvalue = check_arbitrage(s)
            
            if ETF_overvalue == -1 and stock_overvalue == 1:
                make_order('RITC', 'MARKET', 10, 'SELL')
                make_order('BULL', 'MARKET', 10, 'BUY')
                make_order('BEAR', 'MARKET', 10, 'BUY')
                break
            elif ETF_overvalue == 1 and stock_overvalue == -1:
                make_order('RITC', 'MARKET', 10, 'BUY')
                make_order('BULL', 'MARKET', 10, 'SELL')
                make_order('BEAR', 'MARKET', 10, 'SELL')
                break
            
        print(tick, ": no arb opportunity")


if __name__ == '__main__':
    main()
