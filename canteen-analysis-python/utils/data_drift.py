from sklearn.cluster import KMeans
import numpy as np
from scipy.stats import chi2_contingency
import matplotlib.pyplot as plt
from sklearn.metrics.pairwise import euclidean_distances
from sklearn.neighbors import NearestNeighbors


class EIkMeans():

    def __init__(self, k, lambdas=None, C=None, amplify_coe=None):

        self.k = k
        self.lambdas = lambdas
        self.theta = np.arange(0.0, 1.0, 0.05)
        self.C = C
        self.amplify_coe = amplify_coe

    def get_copy(self):
        new_copy = EIkMeans(self.k, self.lambdas, C=self.C, amplify_coe=self.amplify_coe)
        return new_copy

    def fill_lambda(self, data):

        C = self.C
        amplify_coe = self.amplify_coe
        dist_mat = euclidean_distances(C, data)
        C_idx = self.amplify_cluster(dist_mat, amplify_coe)
        k_list, unique_count = np.unique(C_idx, return_counts=True)
        # ===========#
        # plot test #
        # ===========#
        for i in np.flip(k_list):
            idx = np.where(C_idx == i)
            plt.scatter(data[idx[0], 0], data[idx[0], 1])
        # plt.show()

        k_list, unique_count = np.unique(C_idx, return_counts=True)
        self.lambdas = np.zeros(k_list.max() + 1)
        self.lambdas[k_list.astype(int)] = unique_count

    def build_partition(self, data_train, test_size):

        ini_size = 2000
        min_k_ratio = 0
        min_num_sample = 50

        m = data_train.shape[0]
        if m > ini_size:
            data_ini = data_train[:ini_size]
        else:
            data_ini = data_train

        m_ini = data_ini.shape[0]
        min_5 = test_size / 5
        min_50 = m / 50
        min_num_p = int(np.min([min_5, min_50]))
        self.k = np.min([min_num_p, self.k])
        k = self.k
        unique_count = [0]
        C_idx = np.zeros(m_ini)

        k += 1
        num_insts_part = int(np.max([m_ini / (k - 1) * min_k_ratio, min_num_sample]))

        while np.min(unique_count) < num_insts_part:
            k -= 1

            if k == 1:
                # protection
                initial_medoids = self.greed_compact_partition(data_ini, self.k)
                kmeans = KMeans(n_clusters=self.k, n_init=1, init=data_ini[initial_medoids], random_state=0).fit(
                    data_ini)
                C = kmeans.cluster_centers_
                amplify_coe = np.ones(self.k)
                break

            print('num_cluster', k)
            num_insts_part = int(np.max([m_ini / (k - 1) * min_k_ratio, min_num_sample]))

            # greedy ini
            initial_medoids = self.greed_compact_partition(data_ini, k)

            kmeans = KMeans(n_clusters=k, n_init=1, init=data_ini[initial_medoids], random_state=0).fit(data_ini)
            C_idx = kmeans.labels_
            C = kmeans.cluster_centers_

            k_list, unique_count = np.unique(C_idx, return_counts=True)

            dr = unique_count / (m_ini / k)

            for _theta in self.theta:

                if (dr.shape[0]) < k:
                    break
                amplify_coe = np.exp((dr - 1) * _theta)
                C_idx = self.amplify_shrink_cluster(data_ini, C, amplify_coe)
                k_list, unique_count = np.unique(C_idx, return_counts=True)
                temp_unique_count = np.zeros(k)
                temp_unique_count[k_list.astype(int)] = unique_count
                unique_count = temp_unique_count
                dr = unique_count / int(m_ini / k)
                if np.min(unique_count) > num_insts_part:
                    break

        # ===========#
        # fine tune #
        # ===========#
        self.C = C
        self.amplify_coe = amplify_coe
        self.fill_lambda(data_train)

    def drift_detection(self, data_test, alpha):

        lambdas = self.lambdas
        k = len(lambdas)

        C = self.C
        amplify_coe = self.amplify_coe
        dist_mat = euclidean_distances(C, data_test)
        C_idx = self.amplify_cluster(dist_mat, amplify_coe)
        observations = np.zeros(k)

        k_list, unique_count = np.unique(C_idx, return_counts=True)
        observations[k_list.astype(int)] = unique_count
        contingency_table = np.array([lambdas, observations])
        chi2, p, dof, ex = chi2_contingency(contingency_table)
        h = 0
        if p < alpha:
            h = 1
        return h

    def drift_detection2(self, data_test, alpha):

        lambdas = self.lambdas
        k = len(lambdas)

        C = self.C
        amplify_coe = self.amplify_coe
        dist_mat = euclidean_distances(C, data_test)
        C_idx = self.amplify_cluster(dist_mat, amplify_coe)
        observations = np.zeros(k)

        k_list, unique_count = np.unique(C_idx, return_counts=True)
        observations[k_list.astype(int)] = unique_count
        contingency_table = np.array([lambdas, observations])
        chi2, p, dof, ex = chi2_contingency(contingency_table)
        h = 0
        return p

    def amplify_cluster(self, dist_mat, amplify_coe, medoids_index=None):

        k = amplify_coe.shape[0]
        if medoids_index is None:
            C_X_dist = dist_mat
            m = dist_mat.shape[1]
        else:
            C_X_dist = dist_mat[medoids_index]
            m = dist_mat.shape[0]
        amplify_coe_mat = np.repeat(amplify_coe, m, axis=0)
        amplify_coe_mat = amplify_coe_mat.reshape(k, m)
        C_X_dist_amplified = C_X_dist * amplify_coe_mat
        np.argmin(amplify_coe_mat, axis=0)
        C_idx = np.argmin(C_X_dist_amplified, axis=0)
        return C_idx

    def amplify_shrink_cluster(self, data, C, amplify_coe):

        m = data.shape[0]
        k = C.shape[0]
        C_dist_mat = euclidean_distances(C, data)
        amplify_coe_mat = np.repeat(amplify_coe, m, axis=0)
        amplify_coe_mat = amplify_coe_mat.reshape(k, m)
        C_X_dist_amplified = C_dist_mat * amplify_coe_mat
        np.argmin(amplify_coe_mat, axis=0)
        C_idx = np.argmin(C_X_dist_amplified, axis=0)
        return C_idx

    def greed_compact_partition(self, data, k):

        m = data.shape[0]
        p_size = int(m / k)
        temp_data = np.array(data)
        C_idx = np.zeros(m) - 1
        idx_list = np.arange(m)
        for i in range(k - 1):
            nbrs = NearestNeighbors(n_neighbors=p_size, algorithm='ball_tree').fit(temp_data)
            distances, indices = nbrs.kneighbors(temp_data)
            greed_idx = np.argsort(distances[:, -1])[-1]
            C_idx[idx_list[indices[greed_idx]]] = int(i)
            temp_data = np.delete(temp_data, indices[greed_idx], axis=0)
            idx_list = np.delete(idx_list, indices[greed_idx])

        C_idx[np.where(C_idx == -1)[0]] = int(k - 1)
        initial_medoids = np.zeros(k) - 1
        for i in range(k):
            initial_medoids[i] = np.where(C_idx == i)[0][0]
        return initial_medoids.astype(int)


