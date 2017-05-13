

import numpy as np

from traits.api import HasTraits, Instance, Any, Str, on_trait_change, Int, Event
import matplotlib.patches as mpatches
import matplotlib

def axes_boundery_check(pos_1,pos_2,dx,dy,xlim,ylim):
    '''
    Checks whether the movement of the widget would result in a final position which is outside of the data range. If 
    widget being outside of data range, it sets dx/ dy so that the widget is at the closest value inside the data.
    :param pos_1: Widget source point 1
    :param pos_2: Widget source point 2
    :param dx: shift of widget in x direction
    :param dy: shift of widget in y direction
    :param xlim: axes limits in x direction
    :param ylim: axes limits in y direction
    :return: Returns 
    '''
    x0, y0 = pos_1
    x1, y1 = pos_2

    if np.min([x0 + dx, x1 + dx]) < np.min(xlim):
        if x0 < x1:
            dx = np.min(xlim) - x0
        else:
            dx = np.min(xlim) - x1

    if np.max([x0 + dx, x1 + dx]) > np.max(xlim):
        if x0 > x1:
            dx = np.max(xlim) - x0
        else:
            dx = np.max(xlim) - x1

    if np.min([y0 + dy, y1 + dy]) < np.min(ylim):
        if y0 < y1:
            dy = np.min(ylim) - y0
        else:
            dy = np.min(ylim) - y1

    if np.max([y0 + dy, y1 + dy]) > np.max(ylim):
        if y0 > y1:
            dy = np.max(ylim) - y0
        else:
            dy = np.max(ylim) - y1

    return dx, dy


