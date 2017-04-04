from TraitsMPLWidget import BasicFigure

from traits.api import HasTraits, Instance, Array, on_trait_change, Range
from traitsui.api import View, UItem, HGroup, VGroup, Item
import numpy as np

class MultipleAxesExample(HasTraits):
    fig = Instance(BasicFigure)

    data = Array
    sin_range = Range(0.,300.,1.)

    def _fig_default(self):
        fig = BasicFigure(tight_layout=True)
        fig.figure.add_subplot(211)
        fig.figure.add_subplot(212)
        fig.get_axes()
        return fig

    @on_trait_change('sin_range')
    def generate_data(self):
        self.xvals = np.linspace(0., self.sin_range * np.pi / 10, 500)
        self.data = np.sin(self.xvals)*np.cos(self.xvals*30)+self.xvals**2

    @on_trait_change('data')
    def plot(self):
        self.fig.plot(self.xvals, self.data, label='sin',ax=0)
        self.fig.plot(self.xvals[0:-1], np.diff(self.data), label='derivative', ax=1)

    def traits_view(self):
        view = View(
            VGroup(
                UItem('fig', style='custom'),
                VGroup(
                    Item('sin_range'),
                ),
            ),
            resizable=True,
        )
        return view


if __name__ == '__main__':
    ex = MultipleAxesExample()
    ex.configure_traits()