class MaxMinClustering:
    def __init__(self, n_clusters, max_iterations=100, threshold=None):
        """
        初始化 Max-Min 聚类算法
        :param n_clusters: 簇的数量
        :param max_iterations: 最大迭代次数（用于中心更新）
        :param threshold: 最大最小距离阈值（可选，停止添加新簇中心的条件）
        """
        self.n_clusters = n_clusters
        self.max_iterations = max_iterations
        self.threshold = threshold
        self.cluster_centers_ = None
        self.labels_ = None

    def fit(self, X):
        """
        执行 Max-Min 聚类
        :param X: 输入数据，形状为 (n_samples, n_features)
        :return: self
        """
        # 初始化第一个簇中心
        n_samples = X.shape[0]
        idx = np.random.randint(0, n_samples)
        self.cluster_centers_ = [X[idx]]

        # 选择第二个簇中心（距离第一个中心最远的点）
        distances = np.linalg.norm(X - self.cluster_centers_[0], axis=1)
        new_center_idx = np.argmax(distances)
        self.cluster_centers_.append(X[new_center_idx])

        # 选择后续簇中心
        while len(self.cluster_centers_) < self.n_clusters:
            min_distances = np.min([np.linalg.norm(X - center, axis=1)
                                  for center in self.cluster_centers_], axis=0)
            max_min_idx = np.argmax(min_distances)
            max_min_distance = min_distances[max_min_idx]

            # 如果设置了阈值且最大最小距离小于阈值，停止添加新簇中心
            if self.threshold is not None and max_min_distance < self.threshold:
                break

            self.cluster_centers_.append(X[max_min_idx])

        # 将簇中心转换为 NumPy 数组
        self.cluster_centers_ = np.array(self.cluster_centers_)

        # 分配点到簇并可选更新簇中心
        self._assign_clusters(X)
        for _ in range(self.max_iterations):
            old_centers = self.cluster_centers_.copy()
            self._update_centers(X)
            self._assign_clusters(X)
            # 如果簇中心不再变化，提前停止
            if np.all(old_centers == self.cluster_centers_):
                break

        return self

    def _assign_clusters(self, X):
        """
        将数据点分配到最近的簇中心
        :param X: 输入数据
        """
        distances = np.array([np.linalg.norm(X - center, axis=1)
                            for center in self.cluster_centers_]).T
        self.labels_ = np.argmin(distances, axis=1)

    def _update_centers(self, X):
        """
        更新簇中心为每个簇的均值
        :param X: 输入数据
        """
        for i in range(len(self.cluster_centers_)):
            cluster_points = X[self.labels_ == i]
            if len(cluster_points) > 0:
                self.cluster_centers_[i] = np.mean(cluster_points, axis=0)

    def predict(self, X):
        """
        预测新数据的簇标签
        :param X: 新数据
        :return: 簇标签
        """
        distances = np.array([np.linalg.norm(X - center, axis=1)
                            for center in self.cluster_centers_]).T
        return np.argmin(distances, axis=1)