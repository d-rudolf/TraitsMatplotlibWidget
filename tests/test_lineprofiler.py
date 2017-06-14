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
        self.x1, self.x2, self.y1, self.y2 = 69.7307199316, 455.332087161, 80.4446254072, 232.7247557
      #  self.x1, self.x2, self.y1, self.y2 = 0,0,0,0

    def test_interpolation(self):
        model = Model()
        model.interpol(self.x1, self.x2, self.y1, self.y2, self.image)
        print (model.line-self.line)
        np.testing.assert_array_almost_equal(self.line, model.line, decimal=6)

if __name__ == '__main__':
     unittest.main()