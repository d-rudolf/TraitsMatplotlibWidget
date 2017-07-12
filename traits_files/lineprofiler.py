
from traits_mpl_widget import BasicFigure, WidgetFigure
from traits.api import HasTraits, List, Enum, Directory, Instance, Array, Str, Bool, Float, Int, Button, on_trait_change
from traitsui.api import View, HGroup, VGroup, VSplit, Item, UItem, spring

from model import Model, AutomatizeModel
from PIL import Image
import glob
import numpy as np
from scipy.ndimage.interpolation import rotate
import pickle as pkl

class reader(HasTraits):

    #dir = Directory(r'D:\Users\D.Rudolf-Lvovsky\Denis\Juelich-2017\Data\PEEM_space_charge')
    dir = Directory('../data')
    path = '../data/*.TIF'
    files = List
    files_sel = Enum(values='files')
    current_image = Array()
    angle = Float(6.08, label = 'angle', desc = 'image rotation angle')

    def _files_default(self):
        files = glob.glob(self.path)
        return files

    def _dir_changed(self):
        self.files = glob.glob(self.path)

    def _files_sel_changed(self):
        print ('Angle changed to {0:.3f}.'.format(self.angle))
        img = Image.open(self.files_sel)
        w, h = img.size[0], img.size[1]
        current_image = np.array(img.getdata()).reshape(h,w)
        self.current_image = rotate(current_image, self.angle)


class viewer(reader):

    line_list_ = List()
    line_sel = Enum(values='line_list_')
    fig = Instance(WidgetFigure)
    fig_profile = Instance(BasicFigure)
    Mod = Instance(Model)
    AutMod = Instance(AutomatizeModel)
    fit = Str(label='Fit', desc = 'Fit result')
    result_10_90 = Str(label = '10/90', desc = '10/90 result')
    analyze_button = Button('All data')
    num_lines = Int (5, label = 'Number of lines to average')


    @on_trait_change('fig.drawn_lines')
    def update_line_list(self, obj):
        self.line_list_ = self.fig.drawn_lines_names
        if self.line_sel:
            self.line_sel = self.fig.drawn_lines_names[0]

    @on_trait_change('current_image')
    def plot_fig(self):
        self.fig.imshow(self.current_image, origin = 'lower')
        #pkl.dump(self.current_image, open('test_image.p', 'wb'))

    def _fig_default(self):
       fig = WidgetFigure()
       return fig

    def _fig_profile_default(self):
       fig_profile = BasicFigure()
       return fig_profile

    def _Mod_default(self):
        Mod = Model()
        return Mod

    def _AutMod_default(self):
        AutMod = AutomatizeModel()
        return AutMod

    @on_trait_change('line_sel, fig:drawn_lines:lineReleased, num_lines')
    def plot_line_fit(self):
        """
        plots the line profile, the error function fit and the vertical lines for the 10%/90% criterion
        """
        x, y = self.fig.get_widget_line(self.line_sel).line.get_data()
        print x,y
        self.x1,self.x2 = x[0], x[1]
        self.y1,self.y2 = y[0], y[1]
        self.Mod.main_loop(self.x1, self.x2, self.y1, self.y2, self.current_image, self.num_lines)
        x_vec, line = self.Mod.x_vec, self.Mod.line
        #pkl.dump(line, open('test_line.p','wb'))
        line_fitted, param = self.Mod.line_fitted, self. Mod.param
        x_10, x_90 = self.Mod.x_10, self.Mod.x_90
        self.fig_profile.plot(x_vec, line, label = 'Line', color = 'blue', marker = '.')
        self.fig_profile.plot(x_vec, line_fitted, label='Fit',
                              #text = 'fit: {0:.2f} +/- {1:.2f}'.format(2.56*param[0][1],
                                                                     #2.56*param[1][1][1]),
                              pos = (0.1, 0.5),
                              color = 'red', linewidth=2)
        self.fig_profile.plot([x_10, x_10], [np.min(line), np.max(line)], label = 'Vl1', color = 'black', linewidth = 2)
        self.fig_profile.plot([x_90, x_90], [np.min(line), np.max(line)], label='Vl2',
                              #text = '90/10: {0:.2f}'.format(abs(x_90-x_10)),
                              pos = (0.1, 0.4),
                              color = 'black', linewidth = 2)
        self.fit = '{0:.2f} +/- {1:.2f}'.format(2.56*param[0][1],2.56*param[1][1][1])
        try:
            self.result_10_90 = '{0:.2f}'.format(abs(x_90-x_10))
        except (TypeError):
            pass

    def _analyze_button_fired(self):
        """
        analyzes lineprofiles in all data files
        """
        self.AutMod.loop(self.x1, self.x2, self.y1, self.y2,self.files, self.num_lines)
        self.AutMod.plot()

    @on_trait_change('angle')
    def change_angle(self):
        """
        Calculation of the default angle value
        >>> import numpy as np
        >>> x1 = 359
        >>> y1 = 31
        >>> x2 = 320
        >>> y2 = 397
        >>> vec_line = -np.array([x1,y1])+np.array([x2,y2]) 
        >>> vec_y = np.array([0,1])
        >>> value = np.inner(vec_line,vec_y)/(np.linalg.norm(vec_line)*np.linalg.norm(vec_y))))
        >>> np.arccos(value)/np.pi*180
        6.0823366932820901
        """
        self.current_image = rotate(self.current_image, self.angle)

    def traits_view(self):
        view = View(
            HGroup(
                HGroup(
                    VGroup(
                        UItem('fig', style='custom'),
                        UItem('fig_profile', style='custom'),
                    ),
                     VGroup(
                        Item('angle'),
                        Item('num_lines'),
                        spring,
                        spring,
                        Item('line_sel', label='Select line cut'),
                        spring,

                        VGroup(
                            Item('fit', style = 'readonly', padding = 15),
                            Item('result_10_90', style = 'readonly', padding = 15),
                            Item('analyze_button', show_label = False),
                            spring,
                            #label = 'Data analysis',
                        ),

                    ),
                layout = 'split'
                ),
                VGroup(
                    #spring,
                    Item('dir', style='custom', label = 'Dir'),
                    Item('files_sel', label ='Select files:'),
                    #spring,
                    show_border = True,
                ),
            layout='normal'
            ),
            resizable=True,
            height=900
        )
        return view

if __name__ == '__main__':
    r = viewer()
    r.configure_traits()



































