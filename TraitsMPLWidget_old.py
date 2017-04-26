from __future__ import division, print_function

from traits.etsconfig.api import ETSConfig
# ETSConfig.toolkit = 'qt4'

from pyface.qt import QtGui, QtCore

try:
    import win32clipboard
    print("Using win32clipboard")
except:
    import pyperclip
    print("Using Linux clipboard")

import matplotlib as mpl
import matplotlib.pyplot as plt
# mpl.use('Qt4Agg')
# mpl.rcParams['backend.qt4'] = 'PyQt4v2'


import numpy as np


from traitsui.qt4.editor import Editor
from traitsui.qt4.basic_editor_factory import BasicEditorFactory
from traits.api import Instance, HasTraits, Int, Str, Float, List, Array, Bool, Tuple, Button, Dict, Enum, Range, on_trait_change
from traitsui.api import Handler, View, Item, UItem, CheckListEditor, HGroup, VGroup, Include
from pyface.api import FileDialog, OK
from collections import OrderedDict

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.colors import LogNorm
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT
from matplotlib.container import ErrorbarContainer

import cPickle, wx

__author__ = 'd.wilson'

app = wx.App(False)
DISPLAY_SIZE = wx.GetDisplaySize()
DISPLAY_DPI = wx.ScreenDC().GetPPI()


class _ScrollableMPLFigureEditor(Editor):
    scrollable = True
    canvas = Instance(FigureCanvas)
    toolbar = Instance(NavigationToolbar2QT)

    def init(self, parent):
        self.control = self._create_canvas(parent)
        self.set_tooltip()

    def update_editor(self):
        pass

    def _create_canvas(self, parent):
        print("_MPLFigureEditor: Creating canvas (_create_canvas)")
        frame_canvas = QtGui.QWidget()

        scrollarea = QtGui.QScrollArea()
        mpl_canvas = FigureCanvas(self.value)
        mpl_canvas.setParent(scrollarea)
        scrollarea.setWidget(mpl_canvas)


        mpl_toolbar = NavigationToolbar2QT(mpl_canvas, frame_canvas)
        # mpl_toolbar.setIconSize(QtCore.QSize(30, 30))

        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(scrollarea)
        vbox.addWidget(mpl_toolbar)
        vbox.setGeometry(QtCore.QRect(0, 0, 1000, 1000))
        frame_canvas.setLayout(vbox)
        return frame_canvas

class _MPLFigureEditor(Editor):
    scrollable = True
    canvas = Instance(FigureCanvas)
    toolbar = Instance(NavigationToolbar2QT)

    def init(self, parent):
        self.control = self._create_canvas(parent)
        self.set_tooltip()

    def update_editor(self):
        pass

    def _create_canvas(self, parent):
        print("_MPLFigureEditor: Creating canvas (_create_canvas)")
        # matplotlib commands to create a canvas
        frame = QtGui.QWidget()
        mpl_canvas = FigureCanvas(self.value)
        mpl_canvas.setParent(frame)
        mpl_toolbar = NavigationToolbar2QT(mpl_canvas, frame)

        # mpl_toolbar.setIconSize(QtCore.QSize(30, 30))

        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(mpl_canvas)
        vbox.addWidget(mpl_toolbar)
        frame.setLayout(vbox)

        return frame

class MPLFigureEditor(BasicEditorFactory):
    klass = _MPLFigureEditor

class ScrollableMPLFigureEditor(BasicEditorFactory):
    klass = _ScrollableMPLFigureEditor

class MPLInitHandler(Handler):
    """Handler calls mpl_setup() to initialize mpl events"""
    def init(self, info):
        """
            This method gets called after the controls have all been
            created but before they are displayed.
        """
        # print("MPLInitHandler: info = ", info)
        info.object.mpl_setup()
        return True


