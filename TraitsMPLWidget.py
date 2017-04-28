from __future__ import division, print_function
from pyface.qt import QtGui, QtCore

try:
    import win32clipboard
    print("Using win32clipboard")
except:
    import pyperclip
    print("Using Linux clipboard")

import matplotlib as mpl
mpl.use('Qt4Agg')
import numpy as np
import matplotlib.pyplot as plt

from traitsui.qt4.editor import Editor
from traitsui.qt4.basic_editor_factory import BasicEditorFactory
from traits.api import Instance, HasTraits, Int, Str, Float, List, Array, Bool, Tuple, Button, Dict, Enum, Range, on_trait_change
from traitsui.api import Handler, View, Item, UItem, CheckListEditor, HGroup, VGroup, Include
from pyface.api import FileDialog, OK

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.colors import LogNorm
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT
from matplotlib.widgets import RectangleSelector, SpanSelector
from DraggableResizableRectangle import DraggableResizeableRectangle, AnnotatedRectangle, AnnotatedLine, DraggableResizeableLine

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
        print(self.__class__.__name__, ": Creating canvas (_create_canvas)")
        frame_canvas = QtGui.QWidget()

        scrollarea = QtGui.QScrollArea()
        mpl_canvas = FigureCanvas(self.value)
        mpl_canvas.setParent(scrollarea)
        scrollarea.setWidget(mpl_canvas)

        mpl_toolbar = NavigationToolbar2QT(mpl_canvas, frame_canvas)
        # mpl_toolbar.setIconSize(QtCore.QSize(30, 30))  # activate for smaller icon sizes

        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(scrollarea)
        vbox.addWidget(mpl_toolbar)
        vbox.setGeometry(QtCore.QRect(0, 0, 1000, 1000))
        frame_canvas.setLayout(vbox)
        return frame_canvas


