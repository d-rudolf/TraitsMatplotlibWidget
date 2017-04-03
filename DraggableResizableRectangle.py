

import numpy as np

from traits.api import HasTraits, Instance, Any, Str, on_trait_change, Int, Event
import matplotlib.patches as mpatches
import matplotlib

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
    def __init__(self, rect, border_tol=.15, allow_resize=True,
                 fixed_aspect_ratio=False):
        self.rect = rect
        self.border_tol = border_tol
        self.allow_resize = allow_resize
        self.fixed_aspect_ratio = fixed_aspect_ratio
        self.press = None
        self.background = None


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
        #print 'event contains', self.rect.xy
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
        #self.rect.set_x(x0+dx)
        #self.rect.set_y(y0+dy)

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


if __name__ == '__main__':
    p = mpatches.Rectangle((0.5, 0.5), 0.2, 0.2, ec="k", color='c', alpha=0.7)
    d = DraggableResizeableRectangle(p)
    d.configure_traits()