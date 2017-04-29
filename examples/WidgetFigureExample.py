from __future__ import print_function, division

from TraitsMPLWidget import WidgetFigure, BasicFigure

from traits.api import HasTraits, Instance, Array, on_trait_change, List, Enum
from traitsui.api import View, UItem, HGroup, VGroup, Item
import numpy as np

class WidgetFigureExample(HasTraits):
    fig = Instance(WidgetFigure)
    zoom_fig = Instance(BasicFigure)
    line_fig = Instance(BasicFigure)

    line_list_ = List()
    line_sel = Enum(values='line_list_')

    patches_list_ = List()
    patches_sel = Enum(values='patches_list_')

    data = Array

    @on_trait_change('fig.drawn_lines')
    def update_line_list(self,obj):
        self.line_list_ = self.fig.drawn_lines_names
        if self.line_sel:
            self.line_sel = self.fig.drawn_lines_names[0]

    @on_trait_change('fig.drawn_patches')
    def update_patches_list(self):
        print('Here')
        self.patches_list_ = self.fig.drawn_patches_names
        if self.patches_sel:
            self.patches_sel = self.fig.drawn_patches_names[0]

    @on_trait_change('line_sel, fig:drawn_lines:lineReleased')
    def plt_line_cut(self):
        print('update selector',self.line_sel)
        x,y = self.fig.get_widget_line(self.line_sel).line.get_data()

        len_x = abs(x[1] - x[0])
        len_y = abs(y[1] - y[0])
        len_line = np.sqrt(len_x ** 2 + len_y ** 2)
        x = np.linspace(x[0], x[1], len_line)
        y = np.linspace(y[0], y[1], len_line)
        x, y = x.astype(np.int), y.astype(np.int)

        line_cut = np.array(self.data[y,x])
        self.line_fig.plot(range(0,line_cut.shape[0]),line_cut,label='_no_legend')


    @on_trait_change('patches_sel, fig:drawn_patches:rectUpdated')
    def calculate_picture_region_sum(self):
        p = self.fig.get_widget_patch(self.patches_sel)
        x1, y1 = p.rectangle.get_xy()
        x2 = x1 + p.rectangle.get_width()
        y2 = y1 + p.rectangle.get_height()

        if p.rectangle.get_width() < 0:
            x2, x1 = x1, x2
        if p.rectangle.get_height() < 0:
            y2, y1 = y1, y2
        if p.rectangle.get_width()==0 or p.rectangle.get_height()==0:
            print('Zero Patch dimension')

        zoomdata = self.data[int(y1):int(y2),int(x1):int(x2)]

        self.zoom_fig.imshow(zoomdata, extent=[int(x1),int(x2),int(y1),int(y2)])

    def _fig_default(self):
        w = WidgetFigure(facecolor='w')
        w.imshow(self.data)
        return w

    def _zoom_fig_default(self):
        w = BasicFigure(facecolor='w')
        return w

    def _line_fig_default(self):
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
            VGroup(
                HGroup(
                    UItem('fig', style='custom'),
                    UItem('zoom_fig', style='custom'),
                    Item('patches_sel',label='Select patches'),
                ),
                HGroup(
                    UItem('line_fig',style='custom'),
                    Item('line_sel',label='Select line cut'),
                ),
            ),
        )
        return view



if __name__ == '__main__':
    basic_figure_test = WidgetFigureExample()
    basic_figure_test.configure_traits()