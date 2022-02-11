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
ARB_EXIT_THRESHOLD = 0.1
# 0: no position, 1: buy ETF sell stock, -1: sell ETF buy stock
ARBITRAGE_STATUS = 0
arbQuantity = 5000

class ApiException(Exception):
    pass


# get currect time elasped
def get_tick(session):
    resp = session.get('http://localhost:9999/v1/case')
    if resp.ok:
        case = resp.json()
        return case['tick']
    raise ApiException('Authorization error. Please check API key.')


# get the current bid and ask price of ticker
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
            print('time:', mkt_order['tick'], 'ticker:', mkt_order['ticker'], 'action:', mkt_order['action'], 'was successfully submited!')
        else:
            payload = {'ticker': ticker}
            resp = s.get('http://localhost:9999/v1/securities/book', params=payload)
            book = resp.json()
            print("bids quantity:", book['bids'][0]['quantity'])
            print("asks quantity:", book['asks'][0]['quantity'])
            print("The order was not successfully submitted!")
          
            
# check if arbitrage opportunity exists
# action: "enter" or "exit"
def check_arbitrage(s, action):
    USDbid, USDask = ticker_bid_ask(s, 'USD')
    RITCbid, RITCask = ticker_bid_ask(s, 'RITC')
    Bullbid, Bullask = ticker_bid_ask(s, 'BULL')
    Bearbid, bearask = ticker_bid_ask(s, 'BEAR')
    ETF_overvalue = USDbid * RITCbid - Bullask - bearask - fee * 2 - fee * USDask
    stock_overvalue = Bullbid + Bearbid - USDask * RITCask - fee * 2 - fee * USDbid
    
    print(ETF_overvalue)
    print(stock_overvalue)
    if action == "enter":
        if ETF_overvalue > ARB_ENTER_THRESHOLD:
            print("enter1")
            return -1, 1 # sell ETF, buy stocks
        elif stock_overvalue > ARB_ENTER_THRESHOLD:
            print("enter2")
            return 1, -1 # Buy ETF sell stocks
        else: 
            return 0, 0
    elif action == "exit":
        if ETF_overvalue < ARB_EXIT_THRESHOLD:
            print("exit1")
            return -1, 1 # sell ETF, buy stocks
        elif stock_overvalue < ARB_EXIT_THRESHOLD:
            print("exit2")
            return 1, -1 # Buy ETF sell stocks
        else: 
            return 0, 0
    else:
        print("Action incorrect! Either enter or exit!")
    
def trade_arbitrage(session):
    global ARBITRAGE_STATUS
    ETF_overvalue, stock_overvalue = check_arbitrage(session, "enter")

    if ETF_overvalue == -1 and stock_overvalue == 1:
        make_order('RITC', 'MARKET', arbQuantity, 'SELL')
        make_order('BULL', 'MARKET', arbQuantity, 'BUY')
        make_order('BEAR', 'MARKET', arbQuantity, 'BUY')
        ARBITRAGE_STATUS = -1
    elif ETF_overvalue == 1 and stock_overvalue == -1:
        make_order('RITC', 'MARKET', arbQuantity, 'BUY')
        make_order('BULL', 'MARKET', arbQuantity, 'SELL')
        make_order('BEAR', 'MARKET', arbQuantity, 'SELL')
        ARBITRAGE_STATUS = 1
    else:
        print(get_tick(session), ": no arb opportunity")


    
def close_arbitrage(session):
    global ARBITRAGE_STATUS
    
    if ARBITRAGE_STATUS != 0:
        ETF_overvalue, stock_overvalue = check_arbitrage(session, "exit")
       
        # bought ETF sold stock, stock overvalued
        if ARBITRAGE_STATUS == 1:
            if stock_overvalue == -1 and ETF_overvalue == 1: 
                make_order('RITC', 'MARKET', arbQuantity, 'SELL')
                make_order('BULL', 'MARKET', arbQuantity, 'BUY')
                make_order('BEAR', 'MARKET', arbQuantity, 'BUY')
                ARBITRAGE_STATUS = 0
            else:
                print("Doesn't meet close postion criteria!")
        # sold ETF bought stock, ETF overvalued
        elif ARBITRAGE_STATUS == -1:
            if stock_overvalue == 1 and ETF_overvalue == -1: 
                make_order('RITC', 'MARKET', arbQuantity, 'Buy')
                make_order('BULL', 'MARKET', arbQuantity, 'SELL')
                make_order('BEAR', 'MARKET', arbQuantity, 'SELL')
                ARBITRAGE_STATUS = 0
            else:
                print("Doesn't meet close postion criteria!")
    else:
        print("Arbitrage postion: 0")
        
        
def main():   
    while True:
        with requests.Session() as s:
            s.headers.update(API_KEY)
            tick = get_tick(s)
            
            if ARBITRAGE_STATUS == 0:
                trade_arbitrage(s)
            else:
                close_arbitrage(s)
                if ARBITRAGE_STATUS == 0:
                    break

if __name__ == '__main__':
    main()