class _MPLFigureEditor(Editor):
    canvas = Instance(FigureCanvas)
    toolbar = Instance(NavigationToolbar2QT)

    def init(self, parent):
        self.control = self._create_canvas(parent)
        self.set_tooltip()

    def update_editor(self):
        pass

    def _create_canvas(self, parent):
        print(self.__class__.__name__, ": Creating canvas (_create_canvas)")
        # matplotlib commands to create a canvas
        frame = QtGui.QWidget()
        mpl_canvas = FigureCanvas(self.value)
        mpl_canvas.setParent(frame)
        mpl_toolbar = NavigationToolbar2QT(mpl_canvas, frame)

        # mpl_toolbar.setIconSize(QtCore.QSize(30, 30))  # activate for smaller icon sizes

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

    # some options - more to be added!
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
        print(self.__class__.__name__, ": Create figure (_figure_default)")
        fig = plt.figure(**self.figure_kwargs)
        fig.patch.set_facecolor('w')
        return fig

    def update_axes(self):
        print(self.__class__.__name__, ": Updating axes...")
        self.axes = self.figure.get_axes()

    def add_figure(self, fig):
        print(self.__class__.__name__, ": Adding figure")
        self.figure = fig
        self.canvas = fig.canvas
        self.add_trait('figure', fig)
        self.add_trait_listener(fig)
        self.mpl_setup()
        self.update_axes()

    @on_trait_change('figure,axes[]')  # ,
    def update_lines(self):
        print(self.__class__.__name__, ": figure changed! ")
        self.update_axes()  # get axes

        # get lines
        lines = []
        for ax in self.figure.get_axes():
            for l in ax.get_lines():
                tmplinename = self._replace_line2D_str(l)
                if '_nolegend_' in tmplinename:
                    continue

                lines.append(tmplinename)

        self.lines_list = sorted(lines)

        self._set_axes_property_variables()  # get labels
        if self.canvas:
            self.canvas.draw()

    def mpl_setup(self):
        print(self.__class__.__name__, ": Running mpl_setup - connecting button press events")
        self.canvas = self.figure.canvas  # creates link (same object)
        cid = self.figure.canvas.mpl_connect('button_press_event', self.__onclick)

    def __onclick(self, event):
        if event is None:
            return None
        self.clickdata = (event.button, event.x, event.y, event.xdata, event.ydata)
        print(self.__class__.__name__, ": %s" % event)

    def clear(self):
        self._clear_btn_fired()

    def _clear_btn_fired(self):
        ax = self.figure.get_axes()
        for a in ax:
            print(self.__class__.__name__, ": Clearing axis ", a)
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

    def _is_line_in_axes(self, label, ax=None):
        """
        :param label: Label of plot
        :return: False if line is not in axes, line if line is in axes
        """
        lines = []  # use update_lines()
        if ax is None:
            for ax in self.figure.get_axes():
                for l in ax.get_lines():
                    tmplinename = self._replace_line2D_str(l)
                    if '_nolegend_' in tmplinename:
                        continue

                    lines.append(self._replace_line2D_str(l))
                    if label == self._replace_line2D_str(l):
                        return l

            # self.lines_list = sorted(lines)
        else:
            for l in ax.get_lines():
                if label == self._replace_line2D_str(l):
                    return l

        return False

    def _copy_data_btn_fired(self):
        # due to https://github.com/matplotlib/matplotlib/issues/8458, only support for xy-error in Basicfigure()
        print(self.__class__.__name__, ": Trying to copy data to clipboard")
        line = self._is_line_in_axes(self.line_selector)
        x = line.get_xdata()
        y = line.get_ydata()

        text = 'x \t y \n'
        for i in xrange(len(x)):
            text += str(x[i]) + "\t" + str(y[i]) + "\n"

        self.add_to_clip_board(text)

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
        self.axes = self.create_axis_if_no_axis()
        return self.axes

    @on_trait_change('figure')
    def create_axis_if_no_axis(self):
        # creates one axis if none created
        axes = self.figure.get_axes()
        if len(axes) == 0:
            self.figure.add_subplot(111)
            axes = self.figure.get_axes()
            self.axes = axes
            self._set_axes_property_variables()
        return axes

    @on_trait_change('figure')
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
        self.xlabel = self.axes_selector.get_xlabel()
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
    draw_legend_bool = Bool(True)

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

    errorbar_data = Dict()  # this has is needed because of https://github.com/matplotlib/matplotlib/issues/8458
    _xerr = Dict()
    _yerr = Dict()

    def __init__(self, **kwargs):
        super(BasicFigure, self).__init__(**kwargs)
        self.grid = True

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

        return fmt, label

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

        if old != new and self.img_bool is False:
            self.set_animation_for_lines(False)

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
                    if line is False:
                        continue
                    x, y = line.get_data()
                    max = np.nanmax(y)
                    self.normalize_maxes.append(max)
                    if self.normalize_max < max:
                        self.normalize_max = max

                for l in self.lines_list:
                    line = self._is_line_in_axes(l)
                    if line is False:
                        continue
                    x, y = line.get_data()
                    line.set_data(x, y / self.normalize_max)
                    if not line.get_animated():
                        self.draw()
            else:
                line = None
                if len(self.normalize_maxes) > 0:
                    for i, l in enumerate(self.lines_list):
                        line = self._is_line_in_axes(l, self.axes_selector)
                        if line is False:
                            continue
                        x, y = line.get_data()
                        max = np.nanmax(y)
                        if old != new:
                             line.set_data(x, y / max * self.normalize_maxes[i])
                        else:
                            line.set_data(x, y)

                    if line is not None and line is not False:
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
            self.set_animation_for_lines(False)  # has to be done, otherwise no datapoints
            if self.log_bool:  # TODO: Maybe add xscale log, but not needed now.
                # self.axes_selector.set_xscale("log", nonposx='clip')
                self.axes_selector.set_yscale("log", nonposy='clip')
            else:
                self.axes_selector.set_yscale("linear")
            self.draw()

    def _image_slider_btn_fired(self):
        self.autoscale = False
        self.edit_traits(view='image_slider_view')

    def _clear_btn_fired(self):
        if self.img_bool:
            self.img_bool = False  # also triggers
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

        self.errorbar_data = {}
        self.draw_canvas()

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

            if not hasattr(self, "label"):
                self.label = ''

            self.cb = self.figure.colorbar(self.img, label=self.label)
            self.draw()
        else:
            self.update_imshow(self.img_data, ax=ax)
            if 'extent' in kwargs.keys():
                self.img.set_extent(kwargs['extent'])

        assert type(self.img) == mpl.image.AxesImage
        self._set_cb_slider()
        self.img_kwargs = kwargs

    def update_imshow(self, z, ax=0):
        z = np.array(z)
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
        if self.log_bool and self.vmin < 0.:
            vmin = 0.

        if not self.autoscale:
            self.img.set_clim(vmin=vmin,vmax=self.vmax)
            self.draw()


    def axvline(self,pos, ax=0, **kwargs):
        self.ax_line(pos,'axvline',ax=ax,**kwargs)


    def axhline(self,pos, ax=0, **kwargs):
        self.ax_line(pos,'axhline',ax=ax,**kwargs)


    def ax_line(self,pos,func_str, ax=0, **kwargs):
        # self.img_bool = False
        fmt, label = self._test_plot_kwargs(kwargs)

        axes = self.figure.get_axes()
        line = self._is_line_in_axes(label)

        nodraw = False

        if 'nodraw' in kwargs:
            if kwargs.pop('nodraw'):
                nodraw = True

        if not line:
            print("BasicFigure: Plotting axhline ", label)
            if type(ax) == int:
                line = getattr(axes[ax],func_str)(pos, **kwargs)
            elif hasattr(ax, func_str):
                line = getattr(ax, func_str)(pos, **kwargs)
            else:
                raise TypeError('ax can be an int or the axis itself!')
            self.lines_list.append(label)
        else:
            line.remove()
            if type(ax) == int:
                line = getattr(axes[ax], func_str)(pos, **kwargs)
            elif hasattr(ax, func_str):
                line = getattr(ax, func_str)(pos, **kwargs)
            else:
                raise TypeError('ax can be an int or the axis itself!')

        self.lines_list.append(label)
        self.draw_legend()

        if not nodraw:
            self._normalize_bool_changed()
            self.draw()  # draws with respect to autolim etc.

        if hasattr(line, "append"):
            return line[0]
        else:
            return line


    def _is_errorbar_plotted(self, label):
        if label in self.errorbar_data:
            return self.errorbar_data[label]
        else:
            return False

    def errorbar(self, x, y, ax=0, **kwargs):
        """ Additional (to normal matplotlib plot method) kwargs:
                - (bool) nodraw     If True, will not draw canvas
                - (str) fmt         like in matplotlib errorbar(), but it is stupid to use it only in one function
        """
        self.img_bool = False
        fmt, label = self._test_plot_kwargs(kwargs)
        axes = self.get_axes()
        line = self._is_errorbar_plotted(label)

        if len(x) == 0:
            print(self.__class__.__name__, "Length of x array is 0.")
            return

        if not 'xerr' in kwargs:
            kwargs['xerr'] = np.zeros(x.shape)

        if not 'yerr' in kwargs:
            kwargs['yerr'] = np.zeros(y.shape)

        self._xerr[label] = kwargs['xerr']
        self._yerr[label] = kwargs['yerr']

        if len(x) > self.mask_length:
            x = self._mask_data(x)
            y = self._mask_data(y)
            kwargs['xerr'] = self._mask_data(kwargs.pop('xerr'))
            kwargs['yerr'] = self._mask_data(kwargs.pop('yerr'))



        nodraw = False
        if 'nodraw' in kwargs:
            if kwargs.pop('nodraw'):
                nodraw = True

        if type(line) is bool:
            print("BasicFigure: Plotting ", label)
            if type(ax) == int:
                self.errorbar_data[label] = axes[ax].errorbar(x, y, fmt=fmt, **kwargs)
            elif hasattr(ax, 'plot'):
                self.errorbar_data[label] = ax.plot(x, y, fmt=fmt, **kwargs)
            else:
                raise TypeError('ax can be an int or the axis itself!')

            self.lines_list.append(label)
            self.draw_legend()
        else:
            if line[0].get_animated():
                self.set_animation_for_lines(False)  # doesn't work otherwise, dunno why.
            self._set_errorbar_data(x, y, **kwargs)

        if not nodraw:
            self._normalize_bool_changed()
            self.draw()  # draws with respect to autolim etc.

        if hasattr(line, "append"):
            return line[0]
        else:
            return line

    def _copy_data_btn_fired(self):
        print(self.__class__.__name__, ": Trying to copy data to clipboard")
        if self.line_selector in self.errorbar_data:
            line, caplines, barlinecols = self.errorbar_data[self.line_selector]
            x = line.get_xdata()
            y = line.get_ydata()

            xerr = self._xerr[self.line_selector]
            yerr = self._yerr[self.line_selector]
            print("xerr = ", xerr)

            text = 'x \t y \t x_error \t y_error \n'
            for i in xrange(len(x)):
                text += str(x[i]) + "\t" + str(y[i]) + "\t" + str(xerr[i]) + "\t" + str(
                    yerr[i]) + "\n"
        else:
            line = self._is_line_in_axes(self.line_selector)
            x = line.get_xdata()
            y = line.get_ydata()

            text = 'x \t y \n'
            for i in xrange(len(x)):
                text += str(x[i]) + "\t" + str(y[i]) + "\n"

        self.add_to_clip_board(text)

    def _set_errorbar_data(self, *args, **kwargs):
        x, y = args
        label = kwargs['label']
        x = np.array(x)
        y = np.array(y)
        line, caplines, barlinecols = self.errorbar_data[label]

        line.set_data(x, y)
        xerr = kwargs['xerr']
        yerr = kwargs['yerr']

        if not (xerr is None and yerr is None):
            error_positions = (x - xerr, y), (x + xerr, y), (x, y - yerr), (x, y + yerr)

            # Update the caplines
            if len(caplines) > 0:
                for i, pos in enumerate(error_positions):
                    caplines[i].set_data(pos)

            # Update the error bars
            barlinecols[0].set_segments(zip(zip(x - xerr, y), zip(x + xerr, y)))
            barlinecols[1].set_segments(zip(zip(x, y - yerr), zip(x, y + yerr)))


    def plot(self, x, y, ax=0, **kwargs):
        """ Additional (to normal matplotlib plot method) kwargs:
                - (bool) nodraw     If True, will not draw canvas
                - (str) fmt         like in matplotlib errorbar(), but it is stupid to use it only in one function
        """
        self.img_bool = False
        fmt, label = self._test_plot_kwargs(kwargs)
        axes = self.get_axes()
        line = self._is_line_in_axes(label)

        if len(x) == 0:
            print(self.__class__.__name__, "Length of x array is 0.")
            return

        if len(x) > self.mask_length:
            x = self._mask_data(x)
            y = self._mask_data(y)

        nodraw = False
        if 'nodraw' in kwargs:
            if kwargs.pop('nodraw'):
                nodraw = True

        if type(line) is bool:
            print(self.__class__.__name__, ": Plotting ", label)
            if type(ax) == int:
                line = axes[ax].plot(x, y, fmt, **kwargs)
            elif hasattr(ax, 'plot'):
                line = ax.plot(x, y, fmt, **kwargs)
            else:
                raise TypeError('ax can be an int or the axis itself!')

            self.lines_list.append(label)
            self.draw_legend()
        else:
            if line.get_animated():
                self.set_animation_for_lines(False)  # doesn't work otherwise, dunno why.
            line.set_data(x,y)

        if not nodraw:
            self._normalize_bool_changed()
            self.draw()  # draws with respect to autolim etc.
            # self.start_thread('draw()')  # kind of working ...

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
            print(self.__class__.__name__, ": Plotting blitted ", label)
            axes[ax].plot(x, y, fmt, **kwargs)
            self.lines_list.append(label)
            self.draw_legend()
            self.figure.canvas.draw()
            self.background = self.canvas.copy_from_bbox(self.axes_selector.bbox)
            self.refresh_lines(ax)
        else:
            l = self._is_line_in_axes(label)
            if not l.get_animated():
                self.set_animation_for_lines(True)
                self.blit(x, y, ax=0, **kwargs)

            self.canvas.restore_region(self.background)
            self._setlinedata(x, y , ax, **kwargs)
            self.refresh_lines(ax)
            self.canvas.blit(self.axes_selector.bbox)

        self._normalize_bool_changed()

    def _setlinedata(self, x, y, ax, **kwargs):
        x = np.array(x)
        y = np.array(y)
        l = self._is_line_in_axes(kwargs['label'])
        l.set_data(x,y)

    def mpl_setup(self):
        print(self.__class__.__name__, ": Running mpl_setup - connecting button press events")
        self.canvas = self.figure.canvas  # creates link (same object)
        cid = self.figure.canvas.mpl_connect('button_press_event', self.__onclick)

    def __onclick(self, event):
        if event is None:
            return None
        self.clickdata = (event.button, event.x, event.y, event.xdata, event.ydata)
        if not self.img_bool:
            self.set_animation_for_lines(False)
        print(self.__class__.__name__, ": %s" % event)

    def set_animation_for_lines(self, TF):
        self.animated = TF
        axes = self.get_axes()
        for ax in axes:
            for l in ax.get_lines():
                l.set_animated(TF)

            ax.relim()

        self.canvas.draw()
        self.background = self.canvas.copy_from_bbox(self.axes_selector.bbox)

    def refresh_lines(self, ax):
        axes = self.get_axes()
        for line in axes[ax].get_lines():
            axes[ax].draw_artist(line)

        self.canvas.update()

    def draw_legend(self, ax=None):
        if self.draw_legend_bool:

            print(self.__class__.__name__, ": Drawing Legend")
            axes = self.figure.get_axes()
            if ax == None:
                for ax in axes:
                    leg = ax.legend(loc=0, fancybox=True)
            else:
                axes[ax].legend(loc=0, fancybox=True)

    def options_group(self):
        g = HGroup(
            UItem('options_btn'),
            UItem('clear_btn'),
            UItem('line_selector', visible_when='not img_bool'),
            UItem('copy_data_btn', visible_when='not img_bool'),
            Item('normalize_bool', label='normalize'),
            Item('log_bool', label='log scale'),
            Item('draw_legend_bool', label='draw legend'),
            Item('cmap_selector', label='cmap', visible_when='img_bool'),
            UItem('image_slider_btn', visible_when='img_bool'),
            UItem('save_fig_btn'),
        )
        return g

    def options_group_axes_sel(self):
        g = HGroup(
            UItem('options_btn'),
            UItem('clear_btn'),
            UItem('line_selector', visible_when='not img_bool'),
            UItem('copy_data_btn', visible_when='not img_bool'),
            Item('axes_selector'),
            Item('normalize_bool', label='normalize'),
            Item('log_bool', label='log scale'),
            Item('draw_legend_bool', label='draw legend'),
            Item('cmap_selector', label='cmap', visible_when='img_bool'),
            UItem('image_slider_btn', visible_when='img_bool'),
            UItem('save_fig_btn'),
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
            # scrollable=True,
        )
        return traits_scroll_view

    def traits_multiple_axes_view(self):
        traits_scroll_view = View(
            UItem('figure', editor=MPLFigureEditor(), style='custom'),
            Include('options_group_axes_sel'),
            handler=MPLInitHandler,
            resizable=True,
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


class WidgetFigure(BasicFigure):
    nColorsFromColormap = Int(5)

    lock_all_btn = Button('Lock all Widges')
    act_all_btn = Button('Activate all Widgets')

    unlock_all_btn = Button('(Un-) Lock')
    posWidgets_list = List()
    selectWidget_sel= Enum(values = 'posWidgets_list')
    clearWidgetBtn = Button('Clear Current Widget')

    selectionPatches = List()
    selectionPatches_names=List()

    selectionLines = List()
    selectionLines_names=List()

    def _selectWidget_sel_default(self):
        w = self.posWidgets_list[0]
        self._lin_selector()
        return w

    def _clearWidgetBtn_fired(self):
        if self.selectWidget_sel == self.posWidgets_list[0]:
            self._clearLines()

        if self.selectWidget_sel == self.posWidgets_list[1]:
            self._clearPatches()

    @on_trait_change('selectWidget_sel')
    def _selectWidget(self,widget):
        if widget == self.posWidgets_list[0]:
            self._lin_selector()

        if widget == self.posWidgets_list[1]:
            self._rec_selector()


    def _unlock_all_btn_fired(self):
        try:
            if not self.lock:
                self.lock = True
                self._lock_all()
            else:
                self.lock = False
                self._act_all()
        except:
            self.lock = False
            self._unlock_all_btn_fired()

    def _posWidgets_list_default(self):
        w = list()
        w.append('Line Selector')
        w.append('Rectangle Selector')
        return w

    def _lock_all(self):
        try:
            self.rs.disconnect_events()
            for i in self.selectionPatches: i.disconnect()
        except:
            print('No Rectangle to lock')

        try:
            self.ls.disconnect_events()
            for i in self.selectionLines: i.disconnect()
        except:
            print('No line to lock')


    def _act_all(self):
        for i in self.selectionPatches: i.connect()
        for i in self.selectionLines: i.connect()

    def _lin_selector(self):
        try:
            self.rs.disconnect_events()
            DraggableResizeableRectangle.lock = True
            print('Rectangles are locked')

        except:
            print('Rectangles could not be locked')

        print(self.__class__.__name__, ": Connecting Line Selector")
        DraggableResizeableLine.lock = None
        self.ls = RectangleSelector(self.axes_selector, self.lineselectorfunc, drawtype='line', useblit=True,button=[3])

    def lineselectorfunc(self,eclick,erelease,cmap=mpl.cm.jet):
        print(self.__class__.__name__, "Line Selector:")
        print(self.__class__.__name__, "eclick: {} \n erelease: {}".format(eclick, erelease))
        print()

        x0, y0 = eclick.xdata, eclick.ydata
        x1, y1 = erelease.xdata, erelease.ydata

        cNorm = mpl.colors.Normalize(vmin=0, vmax=self.nColorsFromColormap)
        scalarMap = mpl.cm.ScalarMappable(norm=cNorm, cmap=cmap)
        color = scalarMap.to_rgba(len(self.selectionLines) + 1)
        text = 'line ' + str(len(self.selectionLines))
        line = AnnotatedLine(self.axes_selector,x0, y0, x1, y1,text=text,color=color)
        self.selectionLines.append(line)
        self.selectionLines_names.append(line.text)
        self.canvas.draw()

    def get_SelectedLine(self, patch):
        for i, line in enumerate(self.selectionLines):
            if line.text == patch:
                break
        return self.selectionLines[i]

    def _clearLines(self):
        print(self.__class__.__name__, ": Clearing selection lines")
        if len(self.selectionLines) != 0:
            print(self.__class__.__name__, ": Clearing selection lines")
            for l in self.selectionLines:
                try:
                    l.remove()
                except ValueError:
                    print(self.__class__.__name__, ": Line was not found.")
            self.selectionLines = []
            self.selectionLines_names = []

        self.canvas.draw()


    def _rec_selector(self):
        try:
            self.ls.disconnect_events()
            DraggableResizeableLine.lock = True
            print('Line Selector is locked')
        except:
            print('Line Selector could not be locked')
        DraggableResizeableRectangle.lock = None

        print(self.__class__.__name__, ": Connecting Rectangle Selector")

        self.rs = RectangleSelector(self.axes_selector, self.rectangleSelectorFunc, drawtype='box', useblit=True, button=[3])

    def get_selectionPatches_names(self):
        self.selectionPatches_names = []
        for i in self.selectionPatches:
            self.selectionPatches_names.append(i.text)

        return self.selectionPatches_names

    def rectangleSelectorFunc(self, eclick, erelease, cmap=mpl.cm.jet):
        """
            Usage:
            @on_trait_change('fig:selectionPatches:rectUpdated')
            function name:
                for p in self.fig.selectionPatches:
                    do p

        """
        print(self.__class__.__name__, "Rectangle Selector:")
        print(self.__class__.__name__, "eclick: {} \n erelease: {}".format(eclick, erelease))
        print()

        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata

        cNorm = mpl.colors.Normalize(vmin=0, vmax=self.nColorsFromColormap)
        scalarMap = mpl.cm.ScalarMappable(norm=cNorm, cmap=cmap)

        color = scalarMap.to_rgba(len(self.selectionPatches) + 1)

        self.anRect = AnnotatedRectangle(self.axes_selector, x1, y1, x2, y2, 'region ' + str(len(self.selectionPatches)), color=color)
        self.selectionPatches.append(self.anRect)

        self.canvas.draw()

    def get_SelectedPatch(self, patch):
        for i, rect in enumerate(self.selectionPatches):
            if rect.text == patch:
                break

        return self.selectionPatches[i]


    def _clearPatches(self):
        if len(self.selectionPatches) != 0:
            print(self.__class__.__name__, ": Clearing selection patches")
            for p in self.selectionPatches:
                try:
                    p.remove()
                except ValueError:
                    print(self.__class__.__name__, ": Patch was not found.")

            self.selectionPatches = []
            self.canvas.draw()

    def clear_widgets(self):
        self._clearPatchesBtn_fired()
        self._clearLinesBtn_fired()


    def options_group(self):
        g = HGroup(
            UItem('options_btn'),
            UItem('clear_btn'),
            UItem('line_selector', visible_when='not img_bool'),
            UItem('copy_data_btn', visible_when='not img_bool'),
            HGroup(
                VGroup(
                    HGroup(
                        Item('normalize_bool', label='normalize'),
                        Item('log_bool', label='log scale'),
                        Item('cmap_selector', label='cmap', visible_when='img_bool'),
                        UItem('image_slider_btn', visible_when='img_bool'),
                        UItem('save_fig_btn'),
                    ),
                    HGroup(
                        UItem('selectWidget_sel'),
                        UItem('unlock_all_btn'),
                        UItem('clearWidgetBtn'),
                    )
                )

            ),
        )
        return g


class BlittedFigure(BasicFigure):
    def plot(self, *args, **kwargs):
        self.blit(*args, **kwargs)


if __name__ == '__main__':
    # minimal_figure = MinimalFigure(figsize=(6 * 1.618, 6), facecolor='w', tight_layout=True)
    # minimal_figure.configure_traits(view='traits_view')

    basic_figure = BasicFigure(figsize=(5 * 1.618, 5), facecolor='w', tight_layout=True)
    basic_figure.configure_traits()
    # basic_figure.configure_traits(view='traits_multiple_axes_view')
    # basic_figure.configure_traits(view='traits_scroll_view')