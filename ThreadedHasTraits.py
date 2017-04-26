from __future__ import (print_function, division, absolute_import)
import time
import threading
import cPickle

import numpy as np

from traits.api import (HasTraits, Dict, on_trait_change, Int, Button, Bool, Str, Array)
from traitsui.api import (View, Item, Group)

__author__ = 'SirJohnFranklin'

class CaptureThread(threading.Thread):
    """
        This class is used to do task threaded.

        Usage in other classes:

            def do_threaded(self, func):
                self.thread = CaptureThread()
                self.thread.obj = self
                self.thread.func = func
                self.thread.start()
    """
    def __init__(self):
        super(CaptureThread, self).__init__()

    def run(self):
        print(self, ": Thread from ", self.obj, " started with function: ", self.func)
        exec('self.obj.' + self.func)
        print(self, ": Thread from ", self.obj, " with function: ", self.func, " finished!")


class CaptureThreadPerm(threading.Thread):
    """
        This class is used to do a task threaded and till self.stop = True

        Usage in other classes:

            Same as CaptureThread
    """
    def __init__(self, verbose=False):
        super(CaptureThreadPerm, self).__init__()
        self.stop = False
        self.verbose = verbose

    def run(self):
        if self.verbose:
            print(self, ": Thread from ", self.obj, " started with function: ", self.func)
        while not self.stop:
            exec('self.obj.' + self.func)

        if self.verbose:
            print(self, ": Thread from ", self.obj, " with function: ", self.func, " stopped.")


class tHasTraits(HasTraits):
    threads = Dict(transient=True)  # dict with threaded functions and threads itself
    locks = Dict()
    verbose = Bool(True)

    def __init__(self):
        super(tHasTraits, self).__init__()

    def __setstate__ ( self, state, trait_change_notify = True ):
        """ Restores the previously pickled state of an object.
            Taken from
        """
        pop = state.pop
        if pop( '__traits_version__', None ) is None:
            # If the state was saved by a version of Traits prior to 3.0, then
            # use Traits 2.0 compatible code to restore it:
            values = [ ( name, pop( name ) )
                       for name in pop( '__HasTraits_restore__', [] ) ]
            self.__dict__.update( state )
            self.trait_set( trait_change_notify=trait_change_notify,
                            **dict( values ) )
            self.__init__()
        else:
            # Otherwise, apply the Traits 3.0 restore logic:
            self._init_trait_listeners()
            self.trait_set( trait_change_notify = trait_change_notify, **state )
            self._post_init_trait_listeners()
            self.traits_init()
            self.__init__()

        self.traits_inited( True )

    def start_thread(self, func, permanent=False):
        if func in self.threads:
            self.stop_thread(func)

        if not permanent:
            self.threads[func] = CaptureThread()
        else:
            if func in self.threads:
                if self.verbose:
                    print(self, ": Permanent Thread for ", func, " is already running.")
            else:
                self.threads[func] = CaptureThreadPerm(verbose=self.verbose)

        self.threads[func].obj = self
        self.threads[func].func = func
        self.threads[func].start()

    def stop_thread(self, func):
        if func in self.threads:
            self.threads[func].stop = True

            while self.threads[func].isAlive() and isinstance(self.threads[func], CaptureThreadPerm):
                if self.verbose:
                    print(self, ": Permanent ", func, " thread is still living.")
                time.sleep(0.1)

            del self.threads[func]
            if self.verbose:
                print(self, ":Thread stopped.")
        else:
            print(self, ": No thread ", func, " found.")

    def traits_detail_view(self):
        traits_detail_view = View(
            Group(
                Item('threads'),
                Item('verbose'),
                label='Threading Options',
                show_border=True,
            )
        )

        return traits_detail_view


class ThreadTest(tHasTraits):
    """
        Example Class how to use ThreadedHasTraits
    """

    _current_time = Str()
    verbose = Bool(True)
    number = Int()
    start_aquisition_btn = Button('Start Permanent Thread')
    stop_aquisition_btn = Button('Stop Permanent Thread')
    start_single_aquisition_btn = Button('Start normal Thread')
    save_btn = Button('save to pickle')

    def __init__(self):
        super(ThreadTest, self).__init__()
        self.start_thread('_set_time()', permanent=True)

    def add_one(self):
        self.number += 1
        time.sleep(0.3)

    @on_trait_change('start_aquisition_btn')
    def add_one_threaded(self):
        do = 'add_one()'
        self.start_thread(do, permanent=True)

    def _stop_aquisition_btn_fired(self):
        self.stop_thread('add_one()')

    def _start_single_aquisition_btn_fired(self):
        self.start_thread('add_one()')

    def _set_time(self):
        self._current_time = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        time.sleep(1)

    def _save_btn_fired(self):
        cPickle.dump(self, open('testing/threadedhastraits.pkl', 'wb'), protocol=-1)
        print("ThreadedHasTraits: saved to testing/threadedhastraits.pkl")

    traits_view = View(
        Item("_current_time", style='readonly', label='Current Time'),
        Item('number'),
        Item('start_aquisition_btn'),
        Item('stop_aquisition_btn'),
        Item('start_single_aquisition_btn'),
        Item('save_btn'),
    )


if __name__ == '__main__':
    #  ThreadTest
    from datetime import datetime

    # t = ThreadTest()
    # t.configure_traits()

    tnew = cPickle.load(open('testing/threadedhastraits.pkl', 'rb'))
    tnew.configure_traits()









