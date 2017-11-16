# -*- coding: utf-8 -*-

r'''Based on kivy.uix.modalview

kivy.uix.modalview.ModalViewは任意のWidgetを親にする事ができないので、それができる
物を作った。attach_to属性に親にしたいWidgetを指定する。もしNoneを指定した場合は
kivy.core.window.Windowが親になる。
'''
__all__ = (
    'CustomModalViewNoBackground'
)

import kivy
kivy.require(r'1.10.0')
from kivy.config import Config
Config.set('modules', 'inspector', '')
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.properties import (
    ObjectProperty, BooleanProperty, NumericProperty, )
from kivy.animation import Animation


Builder.load_string(r'''
<CustomModalViewNoBackground>:
    pos: self.parent.pos if self.parent else (0, 0, )
    size: self.parent.size if self.parent else (0, 0, )
''')


class CustomModalViewNoBackground(Factory.AnchorLayout):
    attach_to = ObjectProperty(None)
    auto_dismiss = BooleanProperty(True)
    __events__ = ('on_open', 'on_dismiss', )

    def __init__(self, **kwargs):
        kwargs.setdefault('pos_hint', {'x': 0, 'y': 0, })
        super().__init__(**kwargs)

    def open(self, *largs):
        from kivy.core.window import Window
        if self.parent:
            return
        parent = self.attach_to or Window
        self.pos = parent.pos
        self.size = parent.size
        parent.add_widget(self)
        self.dispatch('on_open')

    def dismiss(self, *largs, **kwargs):
        if self.parent is None:
            return
        if self.dispatch('on_dismiss') is True:
            if kwargs.get('force', False) is not True:
                return
        self.parent.remove_widget(self)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            if self.auto_dismiss:
                self.dismiss()
                return True
        super().on_touch_down(touch)
        return True

    def on_touch_move(self, touch):
        super().on_touch_move(touch)
        return True

    def on_touch_up(self, touch):
        super().on_touch_up(touch)
        return True

    def on_open(self):
        pass

    def on_dismiss(self):
        pass


def _test():
    from kivy.base import runTouchApp
    from kivy.core.window import Window

    Window.clearcolor = (.5, .5, 0, 1, )

    root = Builder.load_string(r'''
BoxLayout:
    button: button
    modalviews_parent: modalviews_parent
    Widget:
        Button:
            id: button
            text: 'open modalview'
    # FloatLayout:
    RelativeLayout:
        id: modalviews_parent
    ''')

    def on_press(button):
        label = Factory.Label(
            font_size=40,
            text='Yeah')
        modalview = CustomModalViewNoBackground(attach_to=root.modalviews_parent)
        modalview.add_widget(label)
        modalview.open()
    root.button.bind(on_press=on_press)
    runTouchApp(root)


if __name__ == '__main__':
    _test()
