import matplotlib.pyplot as plt
from matplotlib import dates
import pandas as pd
import urllib
import json
import numpy as np
from bs4 import BeautifulSoup
import requests

class USGS_Gage:
    
    def __init__(self, usgsid, st, ed, metric=True):
        self.id = str(usgsid)
        self.ismetric = metric
        self.startdate = st
        self.enddate = ed
        self.data = None
    
    # A method to get daily discharge time-series 
    def getDailyDischarge(self):
        # Get the JSON file from USGS server
        url = 'https://waterservices.usgs.gov/nwis/dv/?format=json&sites={}&startDT={}&endDT={}&siteStatus=all'.format(
                self.id, self.startdate, self.enddate)
        response = json.loads(urllib.request.urlopen(url).read())
        
        # Retrieve the data from JSON file
        pull = response['value']['timeSeries'][1]['values'][0]['value']
        
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
        print("Standard Deviation:", self.data.iloc[:,1].std())
        
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
    def plotTimeSeries(self, savefig=False):
        
        if self.data is None:
            self.data = self.getDailyDischarge()
        
        # Set the frame of plot
        fig, ax = plt.subplots(figsize=(15,5))
        ax.plot(pd.to_datetime(self.data['Date']), pd.to_numeric(self.data['Flow ({})'.format(self.getUnit())]), linewidth=2)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Discharge {}'.format(self.getUnit()), fontsize=12)
        ax.set_title('Discharge at USGS {}'.format(self.id),fontsize = 16)
        
        # If savefig is True, save the plot to local drive
        if savefig:
            fig.savefig('USGS_{}'.format(self.id))
    
    # A method to find the top X discharges and corresponding dates
    def findLargestEvents(self, top_x):
        if self.data is None:
            self.data = self.getDailyDischarge()
        # Sort the data in desending order and choose the top x events
        dat = self.data.sort_values(by = ['Flow ({})'.format(self.getUnit())], ascending=False).reset_index(drop=True)
        return dat.iloc[:top_x,]
    
    def getMetaData(self):
        url = f'https://waterdata.usgs.gov/va/nwis/uv?site_no={self.id}'
        response = requests.get(url)
        html = response.content
        # use Beuatifulsoup to print tidier html
        soup = BeautifulSoup(html,features="lxml")
        #print (soup)
        rows = soup.find_all('tr')
        table = [[td.getText() for td in rows[i].findAll('td')]
                    for i in range(len(rows))]
        # extract metadata
        iterRow = 2
        metaData = []
        while table[iterRow] != []:
            variableName = table[iterRow][1].split()[1]
            variableID = table[iterRow][1].split()[0]
            startDate = table[iterRow][2]
            endDate = table[iterRow][3]
            newL = [{variableName:variableID},
                                       {"startDate":startDate},{"endDate":endDate}]
            metaData.append(newL)
            iterRow += 1
        return metaData
## Test example
        
start_date = '2010-01-01'
end_date = '2015-12-31'
site = USGS_Gage('02040000', start_date, end_date, metric=False)

data = site.getDailyDischarge()
mD = site.getMetaData()


