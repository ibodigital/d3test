import pandas as pd
import numpy as np
import datetime
import math
from datetime import timedelta  
import os 
#'''
#For developpement :
import time
import matplotlib.pyplot as plt
from sklearn.cluster import MeanShift, estimate_bandwidth
from scipy import signal
import stumpy
#'''

debug = False;
clusteringDebug = True


def loadFile(_name) : #Returns a [bool : If it loaded the file, data : np array of the data, timestamp : array of when the measures where taken, it has the same size as data]
    try :   
        csvFile = pd.read_csv(_name) 
        print("Succesfully loaded the file")
        timeStamp =pd.to_datetime(csvFile['created'])#TO CHECK : The current csv file has this category to store the time of the log
        timeStamp =pd.to_datetime(timeStamp.dt.strftime("%Y-%m-%d %H:%M:%S"))#TO CHECK : The current csv file has this category to store the time of the log
        print(csvFile.head())
        npAccZ = np.array(csvFile['accZ'])#TO CHECK : The current csv file has this category to store the accel dat
        npAccY = np.array(csvFile['accY'])#TO CHECK : The current csv file has this category to store the accel dat
        npAccX = np.array(csvFile['accX'])#TO CHECK : The current csv file has this category to store the accel dat
        threeAxisMerged = np.abs(npAccZ) + np.abs(npAccY) + np.abs(npAccX)

        #threeAxisMerged = np.abs(npAccZ[37500:60000]) 
        threeAxisMerged = np.abs(npAccZ) 
        #threeAxisMerged = np.abs(npAccZ[:120000]) 
        #threeAxisMerged = np.abs(npAccZ[35000:55000]) 
        

        #threeAxisMerged = signal.medfilt(threeAxisMerged,3)
        

        if (debug):
            plt.plot(threeAxisMerged)
            plt.plot(npAccZ)
            plt.show()

        return True,threeAxisMerged,timeStamp
    except:
        print("Failed to load the input file")
        return False,0,0
    
def movingAverage(_a, _n=300) :
    ret = np.cumsum(_a, dtype=float)
    ret[_n:] = ret[_n:] - ret[:-_n]
    return ret[_n - 1:] / _n    
    
