import matplotlib.pyplot as plt
import pandas as pd
import urllib.request
import json
import numpy as np
from bs4 import BeautifulSoup
import requests
from pandas.plotting import register_matplotlib_converters
from scipy import stats
import mkt
register_matplotlib_converters()
import statsmodels.api as sm

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
            self.vars_info = metaData
            
            print('----------------------------------------------------------')
            print('USGS Gage', self.id, 'has following variables:')
            out_frame = pd.DataFrame(columns = ['Variable Name', 'Variable ID', 'Start Date', 'End Date'])
            for i in range(len(metaData['Variables'])):
                print("{}. {:>25} from {} to {}".format(i, metaData['Variables'][i]['variableName'], metaData['Variables'][i]['startDate'], metaData['Variables'][i]['endDate']))
                out_frame.loc[i] = [metaData['Variables'][i]['variableName'], metaData['Variables'][i]['variableID'], 
                                    metaData['Variables'][i]['startDate'], metaData['Variables'][i]['endDate']]
            print('----------------------------------------------------------')
            print()
            return out_frame
    
    def getGeoMetaData(self):
        # grab Geo meta data from only a 3-day period
        if self.vars_info == None:
            vars_info = self.getVarsMetaData()
            s_date = vars_info['Start Date'].values[0]
            var_id = vars_info['Variable ID'].values[0]
        else:
            s_date = self.vars_info['Variables'][0]['startDate']
            var_id = self.vars_info['Variables'][0]['variableID']

        date = pd.to_datetime(s_date, format="%Y-%m-%d")
        modified_date = date + pd.DateOffset(days=3)
        date_3daysAfter = modified_date.strftime(format = "%Y-%m-%d") # 3 days later
        
        # Get its geoLocation and county, state
        url = 'https://waterservices.usgs.gov/nwis/dv/?format=json&sites={}&startDT={}&endDT={}&parameterCd={}&siteStatus=all'.format(
                    self.id, self.startdate, date_3daysAfter, var_id)
        response = json.loads(urllib.request.urlopen(url).read())
        geoLocation = response['value']['timeSeries'][0]["sourceInfo"]["geoLocation"]["geogLocation"]
        siteCode = str(response['value']['timeSeries'][0]["sourceInfo"]["siteProperty"][3]['value'])
        self.noDataValue = response['value']['timeSeries'][0]['variable']['noDataValue']
        
        county_list = pd.read_csv('https://www2.census.gov/geo/docs/reference/codes/files/national_county.txt', dtype=str, header=None)
        county_list['FIPS'] = county_list[1] + county_list[2]
        county, state = county_list[county_list['FIPS']==siteCode].values[0][3].split()[0], county_list[county_list['FIPS']==siteCode].values[0][0]
        
        self.geo_info['County'] = county
        self.geo_info['State'] = state
        self.geo_info['Coordinate'] = (geoLocation['latitude'], geoLocation['longitude']) 
        
        print('---------------------------------------------------------------')
        print('USGS Gage', self.id, 'locates at:')
        print('    {} county, {}. Site coordinates: {}\n'.format(county, state, (geoLocation['latitude'], geoLocation['longitude'])))
        print('---------------------------------------------------------------')
        return {'Gage': self.id, 'County': county,'CountyFIPS': siteCode,'State': state,'Coordiantes':(geoLocation['latitude'], geoLocation['longitude'])}

