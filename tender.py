import requests
import time


API_KEY = {'X-API-key': '2Q904VYC'}

TENDER_THRESHOLD = 0.05 # target profit per share when trade tender at the current market
TENDER_STATUS = 0 
TENDER_POSITION = 0 # current tender position
TENDER_CLEAR_ROUND = 15 # how many rounds of trade to clear the accepted tender

class ApiException(Exception):
    pass

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
        
        if orderType == 'LIMIT':
            price = 0
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
            time.sleep(0.5)
            print("Try submitting again!")
            resp = s.post('http://localhost:9999/v1/orders', params=mkt_params)
            
            
        if resp.ok:
            mkt_order = resp.json()
            print('time:', mkt_order['tick'], 'ticker:', mkt_order['ticker'], 
                  'action:', mkt_order['action'], 'was successfully submited!')
    
    
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
                spread = price - RITCbid - 0.02 * USDask
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
                spread = price - RITCask - 0.02 * USDask
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
    while True:
        with requests.Session() as s:
            s.headers.update(API_KEY)
            while TENDER_STATUS == 0:
                select_tender(s)
                
            reverse_tender(s)
        break

if __name__ == '__main__':
    main()
                    
                    
                    
                    
                    
                    
                
                
                
            
            
