from __future__ import print_function, division

import numpy as np

from TraitsMPLWidget import BasicFigure, MPLFigureEditor, MPLInitHandler
from traits.api import Range, Button, List, Int
from traitsui.api import View, UItem, Item, Include, HGroup


class BasicFigureExample(BasicFigure):
    ### TEST FUNCTIONS ###
    t = Range(0,100,1)
    def _t_changed(self):
        import numpy as np
        x = np.linspace(0., 2 * np.pi, np.random.randint(5, 500))
        y = np.sin(x * self.t)
        y2 = np.cos(x * self.t)
        # self.grid = True
        self.plot(x, y / 10, fmt='o-', linestyle='dashed', label='sin')
        if np.random.uniform() < 0.5:
            self.plot(x, y2 / 10, fmt='o', label='cos 1')
            self.plot(x, y2 / 5., fmt='o', label='cos 2')
            self.plot(x, y2 / 8., fmt='o', label='cos 3')

    tblit = Range(0,100,1)
    def _tblit_changed(self):
        import numpy as np
        x = np.linspace(0., 2 * np.pi, np.random.randint(5, 500))
        y = np.sin(x * self.tblit)
        y2 = np.cos(x * self.tblit)
        # self.grid = True
        self.blit(x, y / 10, fmt='o-', linestyle='dashed', label='sin')
        if np.random.uniform() < 0.5:
            self.blit(x, y2 / 10, fmt='o', label='cos 1')
            self.blit(x, y2 / 5., fmt='o', label='cos 2')
            self.blit(x, y2 / 8., fmt='o', label='cos 3')

    timg = Range(0,20,1)
    def _timg_changed(self):
        nData = np.random.randint(5, 500)
        x = np.linspace(-10, np.random.randint(5,15), nData)
        y = np.linspace(-10, np.random.randint(5,15), nData)
        X, Y = np.meshgrid(x, y)
        Z = (np.sin(X * self.timg) ** 2 + np.cos(Y) ** 2 * X ** 2 * np.random.random())
        self.imshow(Z, extent=[x.min(), x.max(), y.min(), y.max()])

    def test_traits_view(self):
        trait_view = View(
            UItem('figure', editor=MPLFigureEditor(), style='custom'),
            Include('options_group'),
            Item('t'),
            Item('tblit'),
            Item('timg'),
            handler=MPLInitHandler,
            resizable=True,
            # scrollable=True,
        )
        return trait_view


if __name__ == '__main__':
    basic_figure_test = BasicFigureExample(figsize=(6 * 1.618, 6), facecolor='w', tight_layout=True)
    basic_figure_test.configure_traits(view='test_traits_view')