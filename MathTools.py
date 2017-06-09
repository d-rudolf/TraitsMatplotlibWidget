import numpy as np
from scipy.interpolate import griddata
from scipy.interpolate import RectBivariateSpline
from scipy.interpolate import interp2d, interp1d
from scipy.optimize import curve_fit
from scipy.special import erf
from sklearn.cluster import KMeans
from operator import itemgetter
import matplotlib.pyplot as plt

class Math_Util():

    def get_line_func(self, x1,x2,y1,y2):
        """
        :param x1: x coordinate first point
        :param x2: x coordinate second point
        :param y1: y coordinate first point
        :param y2: y coordinate second point
        :return: x,y arrays for interpolation
        """
        print ('getting the line ...')
        print ('x1: {}'.format(x1))
        print ('y1: {}'.format(y1))
        print ('x2: {}'.format(x2))
        print ('y2: {}'.format(y2))
        t = np.arange(0,1,1e-3)
        x = x1+(x2-x1)*t
        y = y1+(y2-y1)*t
        #xx = [[i] for i in x]
        #yy = [[i] for i in y]#
        #return np.concatenate((yy,xx), axis = 1)
        return x,y

    def interpolate(self, im, x,y):
        """
        :param im: image
        :param x,y: arrays of points at which to interpolate
        :return: result of interpolation
        """
        print('interpolating ...')
        width = im.shape[1]
        height = im.shape[0]
        list_y, list_x =range(1,height+1,1), range(1,width+1,1)
       #points = np.array([[i,j] for i in list_y for j in list_x])
       #values = im.flatten()
       #return griddata(points, values, x_i, method='nearest')
        f = interp2d(list_x,list_y,im, kind='cubic')
        image_interpolated = f(x,y)
        size = image_interpolated.shape[0]
        coord = range(0, size, 1)
        return image_interpolated[coord, coord]


    def get_dist_vec(self,x,y):
        """
        :param x,y: arrays of points for which to calculate the distance vector
        :return: Euclidean distance vector
        """
        xx = [[i] for i in x]
        yy = [[i] for i in y]
        points = np.concatenate((yy, xx), axis=1)
        x = []
        for i in range(0,len(points)):
            diff = points[i]-points[0]
            dist = np.sqrt(diff[0]**2 + diff[1]**2)
            x.append(dist)
        return x

    def fit_func(self,x,y,a,sigma,x_0,offset):
        """
        :param x: x_vec
        :param y: interpolated line
        :param a: prefactor
        :param sigma: sigma
        :param x_0: x offset
        :param offeset: y offset
        :return: (fitted parameters, covariance matrix)
        """
        fit = curve_fit(self.func,x,y,p0=[a,sigma,x_0,offset])
        print ('a: {0:.2f}'.format(fit[0][0]))
        print ('sigma: {0:.2f}'.format(fit[0][1]))
        print ('x_0: {0:.2f}'.format(fit[0][2]))
        print ('offset: {0:.2f}'.format(fit[0][3]))
        print ('covariance matrix:')
        print (' {} '.format(fit[1][0]))
        print (' {} '.format(fit[1][1]))
        print (' {} '.format(fit[1][2]))
        print (' {} '.format(fit[1][3]))

        return fit

    def func(self,x,a,sigma,x_0,offset):
        return a*erf((x-x_0)/sigma*1/np.sqrt(2))+offset

    def get_cluster(self,x,y):
        """
        uses kmeans to find two cluster
        :param x: x coords of the line
        :param y: y coords of the line
        :return: x,y values of cluster1 and cluster2
        """
        data = y.reshape(-1, 1)
        kmeans = KMeans(n_clusters=2).fit(data)
        labels = kmeans.labels_
        # label cluster in the same way
        if labels[0] == 1:
            labels = [0 if elem == 1 else 1 for elem in labels]
        cluster1_x, cluster1_y = [], []
        cluster2_x, cluster2_y = [], []
        for index, item in enumerate(labels):
            if item == 0:
                cluster1_x.append(x[index])
                cluster1_y.append(y[index])

            if item == 1:
                cluster2_x.append(x[index])
                cluster2_y.append(y[index])
        return [cluster1_x,cluster1_y],[cluster2_x, cluster2_y]

    def get_plateaus(self, cluster1, cluster2):
        """
        finds the plateaus in the clusters (to calculate the y half width later)
        :param cluster1, cluster2    
        :return: plateau region of two cluster
        """
        def norm(data):
            """
            calculates the normalized distribution
            :param data: 
            :return: normalized data
            """
            data = np.array(data)
           # print 'mean: {0}, std {1}'.format(data.mean(), data.std())
            return (data - data.mean()) / data.std()

        def get_outlier_index(cluster):
            """
            gets the index of outliers
            :param cluster: cluster values (y values)  
            :return: index list of outliers
            """
            index_list = []
            cluster_norm = norm(cluster)
            for index, item in enumerate(cluster_norm):
                # item in std
                if abs(item) > 1.5:
                    index_list.append(index)
            return index_list

        def remove_outliers(cluster, index_list):
            """
            :param cluster: list of x, list of y values
            :param index_list: indices of values to delete
            :return: cluster without outliers
            """
            cluster_out = []
            for data in cluster:
                data_out = np.delete(data, index_list)
                cluster_out.append(data_out)
            return cluster_out

        def clean_data(cluster, num_it):
            """
            :param cluster: list of x, list of y values
            :num_it: number of iterations
            :return: cleaned cluster with outliers removed
            """
            for i in range(0, num_it):
                index_list = get_outlier_index(cluster[1])
                cluster_clean = remove_outliers(cluster, index_list)
                cluster = cluster_clean
            return cluster

        cluster = [cluster1, cluster2]
        for elem in cluster:
            data = clean_data(elem, 10)
            if elem == cluster1:
                cluster1_clean_x = data[0]
                cluster1_clean_y = data[1]
            else:
                cluster2_clean_x = data[0]
                cluster2_clean_y = data[1]
        return [cluster1_clean_x, cluster1_clean_y], [cluster2_clean_x, cluster2_clean_y]

    def get_half_maximum(self, y1, y2):
        """    
        :param y1,y2: y values of two plateau regions  
        :return: half maximum 
        """
        y1, y2 = np.array(y1), np.array(y2)
        return np.abs(y1.mean() + y2.mean()) / 2.0

    def get_fwhm(self, x, y, c1, c2, hm):
        """
        rearranges the data from c1 and c2 and calculates the full width at half max
        :param x, y: raw line coords  
        :param c1,c2: plateau region of the clusters  
        :param hm: half max
        :return: fwhm, x,y values to plot fwhm
        """
        x_c = np.concatenate((np.array(c1[0]), np.array(c2[0])))
        y_c = np.concatenate((np.array(c1[1]), np.array(c2[1])))
        set_x_c = set(x_c)
        set_y_c = set(y_c)
        # get the outliers from the clusters including the edge
        diff_x = [value for value in x if value not in set_x_c]
        diff_y = [value for value in y if value not in set_y_c]

        def sort_and_split(x, y):
            """
            :param x: x values
            :param y: y values
            :return: sorted and splitted (by half) points, first left(x,y), then right(x,y)
            """
            x_y_sorted = sorted(zip(x, y), key=itemgetter(0))
            mid = int(len(x_y_sorted) / 2.0)
            x_y_sorted_left = x_y_sorted[0:mid - 1]
            x_y_sorted_right = x_y_sorted[mid:len(x_y_sorted) - 1]
            return map(list, zip(*x_y_sorted_left)), map(list, zip(*x_y_sorted_right))
        # sort and split the points removed by remove_outliers
        points = sort_and_split(diff_x, diff_y)
        x_left, y_left, x_right, y_right = points[0][0], points[0][1], points[1][0],points[1][1]
        f_left = interp1d(y_left, x_left, kind='linear')
        f_right = interp1d(y_right, x_right, kind='linear')
        fwhm = abs(f_left(hm)-f_right(hm))
        return fwhm,[f_left(hm),f_right(hm)],[hm,hm]