import requests
import time

API_KEY = {'X-API-key  ': '2Q904VYC'}
fee = 0.02 # transaction cost

# tender parameters
TENDER_THRESHOLD = 0.05 # target profit per share when trade tender at the current market
TENDER_STATUS = 0 
TENDER_POSITION = 0 # current tender position
TENDER_CLEAR_ROUND = 15 # how many rounds of trade to clear the accepted tender
TENDER_ID = "NA"

# arbitrage parameters
ARBITRAGE_STATUS = 0
ARB_ENTER_THRESHOLD = 0.2
ARB_EXIT_THRESHOLD = 0.1
# 0: no position, 1: buy ETF sell stock, -1: sell ETF buy stock
arbQuantity = 1
arbClearRound = 15

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
            time.sleep(2)
            resp = s.post('http://localhost:9999/v1/orders', params=mkt_params)
            
            
        if resp.ok:
            mkt_order = resp.json()
            print('time:', mkt_order['tick'], 'ticker:', mkt_order['ticker'], 
                  'action:', mkt_order['action'], 'was successfully submited!')


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
        if ARBITRAGE_STATUS == -1:
            if ETF_overvalue < ARB_EXIT_THRESHOLD:
                print("exit1", stock_overvalue, ARB_EXIT_THRESHOLD)
                return -1, 1 # sell ETF, buy stocks
            else:
                return 0, 0
        elif ARBITRAGE_STATUS == 1:
            if stock_overvalue < ARB_EXIT_THRESHOLD:
                print("exit2", stock_overvalue, ARB_EXIT_THRESHOLD)
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
        make_order('RITC', 'LIMIT', arbQuantity, 'SELL')
        make_order('BULL', 'LIMIT', arbQuantity, 'BUY')
        make_order('BEAR', 'LIMIT', arbQuantity, 'BUY')
        ARBITRAGE_STATUS = -1
    elif ETF_overvalue == 1 and stock_overvalue == -1:
        make_order('RITC', 'LIMIT', arbQuantity, 'BUY')
        make_order('BULL', 'LIMIT', arbQuantity, 'SELL')
        make_order('BEAR', 'LIMIT', arbQuantity, 'SELL')
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
                make_order('RITC', 'LIMIT', arbQuantity, 'SELL')
                make_order('BULL', 'LIMIT', arbQuantity, 'BUY')
                make_order('BEAR', 'LIMIT', arbQuantity, 'BUY')
                ARBITRAGE_STATUS = 0
            else:
                print("Doesn't meet close postion criteria!")
        # sold ETF bought stock, ETF overvalued
        elif ARBITRAGE_STATUS == -1:
            if stock_overvalue == 1 and ETF_overvalue == -1: 
                make_order('RITC', 'LIMIT', arbQuantity, 'Buy')
                make_order('BULL', 'LIMIT', arbQuantity, 'SELL')
                make_order('BEAR', 'LIMIT', arbQuantity, 'SELL')
                ARBITRAGE_STATUS = 0
            else:
                print("Doesn't meet close postion criteria!")
    else:
        print("Arbitrage postion: 0")

def accept_tender(session, t_id):
    resp = session.post('http://localhost:9999/v1/tenders/{}'.format(t_id))
    if not resp.ok:
        print("tender posting failed")
        return False
    else:
        print("tender accepted")
        return True
    

def reject_tender(session, t_id):
    resp = session.delete('http://localhost:9999/v1/tenders/{}'.format(t_id))
    if not resp.ok:
        print("tender rejection failed")
        return False
    else:
        print("tender rejected")
        return True

    
def select_tender(session):
    global TENDER_POSITION
    global TENDER_STATUS
    global TENDER_ID
    RITCbid, RITCask = ticker_bid_ask(session, 'RITC')
    USDbid, USDask = ticker_bid_ask(session, 'USD')
    resp = session.get('http://localhost:9999/v1/tenders')
    if resp.ok:
        all_tenders = resp.json()
        for tender in all_tenders:
            t_id, quantity, price, action = tender['tender_id'], tender['quantity'], tender['price'], tender['action']
            # BUY cheap tender and sell at the market bid
            if action == 'SELL':
                # profit per share if accept the tender and trade at the market
                spread = price - RITCbid - fee * USDask
                if spread >= TENDER_THRESHOLD:
                    accept_tender(session, t_id)
                    TENDER_STATUS = 1
                    TENDER_POSITION += quantity
                    TENDER_ID = t_id
                    print("SELL tender {} accepted with spread {}".format(TENDER_ID, spread))
                else:
                    reject_tender(session, t_id)
                    print("SELL tender {} rejected with spread {}".format(TENDER_ID, spread))
                    
            # SELL expensive tender and buy at the market ask      
            elif action == 'BUY':
                # profit per share if accept the tender and trade at the market
                spread = price - RITCask - fee * USDask
                if spread >= TENDER_THRESHOLD:
                    accept_tender(session, t_id)
                    TENDER_STATUS = -1
                    TENDER_POSITION -= quantity
                    TENDER_ID = t_id
                    print("BUY tender {} accepted with spread {}".format(TENDER_ID, spread))
                    return
                else:
                    reject_tender(session, t_id)
                    print("BUY tender {} rejected with spread {}".format(TENDER_ID, spread))

    
def reverse_tender(session):
    global TENDER_POSITION
    global TENDER_CLEAR_ROUND
    global TENDER_STATUS
    
    # bought cheap tender, now sell them out
    if TENDER_STATUS == 1:
        trade_per_time = TENDER_POSITION / TENDER_CLEAR_ROUND
        if TENDER_POSITION % TENDER_CLEAR_ROUND != 0:
            TENDER_CLEAR_ROUND += 1
            
        # clear all tender positionz   
        while TENDER_POSITION > 0:
            amount = min(trade_per_time, TENDER_POSITION)
            make_order("RITC", "MARKET", amount, "SELL")
            TENDER_POSITION -= amount
            TENDER_CLEAR_ROUND -= 1
            print("tender {} cleared once, {} rounds reamins".format(TENDER_ID, TENDER_CLEAR_ROUND))
            time.sleep(0.5)
        TENDER_STATUS = 0
        print("tender {} cleared!")
        
    # sold expensive tender, now buy them back    
    elif TENDER_STATUS == -1:
        trade_per_time = abs(TENDER_POSITION) / TENDER_CLEAR_ROUND
        if abs(TENDER_POSITION) % TENDER_CLEAR_ROUND != 0:
            TENDER_CLEAR_ROUND += 1
             
        while TENDER_POSITION < 0:
            amount = min(trade_per_time, abs(TENDER_POSITION))
            make_order("RITC", "MARKET", amount, "BUY")
            TENDER_POSITION += amount
            TENDER_CLEAR_ROUND -= 1
            print("tender {} cleared once, {} rounds reamins".format(TENDER_ID, TENDER_CLEAR_ROUND))
            time.sleep(0.5)
        TENDER_STATUS = 0
        print("tender {} cleared!")


def main():   
    with requests.Session() as s:
        s.headers.update(API_KEY)
        tick = get_tick(s)
        while tick >= 5 and tick <= 295:
            with requests.Session() as s:
                s.headers.update(API_KEY)
                if ARBITRAGE_STATUS == 0:
                    trade_arbitrage(s)
                else:
                    close_arbitrage(s)
                
                if TENDER_STATUS == 0:
                    select_tender(s)
                else:
                    reverse_tender(s)
                tick = get_tick(s)
   

if __name__ == '__main__':
    main()

