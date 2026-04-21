import copy
import math
import os

import numpy as np
import matplotlib.pyplot as plt
import scipy
from joblib import Parallel, delayed
from networkx.algorithms.centrality import second_order_centrality

from kedgeswap.Graph import Graph
from kedgeswap.MarkovChain import MarkovChain
from kedgeswap.Stat import Stat


def CheckAutocorrLag1_modified(temp, S_T, alpha):
    """ Check the autocorrelation with lag 1 of a time serie.

        Parameters
        ----------
        S_T: list(float)
            List of assortativity(/number of triangles) values
            to test autocorrelation
        alpha: float
            Significance level of the test (usually fixed to 0.04).
    """
    T = len(S_T)
    tau = 10  # lag at which the sample autocorr is calculated
    mean_st = np.mean(S_T)
    var_st = np.var(S_T)

    R_1 = 1 / T * sum(np.multiply(S_T[:-1] - mean_st, S_T[1:] - mean_st))
    R_0 = 1 / T * sum(np.multiply(S_T - mean_st, S_T - mean_st))
    # a_i = R_1/R_0
    a = R_1 / R_0
    # a = np.correlate(S_T-mean_st, S_T-mean_st, mode='full')[T] # mode=full: convolution over each point of overlap - take value at T to get lag=1
    # a = a/ (var_st * len(S_T))

    mu = -1 / T
    sigma_2 = (T ** 4 - 4 * T ** 3 + 4 * T - 4) / ((T + 1) * T ** 2 * (T - 1) ** 2)
    A = (a - mu) / np.sqrt(sigma_2)
    z = scipy.stats.norm.ppf(1 - alpha)
    temp.append(A)
    if A > z:
        return 1
    else:
        return 0

def run():
    def run_chain(c):
        S_T = []
        n_swap = int(np.round(eta))
        for t in range(500):
            mc[c].run(n_swap)
            if mc[c].use_assortativity:
                S_T.append(mc[c].assortativity)
            else:
                S_T.append(len(mc[c].triangles2edges))
        return S_T

    file = os.path.join(
        os.path.dirname(__file__),
        'data',
        'ucidata-zachary',
        'egograph_edges.txt'
    )

    graph = Graph(directed=False)
    graph.read_ssv(file)
    N_swap = 1000 * graph.M

    burn_in = MarkovChain(
        graph,
        N_swap=N_swap,
        gamma=3.0,
        use_assortativity=True,
        use_fixed_triangle=True,
        use_fixed_triangle_range=9,
        verbose=True,
        old_count=False
    )
    print("burn_in")
    burn_in.run()
    print("burn_in ended")

    burn_in_rate = burn_in.accept_rate / (burn_in.accept_rate + burn_in.refusal_rate)
    eta = math.ceil(1 / burn_in_rate * graph.M)

    prev_eta = eta
    tuned = False
    plot_a = []
    eta_list = []
    plot_std = []
    S_Ts = []
    mc = []
    alpha = 0.04
    flag = 4
    second_flag = 1

    while ((second_flag > 0) and (flag > 0)):
        if eta > 250000:
            break
        flag -= 1
        d_eta = 0
        temp = []
        for c in range(10):
            if len(mc) <= c:

                mc.append(MarkovChain(copy.deepcopy(burn_in.graph), N_swap, 3, use_jd=burn_in.use_jd,
                                      use_triangles=burn_in.use_triangles,
                                      use_fixed_triangle=burn_in.use_fixed_triangle,
                                      use_assortativity=burn_in.use_assortativity,
                                      use_mutualdiades=burn_in.use_mutualdiades,
                                      verbose=burn_in.verbose, keep_record=False, log_dir=None,
                                      use_fixed_threechains=burn_in.use_fixed_threechains,
                                      use_fixed_triangle_range=burn_in.use_fixed_triangle_range,
                                      triangle_buffer=burn_in.buffer_triangle, old_count=burn_in.old_count,
                                      use_fixed_tclosedpath=burn_in.use_fixed_tclosedpath))
            else:
                mc[c] = MarkovChain(copy.deepcopy(burn_in.graph), N_swap, 3, use_jd=burn_in.use_jd,
                                      use_triangles=burn_in.use_triangles,
                                      use_fixed_triangle=burn_in.use_fixed_triangle,
                                      use_assortativity=burn_in.use_assortativity,
                                      use_mutualdiades=burn_in.use_mutualdiades,
                                      verbose=burn_in.verbose, keep_record=False, log_dir=None,
                                      use_fixed_threechains=burn_in.use_fixed_threechains,
                                      use_fixed_triangle_range=burn_in.use_fixed_triangle_range,
                                      triangle_buffer=burn_in.buffer_triangle, old_count=burn_in.old_count,
                                      use_fixed_tclosedpath=burn_in.use_fixed_tclosedpath)

        S_T = []
        S_Ts = Parallel(n_jobs=4)(delayed(run_chain)(c) for c in range(10))
        for c in range(10):
            d_c = CheckAutocorrLag1_modified(temp, S_Ts[c], alpha)
            d_eta += d_c
        plot_a.append(np.mean(temp))
        plot_std.append(np.std(temp))
        eta_list.append(eta)


        if d_eta <= 1:
            print(f"Autocorrelation test passed with eta={eta}")
            tuned = True
            second_flag -= 1
            eta = eta*2
        else:
            print(f"Autocorrelation test failed with eta={eta}")
            eta = eta*2



    print(f"Autocorrelation test passed with eta={eta}")
    plt.figure()
    plt.plot(eta_list, plot_a, marker='o')
    plt.fill_between(
        eta_list,
        np.array(plot_a) - np.array(plot_std),
        np.array(plot_a) + np.array(plot_std),
        alpha=0.2,
        label="±1 std"
    )
    plt.title("Evolution de A (test autocorr lag-1)")
    plt.xlabel("Itération")
    plt.ylabel("A")
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    run()




