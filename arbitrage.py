# -*- coding: utf-8 -*-
"""
Created on Mon Feb 14 21:18:09 2022

@author: laurachen
"""
import executions
import config

# 0: no position, 1: buy ETF sell stock, -1: sell ETF buy stock
ARBITRAGE_STATUS = 0

# check if arbitrage opportunity exists
# action: "enter" or "exit"
def check_arbitrage(s, action):
    USDbid, USDask = executions.ticker_bid_ask(s, 'USD')
    RITCbid, RITCask = executions.ticker_bid_ask(s, 'RITC')
    Bullbid, Bullask = executions.ticker_bid_ask(s, 'BULL')
    Bearbid, Bearask = executions.ticker_bid_ask(s, 'BEAR')

    # print("USD bid:", USDbid, "RITC bid:", RITCbid, "BullAsk:", Bullask, "BearAsk:", Bearask)
    # print(ETF_overvalue)
    # print("USD bid:", USDbid, "RITC ask:", RITCbid, "BullAsk:", Bullask, "BearAsk:", Bearask)
    # print(stock_overvalue)
    if action == "enter":
        ETF_overvalue = USDbid * RITCbid - Bullask - Bearask - config.fee * 2 - config.fee * USDask
        stock_overvalue = Bullbid + Bearbid - USDask * RITCask - config.fee * 2 - config.fee * USDask
        print(ETF_overvalue)
        print(stock_overvalue)
        if ETF_overvalue > config.ARB_ENTER_THRESHOLD:
            print("enter1")
            return -1 # sell ETF, buy stocks
        elif stock_overvalue > config.ARB_ENTER_THRESHOLD:
            print("enter2")
            return 1 # Buy ETF sell stocks
        else: 
            return 0
    elif action == "exit":
        ETF_overvalue = USDask * RITCask - Bullbid - Bearbid - config.fee * 2 - config.fee * USDask
        stock_overvalue = Bullask + Bearask - USDask * RITCbid - config.fee * 2 - config.fee * USDask
        print(ETF_overvalue)
        print(stock_overvalue)
        if ARBITRAGE_STATUS == -1:
            if ETF_overvalue < config.ARB_EXIT_THRESHOLD:
                print("exit1", ETF_overvalue, config.ARB_EXIT_THRESHOLD)
                return -1 # buy ETF, sell stocks to close position
            else:
                return 0
        elif ARBITRAGE_STATUS == 1:
            if stock_overvalue < config.ARB_EXIT_THRESHOLD:
                print("exit2", stock_overvalue, config.ARB_EXIT_THRESHOLD)
                return 1 # Sell ETF Buy stocks to close position
            else:
                return 0
        else: 
            return 0
    else:
        print("Action incorrect! Either enter or exit!")
    
def trade_arbitrage(session):
    global ARBITRAGE_STATUS
    overvalue = check_arbitrage(session, "enter")

    if overvalue == -1:
        executions.make_order('RITC', 'MARKET', config.arbQuantity, 'SELL')
        executions.make_order('BULL', 'MARKET', config.arbQuantity, 'BUY')
        executions.make_order('BEAR', 'MARKET', config.arbQuantity, 'BUY')
        ARBITRAGE_STATUS = -1
    elif overvalue == 1:
        executions.make_order('RITC', 'MARKET', config.arbQuantity, 'BUY')
        executions.make_order('BULL', 'MARKET', config.arbQuantity, 'SELL')
        executions.make_order('BEAR', 'MARKET', config.arbQuantity, 'SELL')
        ARBITRAGE_STATUS = 1
    else:
        print(executions.get_tick(session), ": no arb opportunity")


    
def close_arbitrage(session):
    global ARBITRAGE_STATUS
    
    if ARBITRAGE_STATUS != 0:
        overvalue = check_arbitrage(session, "exit")
       
        # bought ETF sold stock, stock overvalued
        if ARBITRAGE_STATUS == 1:
            if overvalue == 1: 
                executions.make_order('RITC', 'MARKET', config.arbQuantity, 'SELL')
                executions.make_order('BULL', 'MARKET', config.arbQuantity, 'BUY')
                executions.make_order('BEAR', 'MARKET', config.arbQuantity, 'BUY')
                ARBITRAGE_STATUS = 0
            else:
                print("Doesn't meet close postion criteria!")
        # sold ETF bought stock, ETF overvalued
        elif ARBITRAGE_STATUS == -1:
            if overvalue == -1: 
                executions.make_order('RITC', 'MARKET', config.arbQuantity, 'BUY')
                executions.make_order('BULL', 'MARKET', config.arbQuantity, 'SELL')
                executions.make_order('BEAR', 'MARKET', config.arbQuantity, 'SELL')
                ARBITRAGE_STATUS = 0
            else:
                print("Doesn't meet close postion criteria!")
    else:
        print("Arbitrage postion: 0")
