# -*- coding: utf-8 -*-

__all__ = ('Timer', )

if __name__ == '__main__':
    import os
    import sys
    sys.path.insert(0, os.path.abspath('..'))

import kivy
kivy.require(r'1.10.0')
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.factory import Factory
from kivy.properties import (
    NumericProperty, ListProperty,
)

import setup_logging
logger = setup_logging.get_logger(__name__)


Builder.load_string(r"""
#:kivy 1.10.0

<CircleDrawer>:
    _radius: min(*self.size) / 2 - self.line_width
    canvas:
        Color:
            rgba: self.color
        Line:
            circle:
                (self.center_x, self.center_y, self._radius,
                self.angle_start, self.angle_end, 30, )
            width: self.line_width
            cap: 'none'
            # close: True
<Timer>:
    int_current_time: int(self.current_time)
    CircleDrawer:
        pos: root.pos
        size: root.size
        color: root.color
        line_width: root.line_width
        angle_start: 0
        angle_end: root.current_time / root.time_limit * 360 + 1

""")


class CircleDrawer(Factory.Widget):
    color = ListProperty((1, 1, 1, 1, ))
    angle_start = NumericProperty(0)
    angle_end = NumericProperty(360)
    line_width = NumericProperty(1)
    _radius = NumericProperty()


class Timer(Factory.Widget):
    color = ListProperty((1, 1, 1, 1, ))
    line_width = NumericProperty(1)
    time_limit = NumericProperty(10)
    current_time = NumericProperty()
    int_current_time = NumericProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._clock_event = None

    def start(self):
        if self._clock_event is None:
            self.current_time = 0
            self._clock_event = Clock.schedule_interval(
                self._clock_callback, 0.1)
        else:
            logger.debug('Timer is already running.')

    def stop(self):
        if self._clock_event is None:
            pass
        else:
            self._clock_event.cancel()
            self._clock_event = None

    def _clock_callback(self, dt):
        self.current_time = min(self.time_limit, self.current_time + dt)
        if self.current_time >= self.time_limit:
            self.stop()


def _test_ClockDrawer():
    from kivy.app import runTouchApp

    root = CircleDrawer(angle_start=30, angle_end=180)
    runTouchApp(root)


def _test_Timer():
    from kivy.app import runTouchApp

    root = Builder.load_string(r'''
BoxLayout:
    orientation: 'vertical'
    Timer:
        id: id_timer
        size_hint_y: 0.9
        time_limit: 10
        line_width: 20
    BoxLayout:
        size_hint_y: 0.1
        spacing: 10
        Button:
            text: 'Start'
            on_press: id_timer.start()
        Button:
            text: 'Stop'
            on_press: id_timer.stop()
    ''')
    runTouchApp(root)


if __name__ == '__main__':
    _test_Timer()