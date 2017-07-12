import unittest
import numpy as np
import sys
sys.path.append('../traits_files/')
from model import Model
import pickle as pkl

class LineprofilerTest(unittest.TestCase):
    def setUp(self):
        self.image = pkl.load(open('./test_image.p','rb'))
        self.line = pkl.load(open('./test_line.p','rb'))
        self.x1, self.x2, self.y1, self.y2 = 200., 200., 1., 500.

        self.test_edge_x = pkl.load(open('./test_edge_x.p','rb'))
        self.test_edge_y = pkl.load(open('./test_edge_y.p','rb'))
        self.test_edge_fit = pkl.load(open('./test_edge_fit.p','rb'))
        self.x_10, self.x_90 = pkl.load(open('./test_edge_x10_x90.p', 'rb'))

    def test_interpolation(self):
        model = Model()
        model.interpol(self.x1, self.x2, self.y1, self.y2, self.image)
        #print (model.line-self.line)
        np.testing.assert_array_almost_equal(self.line, model.line, decimal=6)

    def test_fit(self):
        model = Model()
        model.x_vec = self.test_edge_x
        model.line = self.test_edge_y
        model.fit()
        np.testing.assert_array_almost_equal(self.test_edge_fit, model.line_fitted)

    def test_10_90(self):
        model = Model()
        model.x_vec = self.test_edge_x
        model.line = self.test_edge_y
        np.testing.assert_array_almost_equal((self.x_10, self.x_90),model.get_10_90())

if __name__ == '__main__':
     unittest.main(verbosity = 2)