class MinimalFigure(HasTraits):
    figure_kwargs = Dict()
    figure = Instance(Figure)
    canvas = Instance(FigureCanvas)
    clickdata = Tuple()

    # some option - more to be added!
    axes = List()
    axes_selector = Enum(values='axes')
    options_btn = Button('options')
    title = Str()
    xlabel = Str()
    ylabel = Str()

    fontsize = Range(0, 30, 12)
    grid = Bool(False)
    autoscale = Bool(True)
    clear_btn = Button('clear')
    lines_list = List()
    line_selector = Enum(values='lines_list')
    copy_data_btn = Button('copy data')
    save_fig_btn = Button('save figure')

    def __init__(self, *args, **kwargs):
        # Figure kwargs: figsize=None, dpi=None, facecolor=None, edgecolor=None, linewidth=0.0, frameon=None, subplotpars=None, tight_layout=None
        super(MinimalFigure, self).__init__()
        self.figure_kwargs = kwargs

    def _figure_default(self):
        print("MinimalFigure: Create figure (_figure_default)")
        fig = Figure(**self.figure_kwargs)
        fig.patch.set_facecolor('w')
        return fig

    @on_trait_change('figure, axes[]')
    def update_lines(self):
        print("MinimalFigure: axes changed! ")
        self.axes = self.figure.get_axes()  # get axes

        # get lines
        lines = []
        for ax in self.figure.get_axes():
            for l in ax.get_lines():
                lines.append(self._replace_line2D_str(l))

        self.lines_list = sorted(lines)

        self._set_axes_property_variables()  # get labels

    def mpl_setup(self):
        print("MinimalFigure: Running mpl_setup - connecting button press events")
        self.canvas = self.figure.canvas  # creates link (same object)
        cid = self.figure.canvas.mpl_connect('button_press_event', self.__onclick)

    def __onclick(self, event):
        if event is None:
            return None
        self.clickdata = (event.button, event.x, event.y, event.xdata, event.ydata)
        print('MinimalFigure: %s' % event)

    def clear(self):
        self._clear_btn_fired()

    def _clear_btn_fired(self):
        if self.img_bool:
            self.img_bool = False
            # self.figure.clear()
            # self.create_axis_if_no_axis()
        else:
            ax = self.figure.get_axes()
            for a in ax:
                print("MinimalFigure: Clearing axis ", a)
                a.clear()

            self.xlabel = ''
            self.ylabel = ''
            self.title = ''
            for ax in self.figure.axes:
                ax.grid(self.grid)
        self.draw_canvas()

    def _replace_line2D_str(self, s):
        s = str(s)
        return s.replace('Line2D(', '').replace(')', '')

    def _is_line_in_axes(self, label):
        """
        :param label: Label of plot
        :return: False if line is not in axes, line if line is in axes
        """
        lines = []
        for ax in self.figure.get_axes():
            for l in ax.get_lines():
                lines.append(self._replace_line2D_str(l))
                if label == self._replace_line2D_str(l):
                    return l

        self.lines_list = sorted(lines)
        return False

    def _copy_data_btn_fired(self):
        # TODO: Add xerr and yerr to copy
        print("MinimalFigure: Trying to copy data to clipboard")
        line = self._is_line_in_axes(self.line_selector)
        x = line.get_xdata()
        y = line.get_ydata()

        text = 'x \t y \n'
        for i in xrange(len(x)):
            text += str(x[i]) + "\t" + str(y[i]) + "\n"

        self.add_to_clip_board(text)

        # x = self._plotlines[self.plotlines_sel].get_xdata()
        # y = self._plotlines[self.plotlines_sel].get_ydata()
        #
        # text = 'x \t y \t x_error \t y_error \n'
        # for i in xrange(len(x)):
        #     text += str(x[i]) + "\t" + str(y[i]) + "\t" + str(self._xerr[self.plotlines_sel][i]) + "\t" + str(self._yerr[self.plotlines_sel][i]) + "\n"
        #
        # self.add_to_clip_board(text)

    def add_to_clip_board(self, text):
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
        except:
            print("MinimalFigure: Could not copy to win32 clipboard. Trying linux version or install win32clipboard ")

        try:
            pyperclip.copy(text)
        except:
            print("MinimalFigure: Could not copy text for linux. Install pyperclip")

    def get_axes(self):
        axes = self.create_axis_if_no_axis()
        return axes

    def create_axis_if_no_axis(self):
        # creates one axis if none created
        axes = self.figure.get_axes()
        if len(axes) == 0:
            self.figure.add_subplot(111)
            axes = self.figure.get_axes()
            self.axes = axes

            self._set_axes_property_variables()
        return axes

    def draw(self):
        if self.autoscale:
            axes = self.figure.get_axes()
            for ax in axes:
                ax.relim()
                ax.autoscale()

        self.draw_canvas()

    def draw_canvas(self):
        try:
            self.canvas.draw_idle()  # Queue redraw of the Agg buffer and request Qt paintEvent (Qt Case) -> SpeedUp
            # self.canvas.draw()
        except AttributeError:
            print("MinimalFigure: Canvas is not ready.")

    def _fontsize_changed(self):
        mpl.rcParams.update({'font.size': self.fontsize})
        self.draw_canvas()

    def _grid_changed(self):
        try:
            self.axes_selector.grid(self.grid)
            self.draw_canvas()
        except AttributeError:
            print("MinimalFigure: Axes not ready")

    @on_trait_change('axes_selector')
    def _set_axes_property_variables(self):
        self.title = self.axes_selector.get_title()
        if self.axes_selector.get_xlabel() != '':
            self.xlabel = self.axes_selector.get_xlabel()

        if self.axes_selector.get_ylabel() != '':
            self.ylabel = self.axes_selector.get_ylabel()

        self.axes_selector.grid(self.grid)

    def _title_changed(self):
        self.create_axis_if_no_axis()
        self.axes_selector.set_title(self.title)
        self.draw_canvas()

    def _xlabel_changed(self):
        self.create_axis_if_no_axis()
        self.axes_selector.set_xlabel(self.xlabel)
        self.draw_canvas()

    def _ylabel_changed(self):
        self.create_axis_if_no_axis()
        self.axes_selector.set_ylabel(self.ylabel)
        self.draw_canvas()

    def _options_btn_fired(self):
        self.edit_traits(view='traits_options_view')

    def _save_fig_btn_fired(self):
        dlg = FileDialog(action='save as')
        if dlg.open() == OK:
            self.savefig(dlg.filename + ".png", dpi=300)
            self.savefig(dlg.filename + ".eps")
            self.savefig(dlg.filename + ".pdf")
            # cPickle.dump(self, open("dlg.filename" + ".pkl", "wb"))

    def savefig(self, *args, **kwargs):
        self.figure.savefig(*args, **kwargs)

    def options_group(self):
        g = HGroup(
            UItem('options_btn'),
            UItem('clear_btn'),
            UItem('line_selector'),
            UItem('copy_data_btn'),
            UItem('save_fig_btn'),
        )
        return g

    def traits_view(self):
        traits_view = View(
            UItem('figure', editor=MPLFigureEditor(), style='custom'),
            Include('options_group'),
            handler=MPLInitHandler,
            resizable=True,
            scrollable=True,
        )
        return traits_view

    def traits_scroll_view(self):
        traits_view = View(
            UItem('figure', editor=ScrollableMPLFigureEditor(), style='custom'),
            Include('options_group'),
            handler=MPLInitHandler,
            resizable=True,
            scrollable=True,
        )
        return traits_view

    def traits_options_view(self):
        traits_options_view = View(
            Item('axes_selector'),
            Item('title'),
            Item('xlabel'),
            Item('ylabel'),
            Item('fontsize'),
            HGroup(
                Item('grid'),
                Item('autoscale'),
            ),
            Item('clickdata', style='readonly'),
            resizable=True,
        )
        return traits_options_view


