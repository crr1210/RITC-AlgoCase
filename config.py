# -*- coding: utf-8 -*-
"""
Created on Mon Feb 14 21:19:55 2022

@author: laurachen
"""

API_KEY = {'X-API-key  ': '2VX1D73B'}
fee = 0.02 # transaction cost

# tender parameters
TENDER_THRESHOLD = 0.05 # target profit per share when trade tender at the current market
TENDER_ID = "NA"

# arbitrage parameters
ARB_ENTER_THRESHOLD = 0.2
ARB_EXIT_THRESHOLD = 0.1
# 0: no position, 1: buy ETF sell stock, -1: sell ETF buy stock
arbQuantity = 500
arbClearRound = 15
