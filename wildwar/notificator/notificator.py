# -*- coding: utf-8 -*-

__all__ = ('Notificator', )

import sys
import os.path

import kivy
kivy.require(r'1.10.0')
from kivy.atlas import Atlas
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.properties import (
    NumericProperty, StringProperty, ListProperty, ObjectProperty,
    DictProperty,
)

from kivy.garden.magnet import Magnet

DATA_ROOT = os.path.dirname(sys.modules[__name__].__file__)
ATLAS_PATH = os.path.join(DATA_ROOT, 'notificator-icons.atlas')


def fadeout_widget(widget, *, duration=4, transition='in_cubic'):
    def on_complete(animation, widget):
        widget.parent.remove_widget(widget)
    animation = Animation(
        duration=duration,
        transition=transition,
        opacity=0)
    animation.bind(on_complete=on_complete)
    animation.start(widget)


Builder.load_string(r'''
<NotificatorItem>:
    size_hint_y: None
    height: id_boxlayout.height
    canvas.before:
        Color:
            rgba: self.color
        Line:
            points: [self.x, self.y - 2, self.right, self.y]
            dash_offset: 5
            dash_length: 2
            width: 1
    BoxLayout:
        id: id_boxlayout
        orientation: 'horizontal'
        size_hint_y: None
        height: id_label.height
        pos: root.pos
        spacing: 10
        Image:
            texture: root.icon_texture
            size: self.texture_size
            size_hint: None, None
            pos_hint: {'top': 1, }
            # size: self.texture_size
        Label:
            id: id_label
            text: root.text
            font_size: root.font_size
            color: root.color
            outline_color: 0, 0, 0, 1,
            outline_width: 1
            text_size: self.width, None
            size_hint_y: None
            height: self.texture_size[1]
<Notificator>:
    id: id_layout
    orientation: 'vertical'
    spacing: 10
    padding: [2]
''')


class NotificatorItem(Factory.FloatLayout):
    font_size = NumericProperty()
    text = StringProperty()
    color = ListProperty()
    icon_texture = ObjectProperty()


class Notificator(Factory.BoxLayout, Factory.StencilView):
    default_font_size = NumericProperty(16)
    color = ListProperty((1, 1, 1, 1, ))
    icon_texture_dict = DictProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.icon_texture_dict = Atlas(ATLAS_PATH).textures

    def add_notification(
            self, *,
            text,
            font_size=None,
            icon_key='',
            duration='4'):
        item = NotificatorItem(
            text=text,
            icon_texture=self.icon_texture_dict.get(icon_key),
            font_size=(
                self.default_font_size if font_size is None else font_size),
            color=self.color,
            x=self.x,
            top=self.y,
            width=self.width,)
        magnet = Magnet(
            transitions={'pos': 'linear', },
            duration=0.5,
            size_hint_y=None)
        item.bind(height=magnet.setter('height'))
        magnet.add_widget(item)
        self.add_widget(magnet)
        Clock.schedule_once(
            lambda __: fadeout_widget(magnet, duration=2),
            duration)


def _test():
    from kivy.app import runTouchApp
    import random

    notificator = Notificator(
        size_hint=(0.5, 0.5, ),
        pos_hint={'center_x': 0.5, 'center_y': 0.5, },)

    args_tuple = (
        ('information', 'Kivy is awesome!', ),
        ('warning', 'Keep away!', ),
        ('disallowed', 'You can not get in.', ),
        ('lock', 'The chest is locked.', ),
        ('unlock', 'Unlocked the chest.', ),
        ('good', 'Gooood!', ),
        ('wifi', 'Connection is stable.', ),
        ('talk', "What's up.", ),
        ('close', 'This is close icon.', ),
        ('unknown key', 'unknown key', ),
        (None, 'None', ), )

    def on_touch_down_handler(widget, __):
        args = random.choice(args_tuple)
        widget.add_notification(
            text=args[1],
            icon_key=args[0],
            duration=4,
            font_size=20)

    notificator.bind(on_touch_down=on_touch_down_handler)
    root = Factory.FloatLayout()
    root.add_widget(notificator)
    runTouchApp(root)


if __name__ == '__main__':
    _test()
