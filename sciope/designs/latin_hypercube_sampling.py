# Copyright 2017 Prashant Singh, Fredrik Wrede and Andreas Hellander
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Latin Hypercube Sampling Initial Design
Implemented as a Translational Propagation LHD
Implementation follows structure from the original reference below.

Ref:
Viana, Felipe AC, Gerhard Venter, and Vladimir Balabanov.
"An algorithm for fast optimal Latin hypercube design of experiments."
International journal for numerical methods in engineering 82, no. 2 (2010): 135-156.
"""

# Imports
from sciope.designs.initial_design_base import InitialDesignBase
from sciope.utilities.housekeeping import sciope_logger as ml
from scipy.spatial.distance import cdist, pdist
import numpy as np
from dask import delayed
from dask.distributed import wait, get_client
import dask.array as da

def _cluster_mode():
    try:
        get_client()
        return True
    except ValueError:
        return False


# Class definition
class LatinHypercube(InitialDesignBase):
    """
    Translational Propagation Latin Hypercube Sampling

    * InitialDesignBase.generate(n)
    """

    def __init__(self, xmin, xmax, use_logger=False, seed_size=None):
        """
        LatinHypercube constructor
        :param xmin: lower bounds for domain in form of a np array containing one value per dimension/variable
        :param xmax: upper bounds, as above
        :param use_logger: enable/disable logging to file and console output
        :param seed_size: number of points in the LHS seed design
        """
        name = 'LatinHypercube'
        super(LatinHypercube, self).__init__(name, xmin, xmax, use_logger)
        self._seed_size = len(xmin) if seed_size is None else seed_size
        self._nv = len(xmin)  # dimensionality / # variables
        assert (1.0 <= self._seed_size <= len(xmin))
        if self.use_logger:
            self.logger = ml.SciopeLogger().get_logger()
            self.logger.info("Latin hypercube design in {0} dimensions initialized".format(len(self.xmin)))

    @delayed
    def _tplhsdesign(self, n, seed, ns):
        """
        Creates a LH using translational propagation.
        :param n:      # of desired points
        :param seed:    initial seed design
        :param ns:      # of points in the seed design
        :return:        generated LHD x
        """
        # Define the size of TPLHD
        # Num. of divisions
        nd = np.power((n / ns), (1 / self._nv))
        nd_star = np.ceil(nd)

        # if true, create bigger LHD, else not
        nb = np.power(nd_star, self._nv) if nd_star > nd else n / ns

        # Size of TPLHD to be created
        np_star = nb * ns

        # Reshape the seed to properly create the first design
        seed = self._reshape_seed(seed, ns, np_star, nd_star).compute()

        # Create a TPLHD with np_star points
        x = self._create_tplhd(seed, np_star, nd_star).compute()

        # Resize if necessary
        if np_star > n:
            x = self._resize_tplhd(x, np_star, n).compute()

        return x

    @delayed
    def _reshape_seed(self, seed, ns, np_star, nd_star):
        """
        Scales the seed design as needed.
        :param seed:    initial seed design (between 1 and ns)
        :param ns:      # of points in the seed design
        :param np_star: # of points in the LH
        :param nd_star: # of divisions in the LH
        :return:        the scaled design
        """
        if ns == 1:
            seed = np.ones(shape=(1, self._nv))
            return seed
        else:
            uf = ns * np.ones(shape=(1, self._nv))
            ut = ((np_star / nd_star) - nd_star * (self._nv - 1) + 1) * np.ones(shape=(1, self._nv))
            a = (ut - 1) / (uf - 1)
            b = ut - a * uf
            return np.round(a * seed + b)

    @delayed
    def _create_tplhd(self, seed, np_star, nd_star):
        """
        Generate a TP LHD
        :param seed:    initial seed design
        :param np_star: # points in the LH
        :param nd_star: # divisions in the LH
        :return:        generated design x
        """
        x = seed
        for c1 in range(0, self._nv):
            # propagate
            seed = x

            # translate
            d = np.concatenate((np.power(nd_star, c1 - 1) * np.ones(np.max((c1, 0))), [np_star / nd_star],
                                np.power(nd_star, c1) * np.ones(self._nv - np.max((c1, 0)) - 1)))

            for c2 in np.arange(1, nd_star):
                seed = seed + d
                x = np.vstack((x, seed))

        np.testing.assert_equal(x.shape, (np_star, self._nv))
        return x

    @delayed
    def _resize_tplhd(self, x, np_star, n):
        """
        In case the design is larger than requested, resize it. Else, return unchanged.
        :param x:       initial design
        :param np_star: # of initial design points
        :param n:       # of desired design points
        :return:        design x of correct dimensions
        """
        # centre of the design space
        centre = np_star * np.ones((1, self._nv)) / 2.

        # calculate distance between each point in x and the centre of the design space
        distances = cdist(x, centre).ravel()
        idx = np.argsort(distances)

        # correct the size of x
        x = x[idx[:n], :]

        # re-establish LH conditions
        x -= np.min(x, axis=0) - 1

        # remove spaces
        x_sorted = np.argsort(x, axis=0)
        x[x_sorted, np.arange(self._nv)] = np.tile(np.arange(1, n + 1), (self._nv, 1)).T
        np.testing.assert_equal(x.shape[0], n)
        return x

    @delayed
    def generate(self, n):
        """
        Sub-classable method for generating 'n' points in the given 'domain'.
        Generate several candidate designs, rank them based on inter-site distance and select the top-ranked candidate
        Implementation similar to gpflowopt/LHD
        """
        candidates = []
        scores = []
        nv = len(self.xmin)
        for i in np.arange(1, min(n, self._seed_size) + 1):
            if i < 3:
                # 1/2 points
                seed = delayed(np.arange(1, i + 1)[:, None] * np.ones(shape=(1, nv)))
            else:
                # Larger seeds using recursive division
                seed = LatinHypercube(self.xmin, self.xmax, self.use_logger, seed_size=i - 1).generate(i)

        # Create candidate designs and compute inter-site distance
        ns = seed.shape[0]
        x = self._tplhsdesign(n, seed, ns).compute()
        candidates.append(x)
        scores.append(np.min(pdist(x)))

        # Select the top-ranked candidate
        lhd = candidates[np.argmax(scores)]

        # Scale to [xmin, xmax]
        lhd_scaled = self.scale_to_new_domain(lhd, self.xmin, self.xmax)

        if self.use_logger:
            self.logger.info("Latin hypercube design: generated {0} points in {1} dimensions".format(n, nv))

        return lhd_scaled

    def draw(self, n_samples, n=50, auto_redesign=True):

        if not hasattr(self, 'generated'):
            if _cluster_mode:
                lhd = self.generate(n).persist()
                wait(lhd)
            else:
                lhd = self.generate(n)
            
            lhd_array = da.from_delayed(lhd, shape=(n, self._nv), dtype=np.float)
            self.generated = lhd_array #store for sampling of design


        if not hasattr(self, 'random_idx'):
            self.random_idx = np.arange(self.generated.shape[0])
        
        len_random = len(self.random_idx)
        if len_random == 0:
            del self.generated
            del self.random_idx
            if auto_redesign:
                if self.use_logger:
                    self.logger.info("{0} points left to draw form Latin hypercube design:\
                    computing new design for {0} points".format(n))
                return self.draw(n_samples, n)
            else:
                raise(ValueError)("{0} points left to draw form Latin hypercube design:\
                 clearing design".format(len_random))

        if n_samples > len_random: 
            if self.use_logger:
                self.logger.info("Only {0} points left to draw form Latin hypercube design:\
                    setting n_samples to {0}".format(len_random))
            idx = range(len_random)
        else:   
            idx = np.random.choice(range(len_random), n_samples, replace=False)
        
        delays = []
        for i in idx:
            rand_idx = self.random_idx[i]
            delay = self.generated[rand_idx].to_delayed()[0]
            delays.append(delay)
            
        self.random_idx = np.delete(self.random_idx, idx)    

        return delays

