import requests
import time
import arbitrage
import config
import tender
import executions



def main():   
    with requests.Session() as s:
        s.headers.update(config.API_KEY)
        tick = executions.get_tick(s)
        while tick >= 1 and tick <= 295:
            with requests.Session() as s:
                s.headers.update(config.API_KEY)
                
                # if arbitrage.ARBITRAGE_STATUS == 0:
                #     arbitrage.trade_arbitrage(s)
                # else:
                #     arbitrage.close_arbitrage(s)
                
                if tender.TENDER_STATUS == 0:
                    tender.select_tender(s)
                else:
                    tender.reverse_tender(s)
                
                tick = executions.get_tick(s)
   

if __name__ == '__main__':
    main()

