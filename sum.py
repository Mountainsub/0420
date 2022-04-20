
import pandas as pd
import numpy as np
import time 
import sys
import os
import ctypes
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


import datetime

from lib.ddeclient import DDEClient
from price_logger import ClientHolder 
from price_logger import LastNPerfTime
from init import keisan

class plot_time:
    def __init__(self):
        self.hdffilename = "./data/sum.hdf5"
        self.store = pd.HDFStore(self.hdffilename)
        self.key_name2 = "timecase"

    

    def hozon2(self, data_dict):
        #print("OK")
        self.store.append(self.key_name2, data_dict)
      
class up_or_down:
    def __init__(self, calc, topix):
        
        
        self.RED = '\033[31m'
        self.BLUE = '\033[34m'
        self.END = '\033[0m'
        self.switch = "N"
        #self.switch = switch 
        self.store = pd.HDFStore("./data/sum2.hdf5")
        dif = calc - float(topix)
        self.Boolean = None
        if dif > 5 or dif < -5:
            self.Boolean = "repair"
            return
        
        elif  dif >= 0.001:
            self.Boolean = "up"
        elif dif <= -0.001:
            self.Boolean = "down"
        else:
            self.Boolean = "None"
        self.calc = calc
        

    def deal(self):
        t = self.Boolean
        RED = self.RED
        BLUE = self.BLUE
        END = self.END
        switch = self.switch
        store = self.store
        if t == "up":
            string = RED +"計算した値が、実際のTOPIXより高いです。"+END
            if switch == ("down" or "N"):
                t = datetime.datetime.now()
                switch = "up"
                return "v"
                #store.append("boundary",pd.DataFrame({"t":[t], "switch":["v"]} ,index=False))
        elif t == "down":
            string = BLUE+"計算した値が、実際のTOPIXより低いです。"+END
            if switch == ("up" or "N"):
                t = datetime.datetime.now()
                switch = "down"
                return "^"
                #store.append("boundary",pd.DataFrame({"t":[t], "switch":["^"]},index=False))
        elif t == "repair":
            string = "差が大きすぎる"
            return t
        
        return None

    
    


if __name__ == "__main__":
    
    # コマンドライン上の出力文字に色を付ける
    ENABLE_PROCESSED_OUTPUT = 0x0001
    ENABLE_WRAP_AT_EOL_OUTPUT = 0x0002
    ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
    MODE = ENABLE_PROCESSED_OUTPUT + ENABLE_WRAP_AT_EOL_OUTPUT + ENABLE_VIRTUAL_TERMINAL_PROCESSING
    
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetStdHandle(-11)
    kernel32.SetConsoleMode(handle, MODE)

    
    calc = 0
    
    object_pass = "value"
    dde = DDEClient("rss", "TOPX")
    st = pd.HDFStore("./data/sum2.hdf5")
    
    try:
        topix = dde.request("現在値").decode("sjis")
    except:
        topix = 0
    else:
        topix = float(topix)
    topix_init = 424.22482609560717

    
    """
    4/13 426.1849710013568 
    4/20 424.22482609560717
    TOPIX
    （calc:8000 / 初期値）× 100
    初期値
    (calc / TOPIX ) kakeru 100
    
    """
    
    #4/8 8222.883552900003
    
    dde_etf = DDEClient("rss", "1306.T")        
    price = 0
    total_interest = 0
    holder = plot_time()
    fail_count = 0
    check_box = {0:65, 1:98, 2:80, 3:86, 4:250, 5:240, 6:360, 7:100, 8:660, 9:550, 10:2000, 11:270, 12:240,13:1680, 14:220, 15:250, 16:230, 17:270}
    while True:
        calc = 0
        x = 0
        Boolean = False
        for i in range(18):
            cycle = 0
            idx = i *126
            filename = "./data/" + str(idx).zfill(3)+ ".hdf5"
             
            try:
                with pd.HDFStore(filename) as store:
                    temp =store.get(object_pass)
            except:
                pass
            else:
                end = temp.tail(1)
                while cycle<=2:
                    try:
                        v = float(end["value"])
                    except:
                        v = 0
                        cycle += 1
                    else:
                        break
                    
                if v==0:
                    now = datetime.datetime.now()
                    print(i, "attention", now)
                    Boolean = True    
                else:
                    print(i, v)
                    x += 1
                if Boolean:
                    break
                
                # check_box {0:65, 1:98, 2:80, 3:86, 4:250, 5:240, 6:360, 7:100, 8:660, 9:550, 10:2000, 11:270, 12:240,13:1680, 14:220, 15:250, 16:230, 17:270}
                # stop
                if v < check_box[i]:
                    print("getting value is failed.")
                    fail_count += 1
                    continue
                else:
                    check_box[i] = v - 10

                
                calc += v
        
        if x != 18:
            Boolean = True
        print(calc)
        if Boolean:
            print("足し算のミス")
            continue
        
        dict = {"total": [calc]}
                
        dict = pd.DataFrame(dict)

        #保存
        #holder.hozon(dict)
        
           
        dict = {"time": [temp]}
        df = pd.DataFrame(dict)
        
        holder.hozon2(df)   
        
        
        
        now = datetime.datetime.now()
        total = calc
        calc /= topix_init 
        calc *= 100
        
        topix = dde.request("現在値").decode("sjis")
        
        
        instance = up_or_down(calc, topix)
        
        
        buy_or_sell = instance.deal()
        
        if buy_or_sell == "^":
            newprice = float(dde_etf.request("現在値"))
            if price != 0: 
                interest = newprice- price
                print("買いから売りで", interest, " 儲けた。")
            price = newprice 
        elif buy_or_sell == "v":
            newprice = float(dde_etf.request("現在値"))
            if price != 0: 
                interest = price - newprice
                print("売りから買いで", interest, " 儲けた。")
            price = newprice
        print("取得時刻:"+str(now),"計算値:" + str(calc))
        data_dict = {"time":[now], "calc":[calc], "topix":[topix], "total":[total],"total_interest":[total_interest* (10**6)],"fail_count":[fail_count]}
        st.append("consequence",pd.DataFrame(data_dict), index=False)
        try:
            total_interest += interest
        except:
            pass

        
        
        if buy_or_sell == "repair":
            if True:
                topix_init = float(topix_init)* float(calc) / float(topix)
                print("トピックス初期値："+str(topix_init))
            