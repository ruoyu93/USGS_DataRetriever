
"""
Created on Wed Jul 22 19:04:49 2020
5.9 Assignment: Module 5 Live Session Exercise: Testing Activity
Yibo Wang (yw9et)
Ruoyu Zhang (rz3jr)
KEYU CHEN (km5ar)
Yusheng Jiang (yj3tp)
Hyunglok Kim (hk5kp)
"""



## Unit test
import unittest
from USGS_FlowData_utils import *
import datetime
import time
import numpy as np


#####################################################################################
# unit test 1 test __init__ , part 1 
#####################################################################################
class USGS_DataRetriever_Test(unittest.TestCase):       
    def test__init__id(self):         # test __init__, if the id number is correct
        data1 = USGS_Gage_DataRetriever('01654000') # set up
        self.assertEqual(len(data1.id),8)  # test if the lenth of the number is 8
        
if __name__ == '__main__':
    unittest.main()         

#####################################################################################
# unit test 2  test __init__, part 2
#####################################################################################

class USGS_DataRetriever_Test(unittest.TestCase):  
    def test__init__vars_info(self):   # test __init__, if vars_info have the correct information 
        data1 = USGS_Gage_DataRetriever('01654000')  # set up 
        self.assertEqual(len(data1.vars_info['Variables'][0]['variableID']),5) # test if the lenth of the data meet our requriement
        
if __name__ == '__main__':
    unittest.main()   

#####################################################################################
# unit test 3 test __info__, part 3 
#####################################################################################

class USGS_DataRetriever_Test(unittest.TestCase):
    def test__init__vars_info2(self):  # test __init__
        data1 = USGS_Gage_DataRetriever('01654000')   # set up 
        self.assertEqual(data1.vars_info['Variables'][1]['variableName'],'Discharge(Mean)')
        # see if the variableName meet our requriement
        
if __name__ == '__main__':
    unittest.main()   

#####################################################################################
# unit test 4  test getDailyDischarge()
#####################################################################################

class USGS_DataRetriever_Test(unittest.TestCase):
    def test_getDailyDischarge(self):      
        test5 = USGS_Gage_DataRetriever("01656120")   # set up
        df5 = test5.getDailyDischarge()  # access test5.getDailyDischarge() then create a new variables called "df5"
        col1 = type(datetime.datetime.strptime(df5["Date"][0],'%Y-%m-%d'))   # check the type of the data
        col2 = type(float(df5["Flow (cms)"][0]))
        col_list = [col1, col2]   # save it into the list
        print(col_list)
        self.assertEqual(col_list, [datetime.datetime, float])   # check if all the data meet our requirmeent
        self.assertEqual(df5["Date"][0], '1996-10-01')  # check if the data 
        self.assertEqual(df5["Flow (cms)"][0], 2.888318392820472)  # 
        
if __name__ == '__main__':
    unittest.main()


#####################################################################################
# unit test 5 test getStatistics()
#####################################################################################



class USGS_DataRetriever_Test(unittest.TestCase):        
    def test_getStatistics(self):
        data1 = USGS_Gage_DataRetriever('01654000')
        test_Stat = data1.getStatistics()
        test_min = test_Stat['Min']
        test_max = test_Stat['Max']
        test_median = test_Stat['Median']
        test_mean = test_Stat['Mean']
        test_std = test_Stat['Standard Deviation']
        test_stat_list = [test_min,test_median,test_max,test_mean,test_std]
        self.assertEqual(test_stat_list,[0.0,0.33980216386123197,101.9406491583696,0.8433053699018033,2.3510523574195155]) 
        #1. first to check the value of each key in the return dictionary of getStatistics() is the expected value
        type_min = type(test_Stat['Min'])
        type_max = type(test_Stat['Max'])
        type_median = type(test_Stat['Median'])
        type_mean = type(test_Stat['Mean'])
        test_std = type(test_Stat['Standard Deviation'])
        type_list = [type_min,type_max,type_median,type_mean,test_std]
        self.assertEqual(type_list, [float, float, float, float, float])
        #2. next to check the type of the value in each key is the correct one

if __name__ == '__main__':
    unittest.main()




#####################################################################################
# unit test 6 - test etStatistics()
#####################################################################################



class USGS_DataRetriever_Test(unittest.TestCase):  
    def test_getStatistics_2(self):
        data1 = USGS_Gage_DataRetriever('01654000')
        test_Stat = data1.getStatistics()
        self.assertEqual(len(test_Stat),5)  # to check the length of the return value of getStatistics() function is correct or not
if __name__ == '__main__':
    unittest.main()  
    
#####################################################################################
# unit test 7
#####################################################################################


class USGS_DataRetriever_Test(unittest.TestCase):
    def test_getUnit(self):
        data1 = USGS_Gage_DataRetriever('01654000')
        test_Stat = data1.getStatistics()
        self.assertEqual(data1.getUnit(),'cms')  
        # to check if the type of the return value of getUnit() function 
# is 'cms' or 'cfs'(cubit foot/meter per second)
if __name__ == '__main__':
    unittest.main()  
    
#####################################################################################
# unit test 8 - test findLargestEvents()
#####################################################################################


