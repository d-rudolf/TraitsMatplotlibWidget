
from traits_mpl_widget import BasicFigure, WidgetFigure
from traits.api import HasTraits, List, Enum, Directory, Instance, Array, Str, Bool, Float, on_trait_change
from traitsui.api import View, HGroup, VGroup, Item, UItem

from model import Model
import img_rw as Im
import glob

import pickle as pkl

class reader(HasTraits):

    dir = Directory('D://Users//D.Rudolf-Lvovsky//Denis//Juelich-2017//Data//PEEM_space_charge//')
    files = List
    files_sel = Enum(values='files')
    current_image = Array

    def _files_default(self):
        files = glob.glob(self.dir + '/*.TI*')
        return files

    def _dir_changed(self):
        self.files = glob.glob(self.dir + '/*.TI*')


    def _files_sel_changed(self):
        print self.files_sel
        self.current_image = Im.read_tif_image(self.files_sel)


class viewer(reader):

    line_list_ = List()
    line_sel = Enum(values='line_list_')
    fig = Instance(WidgetFigure)
    fig_profile = Instance(BasicFigure)
    Mod = Instance(Model)

    @on_trait_change('fig.drawn_lines')
    def update_line_list(self, obj):
        self.line_list_ = self.fig.drawn_lines_names
        if self.line_sel:
            self.line_sel = self.fig.drawn_lines_names[0]

    @on_trait_change('current_image')
    def plot_fig(self):
        self.fig.imshow(self.current_image)
        pkl.dump(self.current_image, open('test_image.p', 'wb'))
    def _fig_default(self):
       fig = WidgetFigure()
       return fig

    def _fig_profile_default(self):
       fig_profile = BasicFigure()
       return fig_profile

    def _Mod_default(self):
        Mod = Model()
        return Mod

    @on_trait_change('line_sel, fig:drawn_lines:lineReleased')
    def plot_line(self):
        x, y = self.fig.get_widget_line(self.line_sel).line.get_data()
        print x,y
        x1,x2 = x[0], x[1]
        y1,y2 = y[0], y[1]
        self.Mod.interpol(x1, x2, y1, y2, self.current_image)
        x_vec, line = self.Mod.x_vec, self.Mod.line
        pkl.dump(line, open('test_line.p','wb'))
        self.Mod.fit()
        line_fitted, param = self.Mod.line_fitted, self. Mod.param
        self.fig_profile.plot(x_vec, line, label = 'Line', color = 'blue', marker = '.')
        self.fig_profile.plot(x_vec, line_fitted, label='Fit',
                              #text='sigma: {0:.2f} +/- {1:.2f}'.format(param[0][1],
                              #param[1][1][1]),
                             # pos=(0.1, 0.5),
                              color='red', linewidth=2)

        #x,y = self.MU.get_line_func(x1,x2,y1,y2)
        #line = self.MU.interpolate(self.current_image, x,y)
        #x_vec = self.MU.get_dist_vec(x,y)
        #self.fig_profile.plot(x_vec,line, label = 'Line', color = 'blue', marker = '.')
#
        #param = self.MU.fit_func(x_vec,line, 7e3,10,25,1e3)
        #line_fitted = self.MU.func(x_vec, param[0][0],param[0][1], param[0][2], param[0][3])


    def traits_view(self):
        view = View(
            HGroup(
                VGroup(
                    UItem('fig', style='custom'),
                    UItem('fig_profile', style='custom'),
                    Item('line_sel', label='Select line cut'),
                ),
                VGroup(
                    UItem('files_sel'),
                    UItem('dir', style='custom'),
                    show_border=True,
                ),
            ),
            HGroup(),
            resizable=True,
            height=900


        )
        return view

if __name__ == '__main__':
    r = viewer()
    r.configure_traits()



