class BasicFigure(MinimalFigure):
    mask_data_bool = Bool(True)
    mask_length = Int(100000)

    normalize_bool = Bool(False)
    normalize_max = Float()
    normalize_maxes = List()

    log_bool = Bool(False)

    # image stuff
    origin = Str('lower')
    img_bool = Bool(False)
    img_max = Float(1.)
    img_data = Array()
    img_kwargs = Dict
    zlabel = Str()

    vmin_lv, vmin_hv, vmax_lv, vmax_hv = Float(0.), Float(0.), Float(1.), Float(1.)
    vmin = Range('vmin_lv', 'vmin_hv')
    vmax = Range('vmax_lv', 'vmax_hv')
    cmaps = List
    cmap_selector = Enum(values='cmaps')

    image_slider_btn = Button('z-slider')

    x_first = Float()
    x_second = Float()

    y_first = Float()
    y_second = Float()

    def __init__(self, **kwargs):
        super(BasicFigure, self).__init__(**kwargs)
        self.grid = True
        # self.add_trait('x_second', Float)

    def _test_plot_kwargs(self, kwargs):
        if 'fmt' in kwargs:
            fmt = kwargs['fmt']
            del kwargs['fmt']
        else:
            fmt = ''

        if 'label' not in kwargs:
            raise Exception("BasicFigure: Please provide a label for datapoints.")
        else:
            label = kwargs['label']

        if 'text' in kwargs:
            text = kwargs['text']
            del kwargs['text']
        else:
            text = ''
        # position of the text
        if 'pos' in kwargs:
            pos = kwargs['pos']
            del kwargs['pos']
        else:
            pos = (0,0)

        return fmt, label, text, pos

    def _mask_data(self, data):
        # fast when data is not too big (like 70M datapoints, but still works. Never possible with matplotlib)
        if not self.mask_data_bool:
            return data
        else:
            data = np.array(data)
            steps = len(data) / self.mask_length
            masked_data = data[0:-1:int(steps)]
            return masked_data

    def _zlabel_changed(self):
        if self.img_bool:
            self.cb.set_label(self.zlabel)
            self.draw()

    def _cmap_selector_changed(self):
        if self.img_bool:
            self.img.set_cmap(self.cmap_selector)
            self.draw()

    def _cmaps_default(self):
        print(self.__class__.__name__, ": Initiating colormaps")
        cmaps = sorted(m for m in mpl._cm.datad)
        return cmaps

    def _normalize_bool_changed(self, old=None, new=None):
        # Function is a little bit long since it handles normalization completly by itself
        # Maybe there is a better way, but it's working and i do not have time to think about a better one
        # Not completly working in my real programmes, since activating normalizing leads the widget to plot only one line ...
        # Normalizing having everything already plotted (so clicking the button), works nicely.

        if old != new and self.img_bool == False:
            self.setAnimationForLines(False)

        self.normalize_max = 0.

        if self.img_bool:
            if self.normalize_bool:
                self.img_max = np.nanmax(self.img_data)
                self.img_data = self.img_data / self.img_max
            else:
                self.img_data = self.img_data * self.img_max

            self.update_imshow(self.img_data)
        else:
            if self.normalize_bool:
                self.normalize_maxes = []
                line = None
                for l in self.lines_list:
                    line = self._is_line_in_axes(l)
                    x, y = line.get_data()
                    max = np.nanmax(y)
                    self.normalize_maxes.append(max)
                    if self.normalize_max < max:
                        self.normalize_max = max

                for l in self.lines_list:
                    line = self._is_line_in_axes(l)
                    x, y = line.get_data()
                    line.set_data(x, y / self.normalize_max)

                # if not self.img_bool:
                if line is not None:
                    if not line.get_animated():
                        self.draw()
            else:
                line = None
                if len(self.normalize_maxes) > 0:
                    for i, l in enumerate(self.lines_list):
                        line = self._is_line_in_axes(l)
                        x, y = line.get_data()
                        max = np.nanmax(y)
                        if old != new:
                             line.set_data(x, y / max * self.normalize_maxes[i])
                        else:
                            line.set_data(x, y)

                    if line is not None:
                        if not line.get_animated():
                            self.draw()

    def draw(self):
        if self.autoscale and not self.img_bool:
            axes = self.figure.get_axes()
            for ax in axes:
                ax.relim()
                ax.autoscale()
                # ax.autoscale_view(True,True,True)

        self.draw_canvas()

    def _img_bool_changed(self, val):
        self.figure.clear()
        if val:
            self.grid = False
        else:
            self.grid = True
        self.create_axis_if_no_axis()

    def _log_bool_changed(self):
        if self.img_bool:
            self.clear()
            if not self.log_bool:
                self.img_kwargs.pop('norm')
            self.imshow(self.img_data, **self.img_kwargs)
        else:
            self.setAnimationForLines(False)  # has to be done, otherwise no datapoints
            if self.log_bool:  # TODO: Maybe add xscale log, but not needed now.
                # self.axes_selector.set_xscale("log", nonposx='clip')
                self.axes_selector.set_yscale("log", nonposy='clip')
            else:
                self.axes_selector.set_yscale("linear")
            self.draw()

    def _image_slider_btn_fired(self):
        self.autoscale = False
        self.edit_traits(view='image_slider_view')

    def imshow(self, z, ax=0, **kwargs):
        if self.normalize_bool:
            self._normalize_bool_changed()
            return

        if self.log_bool:
            kwargs['norm'] = LogNorm()

            if np.any(z < 0.):
                print(self.__class__.__name__, ": WARNING - All values below 0. has been set to 0.")
                z[np.where(z < 0.)] = 0.

        self.img_data = np.array(z)

        if 'label' in kwargs:
            self.label = kwargs.pop('label')

        if 'origin' in kwargs:
            self.origin = kwargs['origin']

        if 'aspect' in kwargs:
            aspect = kwargs.pop('aspect')
        else:
            aspect = 'auto'

        if not self.img_bool:
            self.img_bool = True
            self.img = self.axes_selector.imshow(self.img_data, aspect=aspect, **kwargs)
            # print("type(self.img) = ", type(self.img))
            if not hasattr(self, "label"):
                self.label = ''

            self.cb = self.figure.colorbar(self.img, label=self.label)
            self.draw()
        else:
            self.update_imshow(self.img_data, ax=ax)
            if 'extent' in kwargs.keys():
                self.img.set_extent(kwargs['extent'])

            # print("update: type(self.img) = ", type(self.img))


        assert type(self.img) == mpl.image.AxesImage
        self._set_cb_slider()
        self.img_kwargs = kwargs


    def update_imshow(self, z, ax=0):
        z = np.array(z)
        # print("BasicFigure: Updating imshow: z.shape = ", z.shape)
        self.img.set_data(z)
        if self.autoscale:
            self.img.autoscale()

        self.draw()


    @on_trait_change('autoscale')
    def _set_cb_slider(self):
        if self.autoscale and self.img_bool:
            minv, maxv = float(np.nanmin(self.img_data).round(2)), float(np.nanmax(self.img_data).round(2))
            self.vmin_lv = minv
            self.vmin_hv = maxv
            self.vmax_lv = minv
            self.vmax_hv = maxv
            self.vmin = self.vmin_lv
            self.vmax = self.vmax_hv

    def _vmin_changed(self):
        vmin = self.vmin
        if self.log_bool:
            if self.vmin < 0.:
                vmin = 0.

        if not self.autoscale:
            self.img.set_clim(vmin=vmin,vmax=self.vmax)
            self.draw()

    def _vmax_changed(self):
        vmin = self.vmin
        if self.log_bool:
            if self.vmin < 0.:
                vmin = 0.

        if not self.autoscale:
            self.img.set_clim(vmin=vmin,vmax=self.vmax)
            self.draw()


    def plot(self, x, y, ax=0, **kwargs):
        self.img_bool = False
        fmt, label, text, pos = self._test_plot_kwargs(kwargs)
        print ('Text: {}'.format(text))
        print ('Pos: {}'.format(pos))
        axes = self.get_axes()
        line = self._is_line_in_axes(label)

        assert len(x) > 0, "BasicFigure: Length of x array is 0"

        if len(x) > self.mask_length:
            x = self._mask_data(x)
            y = self._mask_data(y)

        nodraw = False
        if 'nodraw' in kwargs:
            if kwargs.pop('nodraw'):
                nodraw = True

        if not self._is_line_in_axes(label):
            print("BasicFigure: Plotting ", label)
            line = axes[ax].plot(x, y, fmt, **kwargs)
            self.txt = axes[ax].text(pos[0], pos[1], text, transform=axes[ax].transAxes, fontsize = 12)
            self.lines_list.append(label)
            self.draw_legend()

            if self.log_bool:  # TODO: Maybe add xscale log, but not needed now.
                self.axes_selector.set_yscale("log", nonposy='clip')
            else:
                self.axes_selector.set_yscale("linear")

        else:
            if line.get_animated():
                self.setAnimationForLines(False)  # doesn't work otherwise, dunno why.
            line.set_data(x,y)
            self.txt.set_text(text)

        if not nodraw:
            self._normalize_bool_changed()
            self.draw()  # draws with respect to autolim etc.

        if hasattr(line, "append"):
            return line[0]
        else:
            return line


    def blit(self, x, y, ax=0, **kwargs):
        kwargs['animated'] = True

        self.img_bool = False
        fmt, label = self._test_plot_kwargs(kwargs)
        axes = self.get_axes()
        line = self._is_line_in_axes(label)

        assert len(x) > 0, "BasicFigure: Length of x array is 0"

        if len(x) > self.mask_length:
            x = self._mask_data(x)
            y = self._mask_data(y)

        nodraw = False
        if 'nodraw' in kwargs:
            if kwargs.pop('nodraw'):
                nodraw = True

        if not self._is_line_in_axes(label):
            print("BasicFigure: Plotting blitted ", label)
            axes[ax].plot(x, y, fmt, **kwargs)
            self.lines_list.append(label)
            self.draw_legend()
            self.figure.canvas.draw()
            self.background = self.canvas.copy_from_bbox(self.axes_selector.bbox)
            self.refreshLines(ax)
        else:
            l = self._is_line_in_axes(label)
            if not l.get_animated():
                self.setAnimationForLines(True)
                self.blit(x, y, ax=0, **kwargs)

            self.canvas.restore_region(self.background)
            self._setlinedata(x, y , ax, **kwargs)
            self.refreshLines(ax)
            self.canvas.blit(self.axes_selector.bbox)

        self._normalize_bool_changed()

    def _setlinedata(self, x, y, ax, **kwargs):
        x = np.array(x)
        y = np.array(y)
        l = self._is_line_in_axes(kwargs['label'])
        l.set_data(x,y)

    def mpl_setup(self):
        print("MinimalFigure: Running mpl_setup - connecting button press events")
        self.canvas = self.figure.canvas  # creates link (same object)
        self.figure.canvas.mpl_connect('button_press_event', self.__onclick_and_draw)


    def __onclick(self, event):
        if event is None:
            return None
        self.clickdata = (event.button, event.x, event.y, event.xdata, event.ydata)
        if not self.img_bool:
            self.setAnimationForLines(False)
        print('BasicFigure: xdata: {}, ydata: {}'.format(event.xdata, event.ydata))
        self.xdata = event.xdata
        self.ydata = event.xdata
        return (self.xdata, self.ydata)

    def __onclick_and_draw(self, event):
        print("__onclick_and_draw")
        if event is None:
            return None
        self.clickdata = (event.button, event.x, event.y, event.xdata, event.ydata)
        # draw the first point
        self.x_first = event.xdata
        self.y_first = event.ydata
        ax = self.figure.gca()
        ax.plot(self.x_first, self.y_first, 'bo')
        self.figure.canvas.draw()

        if not self.img_bool:
            self.setAnimationForLines(False)

        self.figure.canvas.mpl_connect('button_release_event', self.__move_and_draw)

    def __move_and_draw(self, event):
        print("__move_and_draw")
        if event is None:
            return None
        ax = self.figure.gca()
        if ax.lines:
        # remove old lines
            ax.lines = []
            print('ax.lines {}'.format(ax.lines[:]))

        self.x_second, self.y_second = event.xdata, event.ydata
        print('BasicFigure: xdata: {}, ydata: {}'.format(self.x_second, self.y_second))
        ax.plot([self.x_first, self.x_second], [self.y_first, self.y_second], '-', color = 'black', linewidth = 5)
        self.figure.canvas.draw()

    def setAnimationForLines(self, TF):
        self.animated = TF
        axes = self.get_axes()
        for ax in axes:
            for l in ax.get_lines():
                l.set_animated(TF)

            ax.relim()
            # if self.autoscale:  # has to be off, otherwise no zoom
            #     ax.autoscale()

        # self.canvas.update()
        self.canvas.draw()
        self.background = self.canvas.copy_from_bbox(self.axes_selector.bbox)

    def refreshLines(self, ax):
        axes = self.get_axes()
        for line in axes[ax].get_lines():
            axes[ax].draw_artist(line)

        self.canvas.update()

    def draw_legend(self, ax=None):
        print("BasicFigure: Drawing Legend")
        axes = self.figure.get_axes()
        if ax == None:
            for ax in axes:
                leg = ax.legend(loc=0, shadow=True, fancybox=True)
        else:
            axes[ax].legend(loc=0, shadow=True, fancybox=True)

    def options_group(self):
        g = HGroup(
            UItem('options_btn'),
            UItem('clear_btn'),
            UItem('line_selector', visible_when='not img_bool'),
            UItem('copy_data_btn', visible_when='not img_bool'),
            HGroup(
                Item('normalize_bool', label='normalize'),
                Item('log_bool', label='log scale'),
                Item('cmap_selector', label='cmap', visible_when='img_bool'),
                UItem('image_slider_btn', visible_when='img_bool'),
                UItem('save_fig_btn'),
            ),
        )
        return g

    def traits_view(self):
        trait_view = View(
            UItem('figure', editor=MPLFigureEditor(), style='custom'),
            Include('options_group'),
            handler=MPLInitHandler,
            resizable=True,
        )
        return trait_view

    def traits_scroll_view(self):
        traits_scroll_view = View(
            UItem('figure', editor=ScrollableMPLFigureEditor(), style='custom'),
            Include('options_group'),
            handler=MPLInitHandler,
            resizable=True,
            scrollable=True,
        )
        return traits_scroll_view

    def image_slider_view(self):
        g = View(
            VGroup(
                Item('vmin', label='min', style='custom', visible_when='img_bool'),
                Item('vmax', label='max', style='custom', visible_when='img_bool'),
                Item('autoscale'),
            ),
            resizable=True,
        )

        return g

    def traits_options_view(self):
        traits_options_view = View(
            Item('axes_selector'),
            Item('title'),
            Item('xlabel'),
            Item('ylabel'),
            Item('zlabel'),
            Item('fontsize'),
            HGroup(
                Item('grid'),
                Item('autoscale'),
                Item('mask_data_bool', label='mask data', visible_when='not img_bool'),
                Item('mask_length', width=-50, visible_when='not img_bool'),
            ),
            Item('clickdata', style='readonly'),
            resizable=True,
        )
        return traits_options_view

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


class BlittedFigure(BasicFigure):
    def plot(self, *args, **kwargs):
        self.blit(*args, **kwargs)



if __name__ == '__main__':
    # minimal_figure = MinimalFigure(figsize=(6 * 1.618, 6), facecolor='w', tight_layout=True)
    # minimal_figure.configure_traits(view='traits_view')

    w, h = (5,5)
    basic_figure = BasicFigure(figsize=(w,h), facecolor='w', tight_layout=True)
    basic_figure.configure_traits(view='test_traits_view')