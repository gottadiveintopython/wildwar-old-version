# -*- coding: utf-8 -*-

r'''Based on kivy.uix.behaviors.drag.DragBehavior

DragBehaviorを元にして作ったClass。DragBehaviorとは違いWidgetの移動は行わず、ただ
Drag入力が行われた事を通知するだけである。またdrag_rectangleプロパティを持っておら
ず、Widget全域がDragを感知する領域になっている。
'''


__all__ = ('DragRecognizer', )

from functools import partial

from kivy.clock import Clock
from kivy.properties import NumericProperty
from kivy.config import Config
from kivy.metrics import sp
from kivy.factory import Factory

_scroll_timeout = _scroll_distance = 0
if Config:
    _scroll_timeout = Config.getint('widgets', 'scroll_timeout')
    _scroll_distance = Config.getint('widgets', 'scroll_distance')


class DragRecognizer(object):

    drag_distance = NumericProperty(_scroll_distance)
    drag_timeout = NumericProperty(_scroll_timeout)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type('on_drag_start')
        self.register_event_type('on_being_dragged')
        self.register_event_type('on_drag_finish')
        # Don't use self.__class__.__name__ instead of 'DragRecognizer.'
        self.__ud_key = 'DragRecognizer.' + str(self.uid)

    def on_drag_start(self, touch):
        pass

    def on_being_dragged(self, touch):
        pass

    def on_drag_finish(self, touch):
        pass

    def _rest_of_brothers(self):
        brothers = self.parent.children
        return brothers[brothers.index(self) + 1:]

    def on_touch_down(self, touch):
        # print('DragRecognizer on_touch_down', touch.pos)
        # if not self.collide_point(*touch.pos):
        if not self.collide_point(*touch.pos) or touch.is_mouse_scrolling:
            touch.ud[self.__ud_key] = None
            # print('Marked as non-drag touch.', touch.pos)
            return super().on_touch_down(touch)

        # no mouse scrolling, so the user is going to drag with this touch.
        touch.grab(self)
        touch.ud[self.__ud_key] = {
            'mode': 'unknown',
            'dx': 0,
            'dy': 0, }
        Clock.schedule_once(partial(self._change_touch_mode, touch),
                            self.drag_timeout / 1000.)
        return True

    def on_touch_move(self, touch):
        ud = touch.ud.get(self.__ud_key)
        if ud is None:
            return super().on_touch_move(touch)
        if touch.grab_current is not self:
            return True
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
            self.dispatch(r'on_being_dragged', touch)
        return True

    def on_touch_up(self, touch):
        # print('DragRecognizer on_touch_up', touch.pos, touch.grab_current)
        # import pdb;pdb.set_trace()
        ud_key = self.__ud_key
        ud = touch.ud.get(ud_key)
        if ud is None:
            return super().on_touch_up(touch)

        if touch.grab_current is self:
            touch.ungrab(self)
            if ud['mode'] == 'unknown':
                touch.ud[ud_key] = None
                touch.grab_current = None
                super().on_touch_down(touch)
                for brother in self._rest_of_brothers():
                    # print(brother, 'on_touch_down')
                    brother.on_touch_down(touch)
                touch.grab_current = self
                Clock.schedule_once(partial(self._do_touch_up, touch), 0)
            else:
                self.dispatch(r'on_drag_finish', touch)
        else:
            pass
        return True

    def _do_touch_up(self, touch, *largs):
        # print('DragRecognizer _do_touch_up')
        # don't forget about grab event!
        # print('[----grab_list----')
        for x in touch.grab_list[:]:
            touch.grab_list.remove(x)
            x = x()
            if not x:
                continue
            touch.grab_current = x
            touch.push()
            touch.apply_transform_2d(x.parent.to_widget)
            x.on_touch_up(touch)
            touch.pop()
        touch.grab_current = None
        # print('----grab_list----]')
        touch.push()
        touch.apply_transform_2d(self.parent.to_widget)
        super().on_touch_up(touch)
        for brother in self._rest_of_brothers():
            brother.on_touch_up(touch)
        touch.pop()

    def _change_touch_mode(self, touch, *largs):
        # print('DragRecognizer _change_touch_mode')
        ud_key = self.__ud_key
        ud = touch.ud.get(ud_key)
        if ud is None or ud['mode'] != 'unknown':
            return
        touch.ungrab(self)
        touch.ud[ud_key] = None
        touch.push()
        touch.apply_transform_2d(self.parent.to_widget)
        # print('DragRecognizer Marked as non-drag touch.', touch.pos)
        super().on_touch_down(touch)
        for brother in self._rest_of_brothers():
            brother.on_touch_down(touch)
        touch.pop()
        return


Factory.register('DragRecognizer', cls=DragRecognizer)


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

<DragRecognizerWidget@DragRecognizer+Label>:

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
