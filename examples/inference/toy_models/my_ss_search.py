import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from create_summary_statistics import summarys
import numpy as np
import pickle
import time
from normalize_data import normalize_data, denormalize_data
from load_data import load_spec
import vilar
from vilar import Vilar_model





num_timestamps=401
endtime=200
modelname = "vilar_ACR_" + str(endtime) + "_" + str(num_timestamps) + '_all_species'
# parameter range
dmin = [30, 200, 0, 30, 30, 1, 1, 0, 0, 0, 0.5, 0.5, 1, 30, 80]
dmax = [70, 600, 1, 70, 70, 10, 12, 1, 2, 0.5, 1.5, 1.5, 3, 70, 120]

#6=C, 7=A, 8=R
species = [6]




#Load data
train_thetas, train_ts = load_spec(modelname=modelname, type = "train", species=species)
print("load train data done!")

# train_sum = np.array([summarys(train_ts[i],i) for i in range(len(train_ts))])
#
# pickle.dump(train_sum, open('datasets/' + modelname + '/train_sum.p', "wb"))

train_sum = pickle.load(open('datasets/' + modelname + '/train_sum.p', "rb" ) )

obs_data = pickle.load(open('datasets/' + modelname + '/obs_data_pack.p', "rb" ) )[:,:,species]

print("obs data shape: ", obs_data.shape)

obs_sum = np.array([summarys(ts) for ts in obs_data])

print("obs_sum shape: ", obs_sum.shape)

observed_sum = obs_sum[0]

dmin = [30, 200, 0, 30, 30, 1, 1, 0, 0, 0, 0.5, 0.5, 1, 30, 80]
dmax = [70, 600, 1, 70, 70, 10, 12, 1, 2, 0.5, 1.5, 1.5, 3, 70, 120]
true_param = [50.0, 500.0, 0.01, 50.0, 50.0, 5.0, 10.0, 0.5, 1.0, 0.2, 1.0, 1.0, 2.0, 50.0, 100.0]

#k-NN(rejection sampling)
nr_of_accept = 1000
dist = np.linalg.norm(train_sum - observed_sum, axis=1)
print("dist shape: ", dist.shape)
plt.hist(dist)
plt.savefig("dist_plot")
plt.close()

accepted_ind = np.argpartition(dist,nr_of_accept)[0:nr_of_accept]
acc_dist = dist[accepted_ind]
print("acc_dist max: ", np.max(acc_dist))
print("acc_dist mean: ", np.mean(acc_dist))

print("dist max: ", np.max(dist))
print("dist mean: ", np.mean(dist))


print("accepted_ind shape: ", accepted_ind.shape)

accepted_para = train_thetas[accepted_ind]
f ,ax = plt.subplots(5,3,figsize=(20,20))
for x in range(5):
    for y in range(3):
        i=x*3+y
        ret = ax[x,y].hist(accepted_para[:,i],density=True)
        peakv = np.max(ret[0])
        ax[x, y].plot([true_param[i], true_param[i]], [peakv, 0],c='red')
        ax[x, y].plot([dmin[i], dmin[i]], [peakv, 0],c='black')
        ax[x, y].plot([dmax[i], dmax[i]], [peakv, 0],c='black')


plt.savefig("ss_posterior")