# A subclass of USGS_Gage that can download Discharge data
class USGS_Gage_DataRetriever(USGS_Gage):
    
    def __init__(self, usgsid, st=None, ed=None, metric=True, autoDates=True):
        USGS_Gage.__init__(self, str(usgsid))
        self.id = str(usgsid)
        self.ismetric = metric      
        self.data = None
        self.autodate = autoDates
        self.stat = None
        
        if (self.autodate is True) & (st is None) & (ed is None):
            print('---------------------------------------------------------------')
            print('Retrieving MetaData for Discharge time period')
            try:
                vars_info = self.getVarsMetaData()
                self.startdate = vars_info['Start Date'][vars_info['Variable ID'] == '00060'].values[0]
                self.enddate = vars_info['End Date'][vars_info['Variable ID'] == '00060'].values[0]
                print('    Setting new dates from',self.startdate,'to',self.enddate)
            except:
                raise Exception("No Data Found at This Gage!")
        elif (autoDates is True) & (st is not None) & (ed is not None):   # if user spe
            print('....Overwrite the start and end dates based on variable time period.\n')
            try:
                vars_info = self.getVarsMetaData()
                self.startdate = vars_info['Start Date'][vars_info['Variable ID'] == '00060'].values[0]
                self.enddate = vars_info['End Date'][vars_info['Variable ID'] == '00060'].values[0]
                print('    Setting new dates from',self.startdate,'to',self.enddate)
            except:
                raise Exception("No Data Found at This Gage!")
        elif (autoDates is False) & (st is not None) & (ed is not None):
            self.startdate = vars_info['Start Date'][vars_info['Variable ID'] == '00060'].values[0]
            self.enddate = vars_info['End Date'][vars_info['Variable ID'] == '00060'].values[0]
        else:
            raise Exception(''' ERROR:\nNo dates defined! You need to define start date (end date) or set autoDates to True!''')
            
    # A method to get daily discharge time-series 
    def getDailyDischarge(self, drop_nodata = True):
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
            date = [i['dateTime'][0:10] for i in pull]
            
            # Organize data in a data frame
            st = pd.DataFrame({'Date': date, 'Flow ({})'.format(self.getUnit()): data})
            if drop_nodata:
                print("    Drop {} no data attributes".format(len(st[st['Flow ({})'.format(self.getUnit())]<0])))
                self.data = st[st['Flow ({})'.format(self.getUnit())] >=0]
            else:
                self.data = st
            return self.data
        except:
            raise Exception('ERROR:\nNO Discharge Data at this gage! \nChoose another gage')
            
            
    
    def getStatistics(self):
        
        # Call the method getDailyDischarge(), and define the start and end dates
        if self.data is None:
            self.getDailyDischarge()
        
        # Print the statistics of daily discharge
        print("Summary of flow from",self.startdate,"to",self.enddate)
        print("    Min:", self.data.iloc[:,1].min())
        print("    Median:", self.data.iloc[:,1].median())
        print("    Max:", self.data.iloc[:,1].max())
        print("    Mean:", self.data.iloc[:,1].mean())
        print("    Standard Deviation:", self.data.iloc[:,1].std(),'\n')
        
        # Save stats into a dictionary
        stat_frame = {"Min": self.data.iloc[:,1].min(), "Median": self.data.iloc[:,1].median(), 
                      "Max": self.data.iloc[:,1].max(), "Mean": self.data.iloc[:,1].mean(),
                                     "Standard Deviation": self.data.iloc[:,1].std()}
        self.stat = stat_frame
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
    
    
    def trendTest(self, time_scale, least_records, target_alpha=0.05, plot = False): #HKM added / Jul.30.2020
        if self.data is None:
            self.data = self.getDailyDischarge()

        t_Q = self.data.rename(columns={'Flow ({})'.format(self.getUnit()):'Flow'})
        reason = "no issues"
        t_Q.Date = pd.to_datetime(t_Q.Date)
        # If we have a date gap, we should modify this code lines
        # Here, I assume that USGS provides continuous data
        valid_flag = True
        if time_scale == 'M': # Monthly trend
            t_Q_aggr = t_Q.groupby(t_Q.Date.dt.strftime('%Y-%m')).Flow.agg(['mean'])
            t_aggr_date = (t_Q.Date.apply(lambda x : x.replace(day=1)).unique())

            if len(t_Q_aggr) < least_records: # We should have more than 10-year lenth of data
                valid_flag = False
                reason = "data shortage"
                print(f'    Data at this gage has records shorter than your defined {least_records} months.\n')

        elif time_scale == 'Y': # Yearly trend
            t_Q_aggr = t_Q.groupby(t_Q.Date.dt.strftime('%Y')).Flow.agg(['mean'])
            t_aggr_date = (t_Q.Date.apply(lambda x : x.replace(month=1, day=1)).unique())

            if len(t_Q_aggr) < least_records: # We should have more than 10-year lenth of data
                valid_flag = False
                reason = "data shortage"
                print(f'    Data at this gage has records shorter than your defined {least_records} years.\n')

        else:
            raise Exception('Invalid time scale. Please select M (monthly trend) or Y (yearly trend)')

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
            trend_result = np.nan
            slope_result = np.nan
            R_TS = np.nan
            R_MK = np.nan
            reason = "other issues rather than the data shortage"
       
        if plot: # monthly or yearly plot with the regression line
            if (trend_result == -1) | (trend_result == 1):
                fig, ax = plt.subplots(figsize=(15,5))
                ax.plot(t_aggr_date, y, t_aggr_date, R_TS[0]*np.arange(len(t_aggr_date)) 
                        + R_TS[1], 'r--', linewidth=2)
                ax.set_xlabel('Date', fontsize=12)
                ax.set_ylabel('Discharge {}'.format(self.getUnit()), fontsize=12)
                
                if time_scale == 'Y':
                    ax.set_title('Yearly Discharge at USGS {}'.format(self.id),fontsize = 16)
                else:
                    ax.set_title('Monthly Discharge at USGS {}'.format(self.id),fontsize = 16)
         
            elif trend_result == 0:
                fig, ax = plt.subplots(figsize=(15,5))
                ax.plot(t_aggr_date, y, linewidth=2)
                ax.set_xlabel('Date', fontsize=12)
                ax.set_ylabel('Discharge {}'.format(self.getUnit()), fontsize=12)
                ax.set_title('Discharge at USGS {}'.format(self.id),fontsize = 16)
                plt.text(t_aggr_date[round(len(t_aggr_date)/2)], (max(y)-min(y))/2, 
                         "No Trend", size=50, rotation=30.,ha="center", va="center",
                         bbox=dict(boxstyle="round",ec=(1., 0.5, 0.5),fc=(1., 0.8, 0.8),))
                
            else:
                raise Exception('Not enough data to plot')
                
        return trend_result, slope_result, R_TS, R_MK, reason
            
        


