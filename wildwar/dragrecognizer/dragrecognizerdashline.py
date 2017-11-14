# -*- coding: utf-8 -*-

r'''Drag時に破線を引くようにしたDragRecognizer'''

__all__ = ('DragRecognizerDashLine', )


from kivy.factory import Factory
from kivy.graphics import Line, Color

try:
    from .dragrecognizer import DragRecognizer
except ImportError:
    from dragrecognizer import DragRecognizer


class DragRecognizerDashLine(DragRecognizer):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Don't use self.__class__.__name__ instead of 'DragRecognizerDashLine.'
        self.__ud_key = 'DragRecognizerDashLine.' + str(self.uid)

    def on_drag_start(self, touch):
        inst_list = [
            Color([1, 1, 1, 1]),
            Line(
                points=[touch.ox, touch.oy, touch.ox, touch.oy, ],
                dash_length=4,
                dash_offset=8
            )
        ]
        for inst in inst_list:
            self.canvas.after.add(inst)
        touch.ud[self.__ud_key] = {'inst_list': inst_list, }

    def on_being_dragged(self, touch):
        ud = touch.ud[self.__ud_key]

        line = ud['inst_list'][1]
        points = line.points
        points[2] += touch.dx
        points[3] += touch.dy
        line.points = points

    def on_drag_finish(self, touch):
        ud = touch.ud[self.__ud_key]

        inst_list = ud[r'inst_list']
        for inst in inst_list:
            self.canvas.after.remove(inst)


Factory.register('DragRecognizerDashLine', cls=DragRecognizerDashLine)


def _test():

    from kivy.base import runTouchApp
    from kivy.lang import Builder

    root = Builder.load_string(r'''
<Widget>:
    canvas.after:
        Line:
            rectangle: self.x+1,self.y+1,self.width-1,self.height-1
            dash_offset: 5
            dash_length: 3

<CustomButton@Button>:
    font_size: 100
    on_touch_down: print('Button', self.text, 'on_touch_down', args[1].pos, args[1].grab_current)
    on_touch_up: print('Button', self.text, 'on_touch_up', args[1].pos, args[1].grab_current)
    on_press: print('Button', self.text, 'on_press')
    on_release: print('Button', self.text, 'on_release')

<DragRecognizerWidget@DragRecognizerDashLine+Label>:

BoxLayout:
    on_touch_down: print('------------------------------------------------')
    Widget:
    RelativeLayout:
        CustomButton:
            text: 'A'
            pos_hint: {'x': 0.05, 'top': 0.95, }
            size_hint: .3, .3
        DragRecognizerWidget:
            text: 'draggable area'
            pos_hint: {'center_x': 0.5, 'center_y': 0.5, }
            size_hint: .6, .8
            on_drag_start: print('on_drag_start', args[1].pos)
            on_being_dragged: print('on_being_dragged', args[1].pos)
            on_drag_finish: print('on_drag_finish', args[1].pos)
        CustomButton:
            text: 'B'
            pos_hint: {'right': 0.95, 'y': 0.05, }
            size_hint: .3, .3
    ''')
    runTouchApp(root)


if __name__ == '__main__':
    _test()
