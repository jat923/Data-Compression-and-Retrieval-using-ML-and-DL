import pandas as pd
from keras.models import load_model
import numpy as np
import matplotlib.pyplot as plt
import os
from sklearn.metrics import r2_score
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import mean_squared_error
from sklearn.metrics import mean_squared_log_error

import csv
import glob
import pandas as pd
import keras
from keras.datasets import cifar10
from pathlib import Path
from keras.layers import Dense,Conv2D,MaxPooling2D,Flatten,AveragePooling2D,Dropout,BatchNormalization,Activation,Flatten
from keras.models import Model,Input,Sequential
from sklearn.model_selection import KFold
from keras.optimizers import Adam
from keras.callbacks import LearningRateScheduler
from keras.callbacks import ModelCheckpoint
from keras import optimizers
import os
import tensorflow as tf
from sklearn.decomposition import PCA
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.linear_model import LinearRegression
from keras.utils import layer_utils

model = load_model('model_V1-MissingPoints.h5')

def level_data(data):
    for j in range(26):
        temp = data[:, j]
        temp = np.interp(temp, (temp.min(), temp.max()), (0, 1))
        data[:, j] = temp
    data = data.astype("int")
    return data


def get_neighbors(data,days,features):
    data=data.reshape((days,699,639,features))
    temp = np.zeros((days, 699+ 1 * 2, 639 + 1 * 2, features))
    temp[:, 1:temp.shape[1] - 1, 1: temp.shape[2] - 1] = data

    result = np.zeros((days,699, 639, features, 3 * 3))
    for i in range(days):
        result[i, :, :, :, 0] = temp[i, 0:temp.shape[1] - 2, 0:temp.shape[2] - 2, :]
        result[i, :, :, :, 1] = temp[i, 1:temp.shape[1] - 1, 0:temp.shape[2] - 2, :]
        result[i, :, :, :, 2] = temp[i, 2:temp.shape[1] - 0, 0:temp.shape[2] - 2, :]
        result[i, :, :, :, 3] = temp[i, 0:temp.shape[1] - 2, 1:temp.shape[2] - 1, :]
        result[i, :, :, :, 4] = temp[i, 1:temp.shape[1] - 1, 1:temp.shape[2] - 1, :]
        result[i, :, :, :, 5] = temp[i, 2:temp.shape[1] - 0, 1:temp.shape[2] - 1, :]
        result[i, :, :, :, 6] = temp[i, 0:temp.shape[1] - 2, 2:temp.shape[2] - 0, :]
        result[i, :, :, :, 7] = temp[i, 1:temp.shape[1] - 1, 2:temp.shape[2] - 0, :]
        result[i, :, :, :, 8] = temp[i, 2:temp.shape[1] - 0, 2:temp.shape[2] - 0, :]

    result = result.reshape((days*699 * 639, features, 3 * 3))
    return result

def read_data(file_name):
    dataset = np.genfromtxt(file_name, dtype = "str", delimiter = ",")
    headers = dataset[0]
    data = dataset[1:,3:29].astype("float").reshape((699, 639, 26))
    return data

testfilescount = 6
testfilesnames = ['2013-06','2014-07','2015-08','2013-01','2014-12','2015-02']
final_mae=[]
final_mse=[]
final_r2=[]


file_path = os.getcwd()
for i in range(testfilescount):
    #Take Summer Testing files
    for file_name in os.listdir(file_path):
        if (file_name[-3:]=='csv' and file_name[0:7] == testfilesnames[i]):
            print('reading...' + file_name)
            result = read_data(file_name).reshape((699* 639, 26))
            result=level_data(result)     

            y=result[:,25]
            x=np.delete(result,25,1)
        #     print('Actual X shape: ' , x.shape)
        #     print('Y shape: ' , y.shape) 

            ncomp = 2
            print('Number of components taken: ', ncomp)
            X_reduced = PCA(n_components=ncomp,random_state=42).fit_transform(x)
        #     print('X_reduced shape: ' , X_reduced.shape)

            print('calling get_neighbour function...')
            result=get_neighbors(np.column_stack((X_reduced, y)),1,3)
            #np.savetxt("final_pca_reduced_data.csv", result, delimiter=",")

            ##NN start
            ntfiles = 1
            #take the rows corresponding to the last two files
            data_test = result[-699 * 639 * ntfiles:]
            #create the same input vector as in the training set, features*neighbourhood
            X_test = np.zeros((699 * 639 * ntfiles, 3 * 3 * 3))
            X_test[:, :] = data_test[:, :3].reshape((699 * 639 *ntfiles, 3 * 3 * 3))
            X_test=np.delete(X_test,22,1)
            Y_test = data_test[:, 2, 4]

            Y_pred = model.predict(X_test)
            
            print("min and max of y pred: ",min(Y_pred),max(Y_pred))
            print(Y_pred.shape)
            print()
            
            print("min and max of y pred: ",min(Y_pred),max(Y_pred))
            print(file_name, 'result: ')
            r2=r2_score(Y_test,Y_pred)
            mae=mean_absolute_error(Y_test,Y_pred)
            mse=mean_squared_error(Y_test,Y_pred)
            final_r2.append(r2)
            final_mse.append(mse)
            final_mae.append(mae)
            
            print('R2 score: ',r2_score(Y_test,Y_pred))
            print('MAE: ',mean_absolute_error(Y_test,Y_pred))
            print('MSE: ',mean_squared_error(Y_test,Y_pred))
            
            Y_pred=(Y_pred - np.min(Y_pred))/(np.max(Y_pred)-np.min(Y_pred))
            
            originalfigname = file_name + 'original_NN.png'
            preditedfigname = file_name + 'predicted_NN.png'
            
            fig1=plt.figure()
            plt.contourf(Y_test.reshape(699,639), levels = np.linspace(min(Y_test),max(Y_test),10))
            plt.colorbar()
            plt.axis('off')
            plt.savefig(originalfigname,dpi=1000)
            plt.close()

            fig2=plt.figure()
            plt.contourf(Y_pred.reshape(699,639), levels = np.linspace(0,1,10))
            plt.colorbar()
            plt.axis('off')
            plt.savefig(preditedfigname,dpi=1000)
            plt.show()
            plt.close()


            
print("NN average MSE loss",np.mean(final_mse))
print("NN average MAE",np.mean(final_mae))
print("NN average r2 score",np.mean(final_r2)) 
            
final_r2.append(np.mean(final_r2))
final_mse.append(np.mean(final_mse))
final_mae.append(np.mean(final_mae))
            
np.savetxt("NN Loss(MSE).txt", final_mse,delimiter=",")
np.savetxt("NN MAE.txt", final_mae, delimiter=",")
np.savetxt("NN r2.txt", final_r2, delimiter=",")  