class USGS_DataRetriever_Test(unittest.TestCase):        
    def test_findLargestEvents(self):        
        test = USGS_Gage_DataRetriever("01656120")  # setup 
        test_1 = test.findLargestEvents(10)  # find the largest 10 events and save it into test_1
        self.assertTrue(len(test_1) == 10)    #test if the len of test_1 is 10
        self.assertEqual(type(test_1['Date'][0]), str) # check the type is str
        self.assertEqual(type(test_1['Flow (cms)'][0]), np.float64)  # check if the data is np.float64
        self.assertEqual(test_1['Flow (cms)'][0], 161.9723647738539) # check if the numeric number equal what we are looking for
        self.assertEqual(test_1['Flow (cms)'][1], 145.8317619904454) # check if the numeric number equal what we are looking for
        self.assertEqual(test_1['Date'][0], '1998-02-05')  # check if the data meet our expectation
        self.assertEqual(test_1['Date'][1], '1998-03-21')  # check if the data meet our expectation
        
if __name__ == '__main__':
    unittest.main()

#####################################################################################
# unit test 9 - test the getVarsMetaData()
#####################################################################################    

class USGS_DataRetriever_Test(unittest.TestCase):
    def test_getVarsMetaData(self):       # test the getVarsMetaData
        test1 = USGS_Gage("01656120")    # setup
        df = test1.getVarsMetaData()
        col1 = type(df["Variable Name"][0])   # check the type of first value of df['Variable Name']
        col2 = type(int(df["Variable ID"][0]))
        col3 = type(datetime.datetime.strptime(df["Start Date"][0],'%Y-%m-%d'))
        col4 = type(datetime.datetime.strptime(df["End Date"][0],'%Y-%m-%d'))
        col_list = [col1, col2, col3, col4]  # save all the type into my list 
        print(col_list)                    
        self.assertEqual(col_list, [str, int, datetime.datetime, datetime.datetime]) 
        # assertEqual to see if all the format meet our expectation
        self.assertEqual(df["Start Date"][0], '1996-10-01') 
        # check if the first value from " Start Date" meet our expectation
        self.assertEqual(df["End Date"][1], '1999-12-31')
        # check if the first value from " Start Date" meet our expectation
        self.assertEqual(df["Variable Name"][1], 'Suspnd sedmnt conc(Mean)')
        # check if the second value from "Variable Name" meet our expectation
        self.assertEqual(df["Variable ID"][2], '80155')
        # check if the 3rd value from "Variable ID" meet our expectation

if __name__ == '__main__':
    unittest.main()  
    
#####################################################################################
# unit test 10 - test the etGeoMetaData()
#####################################################################################


class USGS_DataRetriever_Test(unittest.TestCase):  
    def test_getGeoMetaData(self):   
        test4 = USGS_Gage_DataRetriever("01656120") # set up
        res = test4.getGeoMetaData() # save test.getGeoMetaData() into a new variables 
        ele1 = type(res['Coordiantes'])  # check the type 
        ele2 = type(res['County'])
        ele3 = type(int(res['CountyFIPS']))
        ele4 = type(int(res['Gage']))
        ele5 = type(res['State'])
        ele_type_list = [ele1, ele2, ele3, ele4, ele5] # save it into a new list
        print(ele_type_list) 
        self.assertEqual(ele_type_list, [tuple, str, int, int, str])
        # check if all the type of data meet our expectation 
        self.assertEqual(res['Coordiantes'], (38.64150829, -77.5124873)) 
        # check if the value meet our expectation
        self.assertEqual(res['County'], 'Prince') 
        self.assertEqual(res['CountyFIPS'], '51153') 
        self.assertEqual(res['Gage'], '01656120') 
        self.assertEqual(res['State'], 'VA') 

if __name__ == '__main__':
    unittest.main()  
   
    
#####################################################################################
# unit test 11 - test trendTest()
#####################################################################################

class USGS_DataRetriever_Test(unittest.TestCase):  
    def test_trendTest(self):
        # set up
        site = USGS_Gage_DataRetriever("02024752")
        stat = test11.getStatistics() 
        # test if all the data meet our expectation 
        trend_result_m, slope_result_m, R_TS_m, R_MK_m, reason = site.trendTest('M', 120, target_alpha = 0.05)
        trend_result_y, slope_result_y, R_TS_y, R_MK_y, reason = site.trendTest('Y', 10,target_alpha = 0.05)
        list_test_11_m = [trend_result_m, slope_result_m, R_TS_m, R_MK_m, reason]
        list_test_11_y = [trend_result_y, slope_result_y, R_TS_y, R_MK_y, reason]
        # test if trend_result_m, slope_result_m, R_TS_m, R_MK_m, reason meet our expectation
        # test if trend_result_y, slope_result_y, R_TS_y, R_MK_y, reason meet our expectation
        
        self.assertEqual(list_test_11_m,[1,0.14427400917512528,(0.14427400917512528, 62.65598104129241,0.008914136718965527, 0.32995723856417797),(1, 0.29742600090898336, 80.32279420093022, 0.0089450212884567),'no issues'])
        self.assertEqual(list_test_11_y,[1, 4.649560190190382, (4.649560190190382, 69.51532936073576, 1.5004534761252657, 7.679532771685558), (1, 4.818729345465225, 70.80074333396409, 0.0015064528393666787), 'no issues'])
        

if __name__ == '__main__':
    unittest.main()         





