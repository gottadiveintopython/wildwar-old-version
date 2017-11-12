# -*- coding: utf-8 -*-

r'''Based on kivy.uix.behaviors.drag.DragBehavior

DragBehaviorを元にして作ったClass。DragBehaviorとは違いWidgetの移動は行わず、ただ
Drag入力が行われた事を通知するだけである。またdrag_rectangleプロパティを持っておら
ず、Widget全域がDrag入力可能な領域になっている。
'''


__all__ = ('DragRecognizer', )

from kivy.clock import Clock
from kivy.properties import NumericProperty
from kivy.config import Config
from kivy.metrics import sp
from functools import partial

_scroll_timeout = _scroll_distance = 0
if Config:
    _scroll_timeout = Config.getint('widgets', 'scroll_timeout')
    _scroll_distance = Config.getint('widgets', 'scroll_distance')


class DragRecognizer(object):

    drag_distance = NumericProperty(_scroll_distance)
    drag_timeout = NumericProperty(_scroll_timeout)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type(r'on_drag_start')
        self.register_event_type(r'on_being_dragged')
        self.register_event_type(r'on_drag_finish')
        self._touch_dict = {}

    def on_drag_start(self, touch):
        pass

    def on_being_dragged(self, touch):
        pass

    def on_drag_finish(self, touch):
        pass

    def _get_uid(self, prefix='sv'):
        return '{0}.{1}'.format(prefix, self.uid)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            touch.ud[self._get_uid('svavoid')] = True
            return super(DragRecognizer, self).on_touch_down(touch)
        if touch.is_mouse_scrolling:
            return super(DragRecognizer, self).on_touch_down(touch)

        # no mouse scrolling, so the user is going to drag with this touch.
        self._touch_dict[touch.uid] = touch
        uid = self._get_uid()
        touch.grab(self)
        touch.ud[uid] = {
            'mode': 'unknown',
            'dx': 0,
            'dy': 0}
        Clock.schedule_once(partial(self._change_touch_mode, touch),
                            self.drag_timeout / 1000.)
        return True

    def on_touch_move(self, touch):
        if self._get_uid('svavoid') in touch.ud or\
                touch.uid not in self._touch_dict:
            return super(DragRecognizer, self).on_touch_move(touch) or\
                self._get_uid() in touch.ud
        if touch.grab_current is not self:
            return True
        uid = self._get_uid()
        ud = touch.ud[uid]
        mode = ud['mode']
        if mode == 'unknown':
            ud['dx'] += abs(touch.dx)
            ud['dy'] += abs(touch.dy)
            condition1 = ud['dx'] > sp(self.drag_distance)
            condition2 = ud['dy'] > sp(self.drag_distance)
            if condition1 or condition2:
                mode = 'drag'
                self.dispatch(r'on_drag_start', touch)
            ud['mode'] = mode
        if mode == 'drag':
            # self.x += touch.dx
            # self.y += touch.dy
            self.dispatch(r'on_being_dragged', touch)
        return True

    def on_touch_up(self, touch):
        if self._get_uid('svavoid') in touch.ud:
            return super(DragRecognizer, self).on_touch_up(touch)

        if touch.grab_current is self:
            touch.ungrab(self)
            del self._touch_dict[touch.uid]
            ud = touch.ud[self._get_uid()]
            if ud['mode'] == 'unknown':
                super(DragRecognizer, self).on_touch_down(touch)
                Clock.schedule_once(partial(self._do_touch_up, touch), .1)
            else:
                self.dispatch(r'on_drag_finish', touch)
        else:
            if touch.uid not in self._touch_dict:
                super(DragRecognizer, self).on_touch_up(touch)
        return self._get_uid() in touch.ud

    def _do_touch_up(self, touch, *largs):
        super(DragRecognizer, self).on_touch_up(touch)
        # don't forget about grab event!
        for x in touch.grab_list[:]:
            touch.grab_list.remove(x)
            x = x()
            if not x:
                continue
            touch.grab_current = x
            super(DragRecognizer, self).on_touch_up(touch)
        touch.grab_current = None

    def _change_touch_mode(self, touch, *largs):
        if touch.uid not in self._touch_dict:
            return
        uid = self._get_uid()
        touch = self._touch_dict[touch.uid]
        ud = touch.ud[uid]
        if ud['mode'] != 'unknown':
            return
        touch.ungrab(self)
        del self._touch_dict[touch.uid]
        super(DragRecognizer, self).on_touch_down(touch)
        return


def _test():

    from kivy.base import runTouchApp
    from kivy.factory import Factory
    from kivy.lang import Builder
    from kivy.graphics import Color, Line

    class DragRecognizerTest(DragRecognizer, Factory.RelativeLayout):

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self._ud_key = self._get_uid(self.__class__.__name__)
            print(self._ud_key)

        def on_drag_start(self, touch):
            # print(r'on_drag_start :', touch.opos)
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
            touch.ud[self._ud_key] = {
                r'inst_list': inst_list,
            }

        def on_being_dragged(self, touch):
            # print(r'on_being_dragged :', touch.pos)
            ud = touch.ud[self._ud_key]

            line = ud[r'inst_list'][1]
            points = line.points
            points[2] += touch.dx
            points[3] += touch.dy
            line.points = points

        def on_drag_finish(self, touch):
            # print(r'on_drag_finish :', touch.pos)
            ud = touch.ud[self._ud_key]

            inst_list = ud[r'inst_list']
            for inst in inst_list:
                self.canvas.after.remove(inst)
            del touch.ud[self._ud_key]

    root = Builder.load_string(r'''
<Widget>:
    canvas.after:
        Line:
            rectangle: self.x+1,self.y+1,self.width-1,self.height-1
            dash_offset: 5
            dash_length: 3

<Label>:
    font_size: 40

<CustomButton@Button>:
    size_hint: None, None
    pos: 50, 50
    on_touch_down: print(self.text, 'on_touch_down', str(args[1].pos))
    on_press: print(self.text, 'on_press')


GridLayout:
    on_touch_down: print('----------------------------------------------------')
    cols: 2
    DragRecognizerTest:
        CustomButton:
            text: 'A'
    DragRecognizerTest:
        CustomButton:
            text: 'B'
        # Widget:
        #     size_hint: None, None
        #     pos: 100, 100
        #     on_touch_down:
        #         print(args[1].pos)
        #         if self.collide_point(*args[1].pos): print('collision')
    DragRecognizerTest:
        CustomButton:
            text: 'C'
    DragRecognizerTest:
        CustomButton:
            text: 'D'
    ''')
    runTouchApp(root)


if __name__ == '__main__':
    _test()