class DraggableResizeableLine(HasTraits):
    """
    Resizable Lines based on the DraggabelResizableRectangle. Draggable is yet not implemented
    Author: KingKarl, April 2017
    """
    lock = None  # only one can be animated at a time
    updateXY = Int(0)
    updateText = Int(0)
    released = Int(0)
    axes_xlim = None
    axes_ylim = None

    def __init__(self, line, border_tol=0.15, allow_resize=True,
                 fixed_aspect_ratio=False):
        super(DraggableResizeableLine,self).__init__()
        self.line = line
        self.border_tol = border_tol
        self.press = None

        if DraggableResizeableLine.axes_xlim is None:
            DraggableResizeableLine.axes_xlim = self.line.axes.get_xlim()
        if DraggableResizeableLine.axes_ylim is None:
            DraggableResizeableLine.axes_ylim = self.line.axes.get_ylim()

    @staticmethod
    def reset_borders():
        DraggableResizeableLine.axes_xlim = None
        DraggableResizeableLine.axes_ylim = None
        print('Reset of DraggableResizableLines Border to None')

    def connect(self):
        'connect to all the events we need'
        self.cidpress = self.line.figure.canvas.mpl_connect('button_press_event', self.on_press)
        self.cidrelease = self.line.figure.canvas.mpl_connect('button_release_event', self.on_release)
        self.cidmotion = self.line.figure.canvas.mpl_connect('motion_notify_event', self.on_motion)

    def on_press(self, event):
        'on button press we will see if the mouse is over us and store some data'
        if event.inaxes != self.line.axes: return
        if DraggableResizeableLine.lock is not None: return

        if np.abs(self.line.axes.get_xlim()[0]-self.line.axes.get_xlim()[1])>np.abs(DraggableResizeableLine.axes_xlim[0]-DraggableResizeableLine.axes_xlim[1]):
            DraggableResizeableLine.axes_xlim = self.line.axes.get_xlim()

        if np.abs(self.line.axes.get_ylim()[0]-self.line.axes.get_ylim()[1])>np.abs(DraggableResizeableLine.axes_ylim[0]-DraggableResizeableLine.axes_ylim[1]):
            DraggableResizeableLine.axes_ylim = self.line.axes.get_ylim()

        x,y = self.line.get_data()
        x0, x1 = x
        y0, y1 = y

        if not self.within_border_tol([x0, y0],[x1, y1],event): return
        DraggableResizeableLine.lock = self

        self.press = x0, y0, x1, y1, event.xdata, event.ydata

        canvas = self.line.figure.canvas
        axes = self.line.axes
        self.line.set_animated(True)
        canvas.draw()
        self.background = canvas.copy_from_bbox(self.line.axes.bbox)

        # now redraw just the rectangle
        axes.draw_artist(self.line)

        # and blit just the redrawn area
        canvas.blit(axes.bbox)

    def within_border_tol(self,pos_0, pos_1, event):
        x0, y0 = pos_0
        x1, y1 = pos_1
        xpress, ypress = event.xdata, event.ydata

        bt = self.border_tol * (abs(x0-x1)**2 + abs(y0-y1)**2)**0.5

        if (abs(x0-xpress)**2+abs(y0-ypress)**2)**0.5<2**0.5*abs(bt) or (abs(x1-xpress)**2+abs(y1-ypress)**2)**0.5<2**0.5*abs(bt) or (abs((x0+x1)/2-xpress)**2+abs((y0+y1)/2-ypress)**2)**0.5<2**0.5*abs(bt):
            return True
        else:
            return False


    def on_motion(self, event):
        'on motion we will move the rect if the mouse is over us'
        if DraggableResizeableLine.lock is not self:
            return
        if event.inaxes != self.line.axes: return
        x0, y0, x1, y1, xpress, ypress = self.press
        self.dx = event.xdata - xpress
        self.dy = event.ydata - ypress
        self.update_line()

        canvas = self.line.figure.canvas
        axes = self.line.axes

        # restore the background region
        canvas.restore_region(self.background)

        # redraw just the current line
        axes.draw_artist(self.line)

        # blit just the redrawn area
        canvas.blit(axes.bbox)
        self.updateXY += 1


    def on_release(self, event):
        'on release we reset the press data'
        if DraggableResizeableLine.lock is not self:
            return

        self.press = None
        DraggableResizeableLine.lock = None

        # turn off the rect animation property and reset the background
        self.line.set_animated(False)
        self.background = None

        self.updateText +=1

        # redraw the full figure
        self.line.figure.canvas.draw()
        self.released += 1

    def disconnect(self):
        'disconnect all the stored connection ids'
        self.line.figure.canvas.mpl_disconnect(self.cidpress)
        self.line.figure.canvas.mpl_disconnect(self.cidrelease)
        self.line.figure.canvas.mpl_disconnect(self.cidmotion)

    def update_line(self):
        x0, y0, x1, y1, xpress, ypress = self.press
        bt = self.border_tol * (abs(x0-x1)**2 + abs(y0-y1)**2)**0.5

        dx, dy = self.dx, self.dy

        dx, dy = axes_boundery_check([x0,y0],[x1,y1],dx,dy,DraggableResizeableLine.axes_xlim,DraggableResizeableLine.axes_ylim)

        if (abs(x0-xpress)**2+abs(y0-ypress)**2)**0.5<2**0.5*abs(bt): # Check for if mouse close to start (pos 0) of line
            self.line.set_data([x0+dx,x1],[y0+dy,y1])

        elif (abs(x1-xpress)**2+abs(y1-ypress)**2)**0.5<2**0.5*abs(bt): # Check for if mouse close to start (pos 1) of line
            self.line.set_data([x0,x1+dx],[y0,y1+dy])

        elif (abs((x0+x1)/2-xpress)**2+abs((y0+y1)/2-ypress)**2)**0.5<2**0.5*abs(bt): # Make line draggable at center
            self.line.set_data([x0+dx,x1+dx],[y0+dy,y1+dy])

