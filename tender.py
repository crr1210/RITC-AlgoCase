import requests
import executions
import time
import config
import arbitrage

TENDER_STATUS = 0 
TENDER_POSITION = 0 # current tender position
TENDER_CLEAR_SHARES = 500 # clear how many shares per trade

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
    global TENDER_STATUS
    global TENDER_POSITION
    
    resp = session.get('http://localhost:9999/v1/tenders')
    print(resp)
    if resp.ok:
        RITCbid, RITCask = executions.ticker_bid_ask(session, 'RITC')
        USDbid, USDask = executions.ticker_bid_ask(session, 'USD')
        
        all_tenders = resp.json()
        for tender in all_tenders:
            print(tender)
            t_id, quantity, price, action = tender['tender_id'], tender['quantity'], tender['price'], tender['action']
            # BUY cheap tender and sell at the market bid
            if action == 'BUY':
                # profit per share if accept the tender and trade at the market
                spread = price - RITCbid - config.fee * USDask
                if spread >= config.TENDER_THRESHOLD:
                    accept_tender(session, t_id)
                    TENDER_STATUS = 1
                    TENDER_POSITION += quantity
                    TENDER_ID = t_id
                    print("SELL tender {} accepted with spread {}".format(t_id, spread))
                # else:
                #     reject_tender(session, t_id)
                #     print("SELL tender {} rejected with spread {}".format(t_id, spread))
                    
            # SELL expensive tender and buy at the market ask      
            elif action == 'SELL':
                # profit per share if accept the tender and trade at the market
                spread = price - RITCask - config.fee * USDask
                if spread >= config.TENDER_THRESHOLD:
                    accept_tender(session, t_id)
                    TENDER_STATUS = -1
                    TENDER_POSITION -= quantity
                    t_id = t_id
                    print("BUY tender {} accepted with spread {}".format(t_id, spread))
                    return
                # else:
                #     reject_tender(session, t_id)
                #     print("BUY tender {} rejected with spread {}".format(t_id, spread))

    
def reverse_tender(session):
    global TENDER_STATUS
    global TENDER_POSITION
    global TENDER_CLEAR_SHARES
        
    # bought cheap tender, now sell them out
    if TENDER_STATUS == 1:
        # clear all tender positionz   
        while TENDER_POSITION > 0:
            amount = min(TENDER_CLEAR_SHARES, TENDER_POSITION)
            executions.make_order("RITC", "MARKET", amount, "SELL")
            TENDER_POSITION -= amount
            print("tender {} cleared once, {} shares remains".format("RITC", TENDER_POSITION))
            time.sleep(0.25)
        TENDER_STATUS = 0
        print("tender {} cleared!")
    # sold expensive tender, now buy them back    
    elif TENDER_STATUS == -1:
        while TENDER_POSITION < 0:
            amount = min(TENDER_CLEAR_SHARES, abs(TENDER_POSITION))
            executions.make_order("RITC", "MARKET", amount, "BUY")
            TENDER_POSITION += amount
            print("tender {} cleared once, {} shares remains".format("RITC", TENDER_POSITION))
            time.sleep(0.25)
        TENDER_STATUS = 0
        print("tender {} cleared!")
        
        if arbitrage.ARBITRAGE_STATUS != 0:
            arbitrage.close_arbitrage(session)