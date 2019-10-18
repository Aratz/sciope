
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from sciope.inference import abc_inference
from sciope.models.cnn_regressor import CNNModel
from sciope.models.pen_regressor_beta import PEN_CNNModel
from sciope.models.dnn_regressor import ANNModel


import numpy as np

import pickle
import time
from normalize_data import normalize_data, denormalize_data
from load_data import load_spec
from vilar_all_species import Vilar_model


plt.plot(np.random.rand(100))
plt.savefig('randomplot.png')

num_timestamps=401
endtime=200
modelname = "vilar_ACR_" + str(endtime) + "_" + str(num_timestamps) + '_all_species'
# parameter range
dmin = [30, 200, 0, 30, 30, 1, 1, 0, 0, 0, 0.5, 0.5, 1, 30, 80]
dmax = [70, 600, 1, 70, 70, 10, 12, 1, 2, 0.5, 1.5, 1.5, 3, 70, 120]

#5,6,7,8
#6=C, 7=A, 8=R
species = [6]





clay=[32,48,64,96]
ts_len = 401
nr_of_species = len(species)
print("species: ", species)

# choose neural network model
nnm = CNNModel(input_shape=(ts_len,nr_of_species), output_shape=(15), con_len=3, con_layers=clay, dense_layers=[100,100,100])
# nnm = ANNModel(input_shape=(ts_len, train_ts.shape[2]), output_shape=(15), layers=[100,100,100])
# nnm = PEN_CNNModel(input_shape=(train_ts.shape[1],train_ts.shape[2]), output_shape=(15), pen_nr=3, con_layers=clay, dense_layers=[100,100,100])

print("Model name: ", nnm.name)


true_param = pickle.load(open('datasets/' + modelname + '/true_param.p', "rb" ) )
true_param = np.squeeze(np.array(true_param))
print("true_param shape: ", true_param.shape)
data = pickle.load(open('datasets/' + modelname + '/obs_data_pack.p', "rb" ) )
# data = data[3]
# data = np.expand_dims(data,0)
print("data shape: ", data.shape)

nnm.load_model()


test_thetas = pickle.load(open('datasets/' + modelname + '/test_thetas.p', "rb" ) )
test_ts = pickle.load(open('datasets/' + modelname + '/test_ts.p', "rb" ) )
test_ts = test_ts[:,:,species]
test_thetas_n = normalize_data(test_thetas,dmin,dmax)
test_pred = nnm.predict(test_ts)
test_pred = np.reshape(test_pred,(-1,15))
test_pred_d = denormalize_data(test_pred,dmin,dmax)
test_mse = np.mean((test_thetas-test_pred)**2)
test_mae = np.mean(abs(test_thetas-test_pred_d))
test_ae = np.mean(abs(test_thetas-test_pred_d),axis=0)
test_ae_norm = np.mean(abs(test_thetas_n-test_pred),axis=0)




print("Model name: ", nnm.name)
print("mean square error: ", test_mse)
print("mean rel absolute error: ", np.mean(test_ae_norm))



Vilar_ = Vilar_model(num_timestamps=num_timestamps, endtime=endtime)
simulate = Vilar_.simulate

true_params = [[50.0, 500.0, 0.01, 50.0, 50.0, 5.0, 10.0, 0.5, 1.0, 0.2, 1.0, 1.0, 2.0, 50.0, 100.0]]
obs_data = np.zeros((20,num_timestamps,1))
for i in range(20):
    od = simulate(np.array(true_params))[:,species]
    # print("od shape: ", od.shape)
    obs_data[i,:,:] = od

pred_param = denormalize_data(nnm.predict(obs_data),dmin,dmax)

gen_data = np.zeros((20,num_timestamps,1))

for i in range(20):
    od = simulate(pred_param[i])[:,species]
    # print("od shape: ", od.shape)
    gen_data[i,:,:] = od


f,ax = plt.subplots(3,1)

t= np.linspace(0,200,401)
for ts in obs_data:
    ax[0].plot(t,ts[:,0],c='blue')
    ax[2].plot(t,ts[:,0],c='blue')


for ts in gen_data:
    ax[1].plot(t,ts[:,0],c='red')
    ax[2].plot(t,ts[:,0],c='red')


plt.savefig('comp.png')














