
from TraitsMPLWidget import BasicFigure
from ThreadedHasTraits import tHasTraits as ThreadedHasTraits
from traits.api import List, Enum, Directory, Instance, Array, Str, Bool, Float, on_trait_change
from traitsui.api import View, HGroup, VGroup, Item, UItem

from MathTools import Math_Util

import numpy as np
import ImgRW as Im
import glob
from scipy.special import erf


class reader(ThreadedHasTraits):

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
    fig = Instance(BasicFigure)
    fig_profile = Instance(BasicFigure)
    MU = Instance(Math_Util)

    @on_trait_change('current_image')
    def plot_fig(self):
        self.fig.imshow(self.current_image)

    def _fig_default(self):
       fig = BasicFigure()
       return fig

    def _fig_profile_default(self):
       fig_profile = BasicFigure()
       return fig_profile

    # Math utility class instance
    def _MU_default(self):
       MU = Math_Util()
       return MU

    @on_trait_change('fig.y_second')
    def plot_line(self):
        x1 = self.fig.x_first
        x2 = self.fig.x_second
        y1 = self.fig.y_first
        y2 = self.fig.y_second

        x,y = self.MU.get_line_func(x1,x2,y1,y2)
        line = self.MU.interpolate(self.current_image, x,y)
        x_vec = self.MU.get_dist_vec(x,y)
        self.fig_profile.plot(x_vec,line, label = 'Line', color = 'blue', marker = '.')

        param = self.MU.fit_func(x_vec,line, 7e3,10,25,1e3)
        line_fitted = self.MU.func(x_vec, param[0][0],param[0][1], param[0][2], param[0][3])

        self.fig_profile.plot(x_vec,line_fitted,label = 'Fit', text ='sigma: {0:.2f} +/- {1:.2f}'.format(param[0][1],param[1][1][1]),pos = (0.1,0.5), color = 'red', linewidth = 2)

    def traits_view(self):
        view = View(
            HGroup(
                VGroup(
                    UItem('fig', style='custom'),
                    UItem('fig_profile', style='custom'),
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



