class AnnotatedLine(HasTraits):

    axes = Instance(matplotlib.axes.Axes)
    annotext = Instance(matplotlib.text.Text)
    text = Str()
    drl = Instance(DraggableResizeableLine)
    lineUpdated = Int(0)
    lineReleased = Int(0)

    def __init__(self, axes, x0, y0, x1, y1,text, color = 'k'):#text, color='c', ecolor='k', alpha=0.7):
        print("View: Line created")
        super(AnnotatedLine, self).__init__()
        self.pos_0 = [x0,y0]
        self.pos_1 = [x1,y1]
        self.axes = axes
        self.text = text
        line_handle = self.axes.plot([x0,x1],[y0,y1],color = color)[0]
        self.line = line_handle
        self.drl = DraggableResizeableLine(line_handle)
        self.drl.connect()


    def disconnect(self):
        self.drl.disconnect()

    def connect(self):
        self.drl.connect()

    @on_trait_change('drl.updateText')
    def updateText(self):
        try:
            self.annotext.remove()
        except AttributeError:
            print("AnnotatedRectangle: Found no annotated text")
        x, y = self.line.get_data()
        self.pos_0 = np.array([x[0],y[0]])
        self.pos_1 = np.array([x[1],y[1]])
        self.annotext = self.axes.annotate(self.text, self.pos_1+(self.pos_0-self.pos_1)/2, color='w', weight='bold',fontsize=6, ha='center', va='center')


    @on_trait_change('drl.updateXY')
    def xyLineUpdated(self):
        self.lineUpdated += 1

    @on_trait_change('drl.released')
    def released(self):
        print("AnnotatedRectangle: Rectangle released")
        x, y = self.line.get_data()
        self.pos_0 = np.array([x[0],y[0]])
        self.pos_1 = np.array([x[1],y[1]])
        self.lineReleased += 1

    def get_pos(self):
        return self.pos_0, self.pos_1

    def remove(self):
        self.line.remove()
        self.annotext.remove()
        del self


