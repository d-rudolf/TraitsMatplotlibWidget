import numpy as np
from scipy.interpolate import griddata
from scipy.interpolate import RectBivariateSpline
from scipy.interpolate import interp2d
from scipy.optimize import curve_fit
from scipy.special import erf

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