## Test example
#import time
#stime = time.time()
#data = pd.read_csv("gages_list.csv", dtype=str)
#trend_out = pd.DataFrame(columns = ['GageID','Start Data','End Data', 'Min','Median','Max','Mean','slope (M)','p-value (M)','slope (Y)', 'p-value (Y)','County','CountyID','State','Coordinate'])
#count = 0
#for i in range(len(data)):
#    rcode = data["SOURCE_FEA"][i]
#    print("Working on gage", rcode)
#    try:
#        site = USGS_Gage_DataRetriever(rcode,  metric=False)
#        stat = site.getStatistics()
#        trend_result_m, slope_result_m, R_TS_m, R_MK_m, reason = site.trendTest('M', 120)
#        trend_result_y, slope_result_y, R_TS_y, R_MK_y, reason = site.trendTest('Y', 10)
#        geoMeta = site.getGeoMetaData()
#        
#        trend_out.loc[count] = [site.id, site.startdate, site.enddate, stat['Min'], stat['Median'], stat['Max'], stat['Mean'], R_TS_m[0], R_MK_m[-1], R_TS_y[0], R_MK_y[-1],
#                                geoMeta['County'], geoMeta['CountyFIPS'], geoMeta['State'],geoMeta['Coordiantes']]
#        
#        count +=1
#        # site.getGeoMetaData()
#        print('{} completed'.format(round((i+1)/len(data)*100,2)))
#    except:
#        
#        print("Fail to find data.")
#        continue
#print(time.time()-stime)








