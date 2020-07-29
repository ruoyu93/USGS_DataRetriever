import matplotlib.pyplot as plt
import pandas as pd
import urllib.request
import json
import numpy as np
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
from pandas.plotting import register_matplotlib_converters
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
            date = [i['dateTime'][0:10] for i in pull]
            
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








