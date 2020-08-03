# -*- coding: utf-8 -*-
"""
Created on Sat Aug  1 10:59:48 2020

@author: ruoyu
"""

from USGS_FlowData_utils import *
import pandas as pd

data = pd.read_csv("gages_list.csv", dtype=str)
data= ['01673550','02032515','02041000','01636316','01634500','01638480','01490000']

trend_out = pd.DataFrame(columns = ['GageID','Start Data','End Data', 'Min','Median','Max','Mean','slope (M)','p-value (M)','slope (Y)', 'p-value (Y)','County','CountyID','State','Coordinate'])
count = 0
for i in range(len(data)):
    rcode = data[i]
    print("Working on gage", rcode)
    try:
        site = USGS_Gage_DataRetriever(rcode,  metric=False)
        stat = site.getStatistics()
        trend_result_m, slope_result_m, R_TS_m, R_MK_m, reason = site.trendTest('M', 120, 0.05)
        trend_result_y, slope_result_y, R_TS_y, R_MK_y, reason = site.trendTest('Y', 10, 0.05)
        geoMeta = site.getGeoMetaData()
        
        if R_TS_m is np.nan:
            trend_out.loc[count] = [site.id, site.startdate, site.enddate, stat['Min'], stat['Median'], stat['Max'], stat['Mean'], np.nan, np.nan,np.nan, np.nan,
                                geoMeta['County'], geoMeta['CountyFIPS'], geoMeta['State'],geoMeta['Coordiantes']]
        else:
            trend_out.loc[count] = [site.id, site.startdate, site.enddate, stat['Min'], stat['Median'], stat['Max'], stat['Mean'], R_TS_m[0], R_MK_m[-1], R_TS_y[0], R_MK_y[-1],
                                geoMeta['County'], geoMeta['CountyFIPS'], geoMeta['State'],geoMeta['Coordiantes']]
        
        count +=1
        # site.getGeoMetaData()
        print('{} completed'.format(round((i+1)/len(data)*100,2)))
    except:
        
        print("Fail to find data.")
        continue
    
#trend_out.to_csv('C:/Users/ruoyu/Desktop/PythonDS_hw/new_CB_trend.csv', index=False)