# -*- coding: utf-8 -*-
"""
Created on Mon Feb 14 21:18:09 2022

@author: laurachen
"""
import executions
import config

ARBITRAGE_STATUS = 0

# check if arbitrage opportunity exists
# action: "enter" or "exit"
def check_arbitrage(s, action):
    USDbid, USDask = executions.ticker_bid_ask(s, 'USD')
    RITCbid, RITCask = executions.ticker_bid_ask(s, 'RITC')
    Bullbid, Bullask = executions.ticker_bid_ask(s, 'BULL')
    Bearbid, bearask = executions.ticker_bid_ask(s, 'BEAR')
    ETF_overvalue = USDbid * RITCbid - Bullask - bearask - config.fee * 2 - config.fee * USDask
    stock_overvalue = Bullbid + Bearbid - USDask * RITCask - config.fee * 2 - config.fee * USDbid
    
    print(ETF_overvalue)
    print(stock_overvalue)
    if action == "enter":
        if ETF_overvalue > config.ARB_ENTER_THRESHOLD:
            print("enter1")
            return -1, 1 # sell ETF, buy stocks
        elif stock_overvalue > config.ARB_ENTER_THRESHOLD:
            print("enter2")
            return 1, -1 # Buy ETF sell stocks
        else: 
            return 0, 0
    elif action == "exit":
        if ARBITRAGE_STATUS == -1:
            if ETF_overvalue < config.ARB_EXIT_THRESHOLD:
                print("exit1", stock_overvalue, config.ARB_EXIT_THRESHOLD)
                return -1, 1 # sell ETF, buy stocks
            else:
                return 0, 0
        elif ARBITRAGE_STATUS == 1:
            if stock_overvalue < config.ARB_EXIT_THRESHOLD:
                print("exit2", stock_overvalue, config.ARB_EXIT_THRESHOLD)
                return 1, -1 # Buy ETF sell stocks
            else:
                return 0, 0
        else: 
            return 0, 0
    else:
        print("Action incorrect! Either enter or exit!")
    
def trade_arbitrage(session):
    global ARBITRAGE_STATUS
    ETF_overvalue, stock_overvalue = check_arbitrage(session, "enter")

    if ETF_overvalue == -1 and stock_overvalue == 1:
        executions.make_order('RITC', 'MARKET', config.arbQuantity, 'SELL')
        executions.make_order('BULL', 'MARKET', config.arbQuantity, 'BUY')
        executions.make_order('BEAR', 'MARKET', config.arbQuantity, 'BUY')
        config.ARBITRAGE_STATUS = -1
    elif ETF_overvalue == 1 and stock_overvalue == -1:
        executions.make_order('RITC', 'MARKET', config.arbQuantity, 'BUY')
        executions.make_order('BULL', 'MARKET', config.arbQuantity, 'SELL')
        executions.make_order('BEAR', 'MARKET', config.arbQuantity, 'SELL')
        config.ARBITRAGE_STATUS = 1
    else:
        print(executions.get_tick(session), ": no arb opportunity")


    
def close_arbitrage(session):
    global ARBITRAGE_STATUS
    
    if ARBITRAGE_STATUS != 0:
        ETF_overvalue, stock_overvalue = check_arbitrage(session, "exit")
       
        # bought ETF sold stock, stock overvalued
        if ARBITRAGE_STATUS == 1:
            if stock_overvalue == -1 and ETF_overvalue == 1: 
                executions.make_order('RITC', 'MARKET', config.arbQuantity, 'SELL')
                executions.make_order('BULL', 'MARKET', config.arbQuantity, 'BUY')
                executions.make_order('BEAR', 'MARKET', config.arbQuantity, 'BUY')
                config.ARBITRAGE_STATUS = 0
            else:
                print("Doesn't meet close postion criteria!")
        # sold ETF bought stock, ETF overvalued
        elif ARBITRAGE_STATUS == -1:
            if stock_overvalue == 1 and ETF_overvalue == -1: 
                executions.make_order('RITC', 'MARKET', config.arbQuantity, 'Buy')
                executions.make_order('BULL', 'MARKET', config.arbQuantity, 'SELL')
                executions.make_order('BEAR', 'MARKET', config.arbQuantity, 'SELL')
                config.ARBITRAGE_STATUS = 0
            else:
                print("Doesn't meet close postion criteria!")
    else:
        print("Arbitrage postion: 0")