class DraggableResizeableRectangle(HasTraits):
    """
    Draggable and resizeable rectangle with the animation blit techniques.
    Based on example code at
    http://matplotlib.sourceforge.net/users/event_handling.html
    If *allow_resize* is *True* the recatngle can be resized by dragging its
    lines. *border_tol* specifies how close the pointer has to be to a line for
    the drag to be considered a resize operation. Dragging is still possible by
    clicking the interior of the rectangle. *fixed_aspect_ratio* determines if
    the recatngle keeps its aspect ratio during resize operations.
    """
    updateText = Int(0)
    updateXY = Int(0)
    released = Int(0)

    lock = None  # only one can be animated at a time
    axes_xlim = None # Needed to allow widget to leave boundaries of zoomed in data. Might be unnecessary of matplotlib allows do get the unzoomed axes.
    axes_ylim = None

    @staticmethod
    def reset_borders():
        DraggableResizeableRectangle.axes_xlim = None
        DraggableResizeableRectangle.axes_ylim = None
        print('Reset of DraggableResizableRectangle Border to None')

    def __init__(self, rect, border_tol=.15, allow_resize=True,
                 fixed_aspect_ratio=False):
        self.rect = rect
        self.border_tol = border_tol
        self.allow_resize = allow_resize
        self.fixed_aspect_ratio = fixed_aspect_ratio
        self.press = None
        self.background = None

        if DraggableResizeableRectangle.axes_xlim is None:
            DraggableResizeableRectangle.axes_xlim = self.rect.axes.get_xlim()
        if DraggableResizeableRectangle.axes_ylim is None:
            DraggableResizeableRectangle.axes_ylim = self.rect.axes.get_ylim()

    def connect(self):
        'connect to all the events we need'
        self.cidpress = self.rect.figure.canvas.mpl_connect(
            'button_press_event', self.on_press)
        self.cidrelease = self.rect.figure.canvas.mpl_connect(
            'button_release_event', self.on_release)
        self.cidmotion = self.rect.figure.canvas.mpl_connect(
            'motion_notify_event', self.on_motion)

    def on_press(self, event):
        'on button press we will see if the mouse is over us and store some data'
        if event.inaxes != self.rect.axes: return
        if DraggableResizeableRectangle.lock is not None: return
        contains, attrd = self.rect.contains(event)
        if not contains: return

        if np.abs(self.rect.axes.get_xlim()[0]-self.rect.axes.get_xlim()[1])>np.abs(DraggableResizeableRectangle.axes_xlim[0]-DraggableResizeableRectangle.axes_xlim[1]):
            DraggableResizeableRectangle.axes_xlim = self.rect.axes.get_xlim()

        if np.abs(self.rect.axes.get_ylim()[0]-self.rect.axes.get_ylim()[1])>np.abs(DraggableResizeableRectangle.axes_ylim[0]-DraggableResizeableRectangle.axes_ylim[1]):
            DraggableResizeableRectangle.axes_ylim = self.rect.axes.get_ylim()

        x0, y0 = self.rect.xy
        w0, h0 = self.rect.get_width(), self.rect.get_height()
        aspect_ratio = np.true_divide(w0, h0)
        self.press = x0, y0, w0, h0, aspect_ratio, event.xdata, event.ydata
        DraggableResizeableRectangle.lock = self

        # draw everything but the selected rectangle and store the pixel buffer
        canvas = self.rect.figure.canvas
        axes = self.rect.axes
        self.rect.set_animated(True)
        canvas.draw()
        self.background = canvas.copy_from_bbox(self.rect.axes.bbox)

        # now redraw just the rectangle
        axes.draw_artist(self.rect)

        # and blit just the redrawn area
        canvas.blit(axes.bbox)

    def on_motion(self, event):
        'on motion we will move the rect if the mouse is over us'
        if DraggableResizeableRectangle.lock is not self:
            return
        if event.inaxes != self.rect.axes: return
        x0, y0, w0, h0, aspect_ratio, xpress, ypress = self.press
        self.dx = event.xdata - xpress
        self.dy = event.ydata - ypress


        self.update_rect()

        canvas = self.rect.figure.canvas
        axes = self.rect.axes
        # restore the background region
        canvas.restore_region(self.background)

        # redraw just the current rectangle
        axes.draw_artist(self.rect)

        # blit just the redrawn area
        canvas.blit(axes.bbox)
        self.updateXY += 1

    def on_release(self, event):
        'on release we reset the press data'
        if DraggableResizeableRectangle.lock is not self:
            return

        self.press = None
        DraggableResizeableRectangle.lock = None

        # turn off the rect animation property and reset the background
        self.rect.set_animated(False)
        self.background = None

        self.updateText += 1

        # redraw the full figure
        self.rect.figure.canvas.draw()
        self.released += 1

    def disconnect(self):
        'disconnect all the stored connection ids'
        self.rect.figure.canvas.mpl_disconnect(self.cidpress)
        self.rect.figure.canvas.mpl_disconnect(self.cidrelease)
        self.rect.figure.canvas.mpl_disconnect(self.cidmotion)

    def update_rect(self):
        x0, y0, w0, h0, aspect_ratio, xpress, ypress = self.press
        dx, dy = self.dx, self.dy
        bt = self.border_tol
        fixed_ar = self.fixed_aspect_ratio

        dx, dy = axes_boundery_check([x0,y0],[x0+w0,y0+h0],dx,dy,self.rect.axes.get_xlim(),self.rect.axes.get_ylim())

        if (not self.allow_resize or
            (abs(x0+np.true_divide(w0,2)-xpress)<np.true_divide(w0,2)-bt*w0 and
             abs(y0+np.true_divide(h0,2)-ypress)<np.true_divide(h0,2)-bt*h0)):
            self.rect.set_x(x0+dx)
            self.rect.set_y(y0+dy)
        elif abs(x0-xpress)<bt*w0:
            self.rect.set_x(x0+dx)
            self.rect.set_width(w0-dx)
            if fixed_ar:
                dy = np.true_divide(dx, aspect_ratio)
                self.rect.set_y(y0+dy)
                self.rect.set_height(h0-dy)
        elif abs(x0+w0-xpress)<bt*w0:
            self.rect.set_width(w0+dx)
            if fixed_ar:
                dy = np.true_divide(dx, aspect_ratio)
                self.rect.set_height(h0+dy)
        elif abs(y0-ypress)<bt*h0:
            self.rect.set_y(y0+dy)
            self.rect.set_height(h0-dy)
            if fixed_ar:
                dx = dy*aspect_ratio
                self.rect.set_x(x0+dx)
                self.rect.set_width(w0-dx)
        elif abs(y0+h0-ypress)<bt*h0:
            self.rect.set_height(h0+dy)
            if fixed_ar:
                dx = dy*aspect_ratio
                self.rect.set_width(w0+dx)


