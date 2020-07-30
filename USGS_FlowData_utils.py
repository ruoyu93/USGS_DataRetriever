import matplotlib.pyplot as plt
import pandas as pd
import urllib.request
import json
import numpy as np
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta, date
from pandas.plotting import register_matplotlib_converters
from scipy import stats
import mkt # Mann Kendall test lib is required (mkt.py)
register_matplotlib_converters()

# Super Class: get MetaData for a gage
class USGS_Gage:
    
    def __init__(self, usgsid):
        self.id = str(usgsid)
        self.vars_info = None
        self.geo_info = {}
        
    def getVarsMetaData(self):
        
        # 1) get variable list and each time span
        url = f'https://waterdata.usgs.gov/nwis/dv?referred_module=sw&site_no={self.id}'
        response = requests.get(url)
        html = response.content
        # use Beuatifulsoup to print tidier html
        soup = BeautifulSoup(html,features="lxml")
        #print (soup)
        rows = soup.find_all('tr')
        table = [[td.getText() for td in rows[i].findAll('td')]
                    for i in range(len(rows))]
        # extract metadata for available variables and their time of period of records
        metaData = {'Variables':[]}
        for iterRow in range(2,len(table)): # table conten start from the third row
            variableName = ' '.join(table[iterRow][1].split()[1:])
            variableID = table[iterRow][1].split()[0]
            startDate = table[iterRow][2][:10]
            endDate = table[iterRow][3]
            metaData['Variables'].append({"variableID":variableID, 'variableName':variableName, 
                             "startDate":startDate, 'endDate':endDate})
        if metaData == {'Variables': []}: 
            raise Exception("No Data Found at This Gage!\n")
        else:
            print(metaData)
            self.vars_info = metaData
            
            print('-------------------------------------------------------------------------------------------------------')
            print('USGS Gage', self.id, 'has following variables:')
            out_frame = pd.DataFrame(columns = ['Variable Name', 'Variable ID', 'Start Date', 'End Date'])
            for i in range(len(metaData['Variables'])):
                print("{:>10} from {} to {}".format(metaData['Variables'][i]['variableName'], metaData['Variables'][i]['startDate'], metaData['Variables'][i]['endDate']))
                out_frame.loc[i] = [metaData['Variables'][i]['variableName'], metaData['Variables'][i]['variableID'], 
                                    metaData['Variables'][i]['startDate'], metaData['Variables'][i]['endDate']]
            print('-------------------------------------------------------------------------------------------------------')
            print()
            return out_frame
    
    def getGeoMetaData(self):
        # grab Geo meta data from only a 3-day period
        date = datetime.strptime(self.startdate, "%Y-%m-%d")
        modified_date = date + timedelta(days=3)
        date_3daysAfter = datetime.strftime(modified_date, "%Y-%m-%d") # 3 days later
        # Get its geoLocation and county, state
        url = 'https://waterservices.usgs.gov/nwis/dv/?format=json&sites={}&startDT={}&endDT={}&parameterCd=00060&siteStatus=all'.format(
                    self.id, self.startdate, date_3daysAfter)
        response = json.loads(urllib.request.urlopen(url).read())
        geoLocation = response['value']['timeSeries'][0]["sourceInfo"]["geoLocation"]["geogLocation"]
        siteCode = str(response['value']['timeSeries'][0]["sourceInfo"]["siteProperty"][3]['value'])
        county_list = pd.read_csv('https://www2.census.gov/geo/docs/reference/codes/files/national_county.txt', dtype=str, header=None)
        county_list['FIPS'] = county_list[1] + county_list[2]
        county, state = county_list[county_list['FIPS']==siteCode].values[0][3].split()[0], county_list[county_list['FIPS']==siteCode].values[0][0]
        
        self.geo_info['County'] = county
        self.geo_info['State'] = state
        self.geo_info['Coordinate'] = (geoLocation['latitude'], geoLocation['longitude']) 
        
        print('-------------------------------------------------------------------------------------------------------')
        print('USGS Gage', self.id, 'locates at:')
        print('{} county, {}. Site coordinates: {}\n'.format(county, state, (geoLocation['latitude'], geoLocation['longitude'])))
        print('-------------------------------------------------------------------------------------------------------')
        return {'Gage': self.id, 'County': county,'CountyFIPS': siteCode,'State': state,'Coordiantes':(geoLocation['latitude'], geoLocation['longitude'])}
        
