# -*- coding: utf-8 -*-
"""
Created on Thu Jun 18 15:25:18 2020

@author: Ruoyu Zhang
"""


def USGS_DailyDischargePlot(USGS_id, st, et, savefile=True, savefig=True):
    
    ####################################################################
    ## ARGUEMNTS:                                                     ##
    ## USGS_id = '01665500' # Define USGS site                        ##  
    ## start_dt = '2015-01-01' # start date                           ##
    ## end_dt = '2018-12-31' # end date                               ##
    ##                                                                ## 
    ## DESCRIPTION:                                                   ##
    ## Get data from USGS server. Retrieve daily discharge data       ##                             ##
    ## A function used to retrieve USGS daily discharge data          ##
    ##   Three inputs are required: Gage ID, start date, and end date ##
    ##   -- USGS Gage ID: string                                      ##
    ##   -- start/end date: string, format in YYYY-MM-DD              ##
    ##   Optional savefile and savefig option                         ##  
    ##                                                                ##
    ## REVISION HISTORY:                                              ##
    ## Initial specification: Ruoyu Zhang                             ##
    ##                                                                ##
    ####################################################################
    
    # Load packages for data loading and plotting
    #import matplotlib.pyplot as plt
    #from matplotlib import dates
    import pandas as pd
    import urllib
    import json    
    
    url = 'https://waterservices.usgs.gov/nwis/dv/?format=json&sites={0}&startDT={1}&endDT={2}&siteStatus=all'.format(USGS_id, st, et)
    response = json.loads(urllib.request.urlopen(url).read())
    
    # data = []
    # date = []
    # for i in response['value']['timeSeries'][1]['values'][0]['value']:
    #     data.append(i['value'])
    #     date.append(i['dateTime'][0:10])
    
    ## I modfied these lines to use map and lambda functions to avoid for-loop
    ## Tested with tic-toc and found that it is a bit faster than for-loop (see below)
    t_list = response['value']['timeSeries'][1]['values'][0]['value']
    data = list(map(lambda x: x['value'], t_list)) # streamflow data
    date = list(map(lambda x: x['dateTime'][0:10], t_list)) # datetime data 
    
    if savefig:
        # Plotting daily discharge time-series
        ## I moved the previous lines into this block
        ## If we don't want to have a fig, we don't need these lines
        import matplotlib.pyplot as plt # is this practical to import packages inside of if loop?
        fig, ax = plt.subplots(figsize=(15,5))
        ax.plot(pd.to_datetime(date), pd.to_numeric(data), linewidth=2)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Discharge (cfs)', fontsize=12)
        ax.set_title('Discharge at USGS {}'.format(USGS_id),fontsize = 16)
        plt.savefig('USGS{}.png'.format(USGS_id), dpi=150)

    if savefile:
        st.to_csv('USGS{}.csv'.format(USGS_id))
        df = pd.DataFrame({'date':date, 'data':data})
        df.to_csv('USGS{}.csv'.format(USGS_id))

# Example
# Retrieve daily discharge data
# Define USGS site, start and end date
USGS_id = '01665500'
start_dt = '2015-01-01'
end_dt = '2018-12-31'
# Plot figure saved to the same directory as .py file
USGS_DailyDischargePlot(USGS_id = USGS_id, st = start_dt, et = end_dt, savefile=True, savefig=True)
#%%
#%% speed test
import urllib
import json
import time
url = 'https://waterservices.usgs.gov/nwis/dv/?format=json&sites=01665500&startDT=2015-01-01&endDT=2016-12-31&siteStatus=all'
response = json.loads(urllib.request.urlopen(url).read())
t_list = response['value']['timeSeries'][1]['values'][0]['value']

t = time.time()
data = []
date = []
for i in response['value']['timeSeries'][1]['values'][0]['value']:
    data.append(i['value'])
    date.append(i['dateTime'][0:10])
elapsed = time.time() - t
print(elapsed)

t = time.time()
data = list(map(lambda x: x['value'], t_list))
date = list(map(lambda x: x['dateTime'][0:10], t_list))
elapsed = time.time() - t
print(elapsed)

# def ext_val(list_data):
#     return list_data['value']
# #a = list(map(lambda x: x['value'], t_list))
# t = time.time()
# b = list(map(ext_val, t_list))
# elapsed = time.time() - t
# print(elapsed)