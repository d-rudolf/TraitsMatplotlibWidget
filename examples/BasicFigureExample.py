from __future__ import print_function, division

import numpy as np

from TraitsMPLWidget import BasicFigure, MPLFigureEditor, MPLInitHandler
from traits.api import Range, Button, List, Int
from traitsui.api import View, UItem, Item, Include, HGroup
from matplotlib.widgets import RectangleSelector, SpanSelector
from DraggableResizableRectangle import DraggableResizeableRectangle, AnnotatedRectangle

import matplotlib as mpl


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


class WidgetFigure(BasicFigureExample):
    selector_btn = Button('Selector')
    selectionPatches = List()  # contains patches for image stack analysis
    clearPatchesBtn = Button('Clear Patches')
    nColorsFromColormap = Int(5)

    def _selector_btn_fired(self):
        self.connectSelector()

    def connectSelector(self):
        print(self.__class__.__name__, ": Connecting Selector")
        # try:
        self.rs = RectangleSelector(self.axes_selector, self.rectangleSelectorFunc, drawtype='box', useblit=True, button=[3])
        # except:
        #     print(self.__class__.__name__, ": Canvas is not ready.")

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

    def clear_selectionPatches(self):
        if len(self.selectionPatches) != 0:
            print(self.__class__.__name__, ": Clearing selection patches")
            for p in self.selectionPatches:
                try:
                    p.remove()
                except ValueError:
                    print(self.__class__.__name__, ": Patch was not found.")

            self.selectionPatches = []
            self.canvas.draw()

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
                UItem('selector_btn'),
                UItem('clearPatchesBtn'),
            ),
        )
        return g


if __name__ == '__main__':
    # basic_figure_test = BasicFigureTest(figsize=(6 * 1.618, 6), facecolor='w', tight_layout=True)
    # basic_figure_test.configure_traits(view='test_traits_view')

    basic_figure_test = WidgetFigure(figsize=(6 * 1.618, 6), facecolor='w', tight_layout=True)
    basic_figure_test.configure_traits(view='test_traits_view')