def sglProcessing(_sgl,_smoothingWindow=300):

    npAccCentered = _sgl-np.mean(_sgl)#Centers the data around 0

    if (debug):
        plt.plot(npAccCentered)
    
    npAccZqrd =(np.abs(npAccCentered))#it's the equivalent of the absolut value (to make all of the data positive

    npAccZFiltered = movingAverage(npAccZqrd,_smoothingWindow)#Low pass filter (averaging over a 300 elment window)
    
    
    if (debug):
        plt.plot(npAccZFiltered)
        plt.show()


    #################
    toReturn = np.zeros(10000)
    i=0
    win = int(np.size(npAccZFiltered)//10000)

    #TEST OF THE MATRIX PROFILE, Results were not intersting for the moment
    
    '''
    sgl = npAccCentered
    mpTest = True

    if mpTest : 
        _m = [3,5,10,50]
        _m = [100,500,1000]
        plt.plot(npAccCentered*2)
        for m in _m:
            mp = stumpy.stump(npAccCentered, m)
            L = 5
            cac, regime_locations = stumpy.fluss(mp[:, 1], L=L, n_regimes=2, excl_factor=1)
            print("-------------------------------------:   ",regime_locations)

            plt.plot(mp[:, 0]*10)
            plt.title("Matrix porfile")
            plt.plot((1-cac)*60)

        plt.show()
        plt.plot(npAccZFiltered)
        plt.show()
        #'''
    #End of the testing part

    if(np.size(npAccZFiltered)>10000):
        while(i<10000):


            toReturn[i] =np.mean(npAccZFiltered[i*win:(i+1)*win])
            i+=1
        return toReturn
    else:
        return npAccZFiltered    
    #################
    
    



def writToFile(_isOn, _newStampTime,_localSum):#Writes into a CSV file in the same folder as the script
    try:

        df = pd.DataFrame(data=_newStampTime, columns=["date"])
        df['value'] = _isOn
        df['localSum'] = _localSum
        dir_path = os.path.dirname(os.path.realpath(__file__))
        dir_path = os.path.join(dir_path, "export_dataframe.csv") 
        df.to_csv (dir_path, index = False, header=True)
        if (debug):
            #print(df.tail())
            pass
        print("Succesfully saved the processed file")
    except:
        print("Failed to save the CSV file")







def clustering(_smoothingWindow,_raw):

    
    #_raw = _raw[:500]#Calls the processing function#FOR DEBUG, SINGAL WHEN, THESE IS DATA FROM WHEN THE MACHINE IS NOT RUNNNING
    X = sglProcessing(_raw, _smoothingWindow)#Calls the processing function

    X = np.reshape(X, (-1, 1))
    bandwidth = estimate_bandwidth(X, quantile=0.5,n_samples=500)

    ms = MeanShift( bin_seeding=True, bandwidth=bandwidth)
    ms = MeanShift( bin_seeding=True)
    ms.fit(X)
    labels = ms.labels_
    cluster_centers = ms.cluster_centers_

    labels_unique = np.unique(labels)
    n_clusters_ = len(labels_unique)
    

    boolArray = (np.invert(labels == labels[np.argmin(X)]))*1
    boolArray = signal.medfilt(boolArray,9)
    #
    #RAJOUTER ICI L4INTERPOLATION, UNE FONCTION Qui va boucler autant de fois que neceassaire pour avoir un array de la meme taille qu'au départ
    #
    if(clusteringDebug):
        print("Number of estimated clusters : %d" % n_clusters_)
        print("Cluster centers : ", ms.cluster_centers_)
        #Input singal
        fig, ax = plt.subplots(2)

        #ax[0].plot((_raw[(_smoothingWindow//2):]-np.mean(_raw[(_smoothingWindow//2):]))*1,color="gray")
        ax[0].plot(_raw)
        ax[1].plot(X/50,color="orange")
        ax[1].plot(boolArray,color="red")
        #plt.plot((X>2000)*100)
        plt.title("Filtered in blue, in Orange is the  clustured output")
        plt.show()
   
    #return (X>30)*1#Applies the threshold, and transforms it into 1 & 0 !!!!!!!!! IS OBSELETE, IT'S NOW DYNAMIC
    return boolArray







#############################################################################
#                                                                           #
#                   Main code starts here                                   #
#                                                                           #
#############################################################################
if(debug):
    startTime = time.time()

#loaded,data,timeStamp = loadFile('./tmp/data.csv')
loaded,data,timeStamp = loadFile('./tmp/data.csv.machine')



smoothingWindow =50#TO CHECK : THe value 300 was chosen for 30 000 values, to check for less values

if  loaded :#Checks if the file was loaded correctly

    
    resizedTimeStamp = timeStamp[smoothingWindow-1:]#Calculates the size of the array after the filter is applied
    #threshHold = np.mean(processed)*0.8

    
    '''
    print("variance small batch : ",np.std(processed[:500]))
    print("variance big batch : ",np.std(processed))
    print("The median is :",np.quantile(processed,0.5))
    threshHold = (np.quantile(processed,0.5)+np.mean(processed))/2
    print("The mean is :",np.mean(processed))
    print("The threshold is : ", threshHold)
    plt.scatter(processed,processed)
    #plt.hist(processed, bins=400)
    plt.show()
    '''






    boolArray = ((clustering(smoothingWindow,data)>=1)*1)#Gets the output from the cluster, and makes sure that it's a boolean array (even if the clustering gave 3 clusters)
    


    lengthInMinutes = ((timeStamp[len(timeStamp)-1]-timeStamp[0]).total_seconds()//60)#Calculates the interval in minutes
    totalTime = np.zeros(int(lengthInMinutes))#Init of the array that will store the the 0s and 1 and will be summed up
    localSum = np.zeros(int(lengthInMinutes))#Init of the array that will store the the 0s and 1 and will be summed up
    newStampTime = []#Init. of the new time timestamp array, that has a one minute interval between measure (extrapolated)



    for i in range(int(lengthInMinutes)):
        totalTime[i] = boolArray[math.floor(len(boolArray)*(i/lengthInMinutes))]#Extrapolates if it's a one or a zero .
        newStampTime.append((timeStamp[0]+ timedelta(seconds=60)*i))#generates the new time stamps
        try:
            localSum[i]=totalTime[i]+localSum[i-1] 
        except:
            pass

    writToFile(totalTime,newStampTime,localSum)#Calls the write to a file function
    if (debug):
        plt.plot(totalTime)
        plt.show()
        print(str(sum(totalTime)/60)+"h")
        #print(startTime -time.time())
    
    


    
    #OBS : IT doesn't work for only off machine, if the filtering window is not put to 300 (the singal is too noisy, and the algorithm thinks that there are two catogires
    
    #TODO : Change the Filter for something smarter
    #TODO : Rescale the time from 10 000 to real time
    #TODO : Not fit(x) eveyrthime we have a request, but do it once, as setup procedure (an automatic one), then just "predict"

    
    
    
    
    
    
    
    
    
    
    
    
    
    
