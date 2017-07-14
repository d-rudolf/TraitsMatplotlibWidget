from mathtools import MathUtil
from PIL import Image
import numpy as np
import re
import matplotlib.pyplot as plt

class Model(object):
    def __init__(self):
        print('Init in {0}.'.format(__name__))
        self.x1, self.x2, self.y1, self.y2 = 0, 0, 0, 0
        self.image = []
        self.MU = MathUtil()
        self.x_vec = []
        self.line = []
        self.param = []
        self.line_fitted = []
        self.x_10 = 0
        self.x_90 = 0

    def interpol(self):
        """
        interpolates the line
        :return: x vector and line
        """
        x,y = self.MU.get_line_func(self.x1, self.x2, self.y1, self.y2)
        self.line = self.MU.interpolate(self.image, x, y)
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

    def get_10_90(self):
        """
        calculates the x values for y = 0.1 and y = 0.9,
        important: use pixel values fo x
        :return: x_10 and x_90
        """
        def get_y_target():
            """
            calculates the y_10 and y_90 target values from x_vec and line
            :return: y_10, y_90, and the y error from the plateau region
            """
            c1, c2 = self.MU.get_cluster(self.x_vec, self.line)
            cc1, cc2 = self.MU.get_plateaus(c1, c2)
            y1, y2 = cc1[1].mean(), cc2[1].mean()
            y_err = cc1[1].std()
            y_diff = y2 - y1
            return y1 + 0.1 * y_diff, y1 + 0.9 * y_diff, y_err

        def get_x_target(x, y, y_t, y_std):
            """
            calculates x_10 and x_90 values 
            param y_t: target y value 
            param y_std: y error from clusters
            :return: x_10, x_90 values
            """
            diff = np.abs(y - y_t)
            #print ('y: {0}, y_t: {1}'.format(y, y_t))
            if np.abs(np.min(diff)) < y_std:
               # print ('The minimum is: {0:.3f}'.format(np.min(diff)))
                arg = np.argmin(diff)
                print ('The y value is: {0:.3f}'.format(y[arg]))
                return x[arg]
            else:
                print('Deviation from y_t too large.')

        c1,c2 = self.MU.get_cluster(self.x_vec, self.line)
        cc1, cc2 = self.MU.get_plateaus(c1,c2)
        # this is to confine the data around the edge
        start = int(np.argmax(cc1[0]))
        # TODO: replace 200 by a variable
        end = start+200
        print ('start: {0}, end: {1}'.format(start, end))
        y_10, y_90, y_std = get_y_target()
       # print ('y_10: {0}, y_90: {1}, y_std: {2}'.format(y_10, y_90, y_std))
       # print('line: {0}'.format(self.line[start:end]))
        self.x_10 = get_x_target(self.x_vec[start:end], self.line[start:end], y_10, y_std)
        self.x_90 = get_x_target(self.x_vec[start:end], self.line[start:end], y_90, y_std)

    def main_loop(self, x1, x2, y1, y2, current_image, num_lines):
        """
        main loop to interpolate the shifted lines and to fit the average
        :param x1: pos x1
        :param x2: pos x2
        :param y1: pos y1
        :param y2: pos y2
        :param current_image: 
        :param num_lines: number of neighbouring lines for averaging
        """
        lines = []
        self.x1, self.x2, self.y1, self.y2 = x1, x2, y1, y2
        self.image = current_image
        n1, n2 = self.MU.get_normal(self.x1, self.x2, self.y1, self.y2)
        for num in range(num_lines):
            print 'Interpolation number {}.'.format(num)
            self.interpol()
            lines.append(self.line)
            self.x1 = self.x1 + n1
            self.x2 = self.x2 + n1
            self.y1 = self.y1 + n2
            self.y2 = self.y2 + n2
        #self.line = np.array(lines).mean(axis = 0)
        self.line = np.array(lines).sum(axis = 0)
        self.fit()
#        self.get_10_90()

class AutomatizeModel(Model):

    def __init__(self):
        print('Init in {0}.'.format(__name__))
        super(AutomatizeModel, self).__init__()
        self.volt = ''
        self.freq = ''
        self.sigma = 0
        self.sigma_err = 0
        self.data = {'1000': {}, '1500': {}, '2000': {}, '2500': {}}


    def loop(self, x1, x2, y1, y2, files, num_lines):
        """
        loops through the tif files, interpolates and fits        
        :param x1: 
        :param x2: 
        :param y1: 
        :param y2: 
        :param files: 
        """
        for filename in files:
           if self.get_file_info(filename) is not None:
               self.volt, self.freq = self.get_file_info(filename)
               self.image = self.read_tif_image(filename)
               self.main_loop(x1, x2, y1, y2, self.image, num_lines)
               # factor 2.56 for the 10/90 criterion
               if self.param:
                    self.sigma, self.sigma_err = 2.56 * self.param[0][1], 2.56 * self.param[1][1][1]
               #print (self.sigma, self.sigma_err)
               self.store()
               print (self.data)

    def read_tif_image(self,fname):
        """read image with filename as np array"""
        img = Image.open(fname)
        # positive values correspond to counterclockwise rotation
        img_r = img.rotate(0)
        width = img_r.size[0]
        height = img_r.size[1]
        return np.array(img_r.getdata()).reshape(height,width)

    def get_file_info(self, path):
        """
        finds the voltage and frequency values from filenames, 
        uses regular expression matching 
        :param path: full path to the tif file
        :return: voltage and frequency string
        """
        filename = path.split('\\')[-1]
        volt_str = ''
        freq_str = ''
        volt_pattern = re.compile('([\d,-]{1,3})(?=kV)')
        freq_pattern = re.compile('([\d]{4})(?=Hz)')
        found_volt_pattern = volt_pattern.search(filename)
        found_freq_pattern = freq_pattern.search(filename)
        if found_volt_pattern:
            volt_str = found_volt_pattern.group()
            volt_str_list = volt_str.split('-')
            if len(volt_str_list) < 2:
                volt_str = volt_str_list[0]+'.'+'0'
            else:
                volt_str = volt_str_list[0]+'.'+volt_str_list[1]
        if found_freq_pattern:
            freq_str = found_freq_pattern.group()
        if volt_str != '' and freq_str != '':
            return volt_str, freq_str

    def store(self):
        self.data[self.freq][self.volt] = (self.sigma, self.sigma_err)

    def plot(self):
        plt.figure(3)
        for freq in self.data:
            volt_list = []
            sigma_list = []
            sigma_err_list = []
            for volt, value in self.data[freq].iteritems():
                volt_list.append(float(volt))
                sigma_list.append(value[0])
                sigma_err_list.append(value[1])
            ax = plt.gca()
            ax.errorbar(volt_list, sigma_list, sigma_err_list, label = freq, fmt = 'o')
        plt.xlabel('voltage (kV)')
        plt.ylabel('sigma 90/10 (pixel)')
        plt.legend()
        plt.show()
        
if __name__ == '__main__':

    fname = '../data/021_BiTe_EUV_2kV_2500Hz_001.tif'

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