class AnnotatedRectangle(HasTraits):
    rectangle = Instance(mpatches.Rectangle)
    axes = Instance(matplotlib.axes.Axes)
    annotext = Instance(matplotlib.text.Text)
    text = Str()
    drr = Instance(DraggableResizeableRectangle)

    rectUpdated = Int(0)
    rectReleased = Int(0)

    def __init__(self, axes, x1, y1, x2, y2, text, color='c', ecolor='k', alpha=0.7):
        print("View: AnnotatedRectangle created")
        super(AnnotatedRectangle, self).__init__()
        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2

        # Rectangle Workaround, because it's not draggable when selecting from top
        if x1 > x2:
            temp = x2
            x2 = x1
            x1 = temp

        if y1 > y2:
            temp = y2
            y2 = y1
            y1 = temp

        xto = x2 - x1
        yto = y2 - y1

        rectangle = mpatches.Rectangle((x1, y1), xto, yto, ec=ecolor, color=color, alpha=alpha)
        self.text = text
        self.axes = axes

        xtext = self.x1 + (self.x2 - self.x1) / 2.
        ytext = self.y1 + (self.y2 - self.y1) / 2.

        self.axes.add_patch(rectangle)
        self.drr = DraggableResizeableRectangle(rectangle)

        self.drr.connect()
        self.rectangle = self.drr.rect


    @on_trait_change('drr.updateText')
    def updateText(self):
        try:
            self.annotext.remove()
        except AttributeError:
            print("AnnotatedRectangle: Found no annotated text")

        x1, y1 = self.drr.rect.get_xy()
        x2 = x1 + self.drr.rect.get_width()/2.0
        y2 = y1 + self.drr.rect.get_height()/2.0

        self.annotext = self.axes.annotate(self.text, (x2, y2), color='w', weight='bold',
                        fontsize=6, ha='center', va='center')

    @on_trait_change('drr.updateXY')
    def xyRectUpdated(self):
        self.rectUpdated += 1

    @on_trait_change('drr.released')
    def released(self):
        print("AnnotatedRectangle: Rectangle released")
        self.x1, self.y1 = self.drr.rect.get_xy()
        self.x2 = self.x1+self.drr.rect.get_width()
        self.y2 = self.y1+self.drr.rect.get_width()
        self.rectReleased += 1

    def remove(self):
        self.rectangle.remove()
        self.annotext.remove()
        del self

    def get_rect_xy(self):
        return self.drr.rect.get_xy()

    def get_rect_width(self):
        return self.drr.rect.get_width()

    def get_rect_height(self):
        return self.drr.rect.get_height()

    def disconnect(self):
        self.drr.disconnect()

    def connect(self):
        self.drr.connect()

if __name__ == '__main__':
    p = mpatches.Rectangle((0.5, 0.5), 0.2, 0.2, ec="k", color='c', alpha=0.7)
    d = DraggableResizeableRectangle(p)
    d.configure_traits()