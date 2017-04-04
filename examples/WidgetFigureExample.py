from __future__ import print_function, division

from TraitsMPLWidget import WidgetFigure, BasicFigure

from traits.api import HasTraits, Instance, Array, on_trait_change, Range, Button, List, Int
from traitsui.api import View, UItem, Item, Include, HGroup
from scipy.stats import poisson
import numpy as np

class WidgetFigureExample(HasTraits):
    fig = Instance(WidgetFigure)
    zoomfig = Instance(BasicFigure)

    data = Array

    @on_trait_change('fig:selectionPatches:rectUpdated')
    def calculate_picture_region_sum(self, new):
        for i, p in enumerate(self.fig.selectionPatches):
            x1, y1 = p.rectangle.get_xy()
            x2 = x1 + p.rectangle.get_width()
            y2 = y1 + p.rectangle.get_height()
            # print("x2, x1 = ", x2, x1)
            # print("y2, y2 = ", y2, y1)
            zoomdata = self.data[y1:y2,x1:x2]

        self.zoomfig.imshow(zoomdata, extent=[int(x1),int(x2),int(y1),int(y2)])

    def _fig_default(self):
        w = WidgetFigure(facecolor='w')
        w.imshow(self.data)
        return w

    def _zoomfig_default(self):
        w = BasicFigure(facecolor='w')
        return w

    def _data_default(self):
        x = np.linspace(-.5,1.,500)
        y = np.linspace(-.5,1.,500)

        XX,YY = np.meshgrid(x,y)

        data = np.exp(-((XX-0.5)**2+YY**2)/(2.0*(0.5/(2*np.sqrt(2*np.log(2))))**2))
        return data

    def plot_data(self):
        self.fig.imshow(self.data, origin='lower')

    def traits_view(self):
        view = View(
            HGroup(
                UItem('fig', style='custom'),
                UItem('zoomfig', style='custom'),
            ),
        )
        return view



if __name__ == '__main__':
    basic_figure_test = WidgetFigureExample()
    basic_figure_test.configure_traits()