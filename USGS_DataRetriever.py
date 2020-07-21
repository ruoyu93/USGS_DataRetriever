# -*- coding: utf-8 -*-
"""
Created on Thu Jun 18 15:25:18 2020

@author: Ruoyu Zhang
"""


def USGS_DailyDischargePlot(USGS_id, st, et, savefile=False, savefig=True):
    
    ####################################################################
    ## A function used to retrieve USGS daily discharge data          ##
    ##   Three inputs are required: Gage ID, start date, and end date ##
    ##   -- USGS Gage ID: string                                      ##
    ##   -- start/end date: string, format in YYYY-MM-DD              ##
    ##   Optional savefile and savefig option                         ##
    ####################################################################
    
    
    # Load packages for data loading and plotting
    import matplotlib.pyplot as plt
    from matplotlib import dates
    import pandas as pd
    import urllib
    import json
    
    
    # Retrieve daily discharge data
    #      Define USGS site, start and end date
    # USGS_id = '01665500'
    # start_dt = '2015-01-01'
    # end_dt = '2018-12-31'
    # get data from USGS server
    url = 'https://waterservices.usgs.gov/nwis/dv/?format=json&sites={}&startDT={}&endDT={}&siteStatus=all'.format(USGS_id, st, et)
    response = json.loads(urllib.request.urlopen(url).read())
    
    
    data = []
    date = []
    for i in response['value']['timeSeries'][1]['values'][0]['value']:
        data.append(i['value'])
        date.append(i['dateTime'][0:10])
    
    
    # Plotting daily discharge time-series
    fig, ax = plt.subplots(figsize=(15,5))
    ax.plot(pd.to_datetime(date), pd.to_numeric(data), linewidth=2)
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Discharge (cfs)', fontsize=12)
    ax.set_title('Discharge at USGS {}'.format(USGS_id),fontsize = 16)
    
    if savefig:
        plt.savefig('USGS{}.png'.format(USGS_id), dpi=150)
    if savefile:
        st.to_csv('USGS{}.csv'.format(USGS_id))


# Example
# Plot figure saved to the same directory as .py file
USGS_DailyDischargePlot(USGS_id = '01665500', st='2015-01-01', et='2016-12-31')
