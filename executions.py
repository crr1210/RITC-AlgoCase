# -*- coding: utf-8 -*-
"""
Created on Mon Feb 14 21:21:41 2022

@author: laurachen
"""
import requests
import config
import time

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
        s.headers.update(config.API_KEY)
        RITCbid, RITCask = ticker_bid_ask(s, 'RITC')
        Bullbid, Bullask = ticker_bid_ask(s, 'BULL')
        Bearbid, Bearask = ticker_bid_ask(s, 'BEAR') 
        mkt_params = {'ticker': ticker, 'type': orderType, 'quantity': quantity, 
                      'action': action}
        price = 0
        if orderType == 'LIMIT':
            if ticker == 'RITC':
                if action == 'BUY':
                    price = RITCbid + 0.01
                else:
                    price = RITCask - 0.01
            elif ticker == 'BULL':
                if action == 'BUY':
                    price = Bullbid + 0.01
                else:
                    price = Bullask - 0.01
            else:
                if action == 'BUY':
                    price = Bearbid + 0.01
                else:
                    price = Bearask - 0.01
                    
            mkt_params['price'] = price
            
        resp = s.post('http://localhost:9999/v1/orders', params=mkt_params)
       
        while not resp.ok:
            print("Try submitting again!")
            time.sleep(1)
            resp = s.post('http://localhost:9999/v1/orders', params=mkt_params)
            
            
        if resp.ok:
            mkt_order = resp.json()
            print('time:', mkt_order['tick'], 'ticker:', mkt_order['ticker'], 
                  'action:', mkt_order['action'], 'was successfully submited!')