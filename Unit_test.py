# -*- coding: utf-8 -*-
"""
Created on Wed Jul 29 09:28:43 2020

@author: ruoyu
"""

## Unit test
import unittest
from USGS_FlowData_utils import *

class USGS_DataRetriever_Test(unittest.TestCase):
    
    
data = pd.read_csv("va_gages.csv", dtype=str)
trend_out = pd.DataFrame(columns = ['GageID','trend result','slope'])
count = 0
for i in range(len(data)):
    rcode = data["SOURCE_FEA"][i]
    try:
        site = USGS_Gage_DataRetriever(rcode,  metric=False)
        trend, slope, rts, rmk, reason = site.trendTest('Y', 10, 0.05)
        data.loc[count] = [rcode, trend, slope]
        
        count +=1
        # site.getGeoMetaData()
    except:
        print("")
        continue