class USGS_Gage_DataRetriever(USGS_Gage):
    
    def __init__(self, usgsid, st=None, ed=None, metric=True, autoDates=True):
        USGS_Gage.__init__(self, str(usgsid))
        self.id = str(usgsid)
        self.ismetric = metric      
        self.data = None
        self.autodate = autoDates
        if (self.autodate is True) & (st is None) & (ed is None):
            print('Retrieving MetaData for Discharge time period')
            try:
                vars_info = self.getVarsMetaData()
                self.startdate = vars_info['Start Date'][vars_info['Variable ID'] == '00060'].values[0]
                self.enddate = vars_info['End Date'][vars_info['Variable ID'] == '00060'].values[0]
                print('.........................................\nNew dates from',self.startdate,'to',self.enddate)
            except:
                raise Exception("No Data Found at This Gage!")
        elif (autoDates is True) & (st is not None) & (ed is not None):   # if user spe
            print('.............................................\nOverwrite the start and end dates based on variable time period.\n')
            try:
                vars_info = self.getVarsMetaData()
                self.startdate = vars_info['Start Date'][vars_info['Variable ID'] == '00060'].values[0]
                self.enddate = vars_info['End Date'][vars_info['Variable ID'] == '00060'].values[0]
                print('.........................................\nNew dates from',self.startdate,'to',self.enddate)
            except:
                raise Exception("No Data Found at This Gage!")
        elif (autoDates is False) & (st is not None) & (ed is not None):
            self.startdate = vars_info['Start Date'][vars_info['Variable ID'] == '00060'].values[0]
            self.enddate = vars_info['End Date'][vars_info['Variable ID'] == '00060'].values[0]
        else:
            raise Exception("No dates defined! You need to define start date (end date) or set autoDates to True!")
            
    # A method to get daily discharge time-series 
    def getDailyDischarge(self):
        # Get the JSON file from USGS server
        try:
            url = 'https://waterservices.usgs.gov/nwis/dv/?format=json&sites={}&startDT={}&endDT={}&parameterCd=00060&siteStatus=all'.format(
                    self.id, self.startdate, self.enddate)
            response = json.loads(urllib.request.urlopen(url).read())
            
            # Retrieve the data from JSON file
            pull = response['value']['timeSeries'][0]['values'][0]['value']
            
            # Get discharge values
            if self.ismetric:
                data = np.array([float(i['value']) for i in pull]) * 0.028316846988436  # Convert from cfs to cms
            else:
                data = [float(i['value']) for i in pull]                      # keep unit to be cfs
            # Get dates
            date = pd.to_datetime([i['dateTime'][0:10] for i in pull]) # HK: save the date to datetime format
            
            # Organize data in a data frame
            st = pd.DataFrame({'Date': date, 'Flow ({})'.format(self.getUnit()): data})
            self.data = st
            return st
        except:
            print('No Discharge Data at this gage!')
            print('Choose another gage...')
            
    def getStatistics(self):
        
        # Call the method getDailyDischarge(), and define the start and end dates
        if self.data is None:
            self.data = self.getDailyDischarge()
        
        # Print the statistics of daily discharge
        print("Summary of flow from",self.startdate,"to",self.enddate)
        print("Min:", self.data.iloc[:,1].min())
        print("Median:", self.data.iloc[:,1].median())
        print("Max:", self.data.iloc[:,1].max())
        print("Mean:", self.data.iloc[:,1].mean())
        print("Standard Deviation:", self.data.iloc[:,1].std(),'\n')
        
        # Save stats into a dictionary
        stat_frame = {"Min": self.data.iloc[:,1].min(), "Median": self.data.iloc[:,1].median(), 
                      "Max": self.data.iloc[:,1].max(), "Mean": self.data.iloc[:,1].mean(),
                                     "Standard Deviation": self.data.iloc[:,1].std()}
        return stat_frame
    # A method to return the unit, either cfs or cms (cubit foot/meter per second)
    def getUnit(self):
        if self.ismetric:
            unit = 'cms'
        else:
            unit = 'cfs'
        return unit
    
    # A method to plot user defined period of daily discharge
    # Type the folder that you want to save the output file
    def plotTimeSeries(self, savefig=None):
        
        if self.data is None:
            self.data = self.getDailyDischarge()
        
        # Set the frame of plot
        fig, ax = plt.subplots(figsize=(15,5))
        ax.plot(pd.to_datetime(self.data['Date']), pd.to_numeric(self.data['Flow ({})'.format(self.getUnit())]), linewidth=2)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Discharge {}'.format(self.getUnit()), fontsize=12)
        ax.set_title('Discharge at USGS {}'.format(self.id),fontsize = 16)
        
        # If savefig is True, save the plot to local drive
        if savefig is not None:
            fig.savefig(savefig+'/USGS_{}.png'.format(self.id), dpi=200)
    
    # A method to find the top X discharges and corresponding dates
    def findLargestEvents(self, top_x):
        if self.data is None:
            self.data = self.getDailyDischarge()
        # Sort the data in desending order and choose the top x events
        dat = self.data.sort_values(by = ['Flow ({})'.format(self.getUnit())], ascending=False).reset_index(drop=True)
        return dat.iloc[:top_x,]
    

    def trendTest(self, time_scale, target_alpha): #HKM added / Jul.30.2020

        if self.data is None:
            self.data = self.getDailyDischarge()

        t_Q = self.data.rename(columns={'Flow ({})'.format(self.getUnit()):'Flow'})

        # If we have a date gap, we should modify this code lines
        # Here, I assume that USGS provides continuous data
        valid_flag = True
        if time_scale == 'M': # Monthly trend
            t_Q_aggr = t_Q.groupby(t_Q.Date.dt.strftime('%Y-%m')).Flow.agg(['mean'])
            nod = len(t_Q_aggr)

            if nod < 120: # We should have more than 10-year lenth of data
                valid_flag = False

        elif time_scale == 'Y': # Yearly trend
            t_Q_aggr = t_Q.groupby(t_Q.Date.dt.strftime('%Y')).Flow.agg(['mean'])
            nod = len(t_Q_aggr)
            if nod < 10: # We should have more than 10-year lenth of data
                valid_flag = False

        else:
            print('Please select M (monthly trend) or Y (yearly trend)')
            valid_flag = False

        if valid_flag:
            x = np.arange((len(t_Q_aggr)))
            y = t_Q_aggr.to_numpy().ravel()

            # Theilslopes
            R_TS = stats.theilslopes(y, x, alpha = 1 - target_alpha)
            """            
            Ruetunrs:
            1) medslope : float
                Theil slope.
            2) medintercept : float
                Intercept of the Theil line, as median(y) - medslope*median(x).
            3) lo_slope : float
                Lower bound of the confidence interval on medslope.
            4) up_slope : float
                Upper bound of the confidence interval on medslope.
            https://docs.scipy.org/doc/scipy-0.15.1/reference/generated/scipy.stats.mstats.theilslopes.html
            """

            # Mann Kendall Trend Test
            R_MK = mkt.test(x, y, 1, target_alpha,"upordown")
            """
            Returns
            1) MK : string
                result of the statistical test indicating whether or not to accept hte
                alternative hypothesis 'Ha'
            2) m : scalar, float
                slope of the linear fit to the data
            3) c : scalar, float
                intercept of the linear fit to the data
            4) p : scalar, float, greater than zero
                p-value of the obtained Z-score statistic for the Mann-Kendall test
            # https://up-rs-esp.github.io/mkt/_modules/mkt.html
            """
            if (R_MK[3] < target_alpha) & (R_MK[1] > 0):
                trend_result = 1 # increasing trend
                slope_result = R_TS[0]
            elif (R_MK[3] < target_alpha) & (R_MK[1] < 0):
                trend_result = -1 # decreasing trend
                slope_result = R_TS[0]
            else:
                trend_result = 0 # no trend
                slope_result = 0
        else: # Any cases we cannot conduct the trend analysis
            trend_result = False
            slope_result = False
            R_TS = False
            R_MK = False

        return trend_result, slope_result, R_TS, R_MK

## Test example
#import time
#stime = time.time()
#data = pd.read_csv("va_gages.csv", dtype=str)
#for i in range(0,30):
#    rcode = data["SOURCE_FEA"][i]
#    try:
#        site = USGS_Gage_DataRetriever(rcode,  metric=False)
#        site.getDailyDischarge()
#        # site.getGeoMetaData()
#    except:
#        print("")
#        continue
#print(time.time()-stime)

## Trend Test example
site=USGS_Gage_DataRetriever(usgsid='02034000')
trend_result, slope_result, R_TS, R_MK = site.trendTest('M',0.05)
print(R_MK[0], '\nTrend? (0: no trend, -1: downard trend, 1: upward trend): {0}\nSlope? {1}'.format(trend_result, trend_result))
