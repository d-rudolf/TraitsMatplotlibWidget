from mathtools import MathUtil
from PIL import Image
import numpy as np


class Model:
    def __init__(self):
        self.MU = MathUtil()
        self.x_vec = []
        self.line = []
        self.param = []
        self.line_fitted = []

    def interpol(self, x1, x2, y1, y2, current_image):
        """
        :param x1: 
        :param x2: 
        :param y1: 
        :param y2: 
        :param current_image: 
        :return: x vector and line
        """
        x,y = self.MU.get_line_func(x1,x2,y1,y2)
        self.line = self.MU.interpolate(current_image, x,y)
        self.x_vec = self.MU.get_dist_vec(x,y)
        #self.fig_profile.plot(x_vec,line, label = 'Line', color = 'blue', marker = '.')

    def fit(self):
        """
        :param x_vec: 
        :param line: 
        :return: parameters of the fit and the fitted line 
        """
        self.param = self.MU.fit_func(self.x_vec,self.line, 7e3,10,25,1e3)
        self.line_fitted = self.MU.func(self.x_vec, self.param[0][0],self.param[0][1], self.param[0][2], self.param[0][3])
        #self.fig_profile.plot(x_vec,line_fitted,label = 'Fit', text ='sigma: {0:.2f} +/- {1:.2f}'.format(param[0][1],param[1][1][1]),pos = (0.1,0.5), color = 'red', linewidth = 2)


if __name__ == '__main__':

    fname = 'D://Users//D.Rudolf-Lvovsky//Denis//Juelich-2017//Data//PEEM_space_charge//021_BiTe_EUV_2kV_2500Hz_001.tif'

    def read_tif_image(fname):
        """read image with filename as np array"""
        img = Image.open(fname)
        # positive values correspond to counterclockwise rotation
        img_r = img.rotate(0)
        width = img_r.size[0]
        height = img_r.size[1]
        return np.array(img_r.getdata()).reshape(height,width)

    image = read_tif_image(fname)
    x1, y1 = 0, 0
    x2, y2 = np.shape(image)[1], np.shape(image)[0]

    print(x1,x2)

    Mod = Model()
    Mod.interpol(x1, x2, y1, y2, image)
    x_vec, line = Mod.x_vec, Mod.line
    Mod.fit()