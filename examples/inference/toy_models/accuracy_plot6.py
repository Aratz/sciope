import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sciope.inference import abc_inference
from sciope.models.cnn_regressor import CNNModel
from sciope.models.pen_regressor_beta import PEN_CNNModel
from sciope.models.dnn_regressor import ANNModel
from load_data_from_julia import load_data
import numpy as np
from AutoRegressive_model import simulate, prior
# from MovingAverage_model import simulate, prior
from sklearn.metrics import mean_absolute_error
import pickle
from normalize_data import normalize_data, denormalize_data
from load_data import load_spec
import vilar
from scipy import stats, optimize



# choose neural network model
# nnm = CNNModel(input_shape=(401,3), output_shape=(15))

# nnm = PEN_CNNModel(input_shape=(201,3), output_shape=(15), pen_nr=10)
# nm = ANNModel(input_shape=(100,1), output_shape=(2))
clay=[32,48,64,96]
nnm = CNNModel(input_shape=(401,3), output_shape=15, con_len=3, con_layers=clay, dense_layers=[100,100])
nnm.load_model()


#ABC algorithm


num_timestamps=401
endtime=200

modelname = "vilar_ACR_prior6_" + str(endtime) + "_" + str(num_timestamps)

dmin = [0,    100,    0,   20,   10,   1,    1,   0,   0,   0, 0.5,    0,   0,    0,   0]
dmax = [80,   600,    4,   60,   60,   7,   12,   2,   3, 0.7, 2.5,   4,   3,   70,   300]


true_param = pickle.load(open('datasets/' + modelname + '/true_param.p', "rb" ) )
true_param = np.squeeze(np.array(true_param))
print("true_param shape: ", true_param.shape)
data = pickle.load(open('datasets/' + modelname + '/obs_data_pack.p', "rb" ) )
data = data[3]
data = np.expand_dims(data,0)
print("data shape: ", data.shape)
# data_exp = np.expand_dims( np.expand_dims(data,axis=0), axis=2 )
# print("data_exp shape: ", data_exp.shape)

data_pred = nnm.predict(data)
data_pred_denorm = denormalize_data(data_pred,dmin,dmax)

test_thetas = pickle.load(open('datasets/' + modelname + '/test_thetas.p', "rb" ) )
# abc_trial_thetas = normalize_data(abc_trial_thetas,dmin,dmax)
test_ts = pickle.load(open('datasets/' + modelname + '/test_ts.p', "rb" ) )

test_thetas_min = np.min(test_thetas,0)
test_thetas_min_text = ["{0:.1f}".format(s) for s in test_thetas_min]

test_thetas_max = np.max(test_thetas,0)
test_thetas_max_text = ["{0:.1f}".format(s) for s in test_thetas_max]

print("min: ", test_thetas_min_text)
print("max: ", test_thetas_max_text)

test_pred = nnm.predict(test_ts)

pred_min = np.min(test_pred,0)
pred_min_text = ["{0:.1f}".format(s) for s in pred_min]

print("predict min: ", pred_min_text)


test_pred_denorm = denormalize_data(test_pred,dmin,dmax)
test_thetas_norm = normalize_data(test_thetas,dmin,dmax)
mean_dev = np.mean(abs(test_thetas_norm-test_pred), axis=0)
print("mean dev shape: ", mean_dev.shape)
print("mean deviation(", np.mean(mean_dev), "):: ", mean_dev)

bpi = np.argsort(mean_dev)[:4] # best_param_ind
para_names = vilar.get_parameter_names()

for i in range(15):
    pk = para_names[i]
    pks = pk.split("_")
    if len(pks) > 1:
        pk_p = "\hat{\\" + pks[0].lower() + "}_{" + pks[1].upper() + "}"
        pk = pks[0].lower() + "_{" + pks[1].upper() + "}"
    if len(pks) == 3:
        print("len 3: ", pks[2])
        if pks[2] == 'prime':
            pk_p = pk_p + "'"
            pk = pk + "'"

    para_name_p = "$" + pk_p + "$"
    para_names[i] = "$\\" + pk + "$"

lwidth = 3
f,ax = plt.subplots(3,5,figsize=(50,30))
plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=0.15, hspace=0.15)
for x in range(3):
    for y in range(5):
        i = x*5+y
        ax[x,y].set_title(para_names[i])
        # ax[x,y].scatter(test_thetas[:,i],test_pred_denorm[:,i],s=0.4,alpha=0.1)
        # ax[x,y].hist2d(test_thetas[:,i],test_pred_denorm[:,i],bins=50)
        ax[x,y].hist2d(test_thetas_norm[:,i],test_pred[:,i],bins=100)

        # ax[x,y].plot([dmin[i], dmax[i]],[dmin[i],dmax[i]],c='green',ls='--',lw=lwidth)
        # ax[x, y].plot([dmin[i], dmin[i], dmax[i], dmax[i], dmin[i]], [dmin[i], dmax[i], dmax[i], dmin[i], dmin[i]],
        #               lw=lwidth, c='b')

        ax[x, y].plot([0, 0, 1, 1, 0], [0, 1, 1, 0, 0],
                      lw=lwidth, c='b')

plt.savefig('accuracyplot6')
print("new save")