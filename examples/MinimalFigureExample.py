from __future__ import print_function, division

from TraitsMPLWidget import MinimalFigure
from traits.api import HasTraits, on_trait_change, Instance, Range, Array, Button
from traitsui.api import View, VGroup, Item, UItem, HGroup

import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import numpy as np

from scipy.stats import norm

__author__ = 'd.wilson'

class MinimalFigureExample(HasTraits):
    hist_fig0 = Instance(MinimalFigure)
    hist_fig1 = Instance(MinimalFigure)
    poiss_range = Range(0, 100, 1)
    data = Array

    def _hist_fig0_default(self):
        hist_fig0 = MinimalFigure(num=0)  # minimal figure will create a plt.figure and store it.
        hist_fig0.grid = True  # activate grid
        return hist_fig0

    def _hist_fig1_default(self):
        hist_fig1 = MinimalFigure(num=1)  # minimal figure will create a plt.figure and store it.
        return hist_fig1

    @on_trait_change('poiss_range')
    def get_data(self):
        self.data = np.random.poisson(self.poiss_range, int(1e4))  # get possion data

    def fit_data(self, data):
        return norm.fit(data)  # fit gaussion (to poission data)

    @on_trait_change('data')
    def plot_fig1(self):
        self.hist_fig1.clear()
        plt.figure(1)
        data = self.data * np.pi

        n, bins, patches = plt.hist(data, normed=1)  # create histogram

        mu, sigma = self.fit_data(data)  # fit histogram data

        xfitdata = np.linspace(np.min(bins), np.max(bins), 500)  # create x array for fit
        y = mlab.normpdf(xfitdata, mu, sigma)

        plt.plot(xfitdata, y, 'r--', linewidth=2)  # plot
        plt.grid(True)  # show grid
        plt.title(r'$\mathrm{Fitting\ wrong\ function\ to\ data:}\ \mu=%.3f,\ \sigma=%.3f$' % (mu, sigma))
        self.hist_fig1.update_lines()  # updates line array to copy data from fit out of GUI


    @on_trait_change('data')
    def plot_fig0(self):
        self.hist_fig0.clear()
        plt.figure(0)
        n, bins, patches = plt.hist(self.data, normed=1)  # create histogram

        mu, sigma = self.fit_data(self.data)  # fit histogram data

        xfitdata = np.linspace(np.min(bins), np.max(bins), 500)  # create x array for fit
        y = mlab.normpdf(xfitdata, mu, sigma)

        plt.plot(xfitdata, y, 'r--', linewidth=2)  # plot
        plt.grid(True)  # show grid
        plt.title(r'$\mathrm{Fitting\ wrong\ function\ to\ data:}\ \mu=%.3f,\ \sigma=%.3f$' % (mu, sigma))
        self.hist_fig0.update_lines()  # updates line array to copy data from fit out of GUI

    traits_view = View(
        VGroup(
            HGroup(
                UItem('hist_fig0', style='custom'),
                UItem('hist_fig1', style='custom'),
                # label='Histogram'
            ),
            HGroup(
                UItem('poiss_range'),
            ),
        ),
        resizable=True,
    )


if __name__ == '__main__':
    min_fig_ex = MinimalFigureExample()
    min_fig_ex.configure_traits()



