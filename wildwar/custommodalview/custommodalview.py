# -*- coding: utf-8 -*-

r'''Based on kivy.uix.modalview

kivy.uix.modalview.ModalViewは任意のWidgetを親にする事ができないので、それができる
物を作った。attach_to属性に親にしたいWidgetを指定する。もしNoneを指定した場合は
kivy.core.window.Windowが親になる。
'''
__all__ = (
    'CustomModalView'
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
<CustomModalView>:
    canvas.before:
        Color:
            rgba: 0, 0, 0, self.background_opacity
        Rectangle:
            pos: -self.x, -self.y
            size: self.parent.size if self.parent else (0, 0,)
''')


class CustomModalView(Factory.RelativeLayout):
    attach_to = ObjectProperty(None)
    auto_dismiss = BooleanProperty(True)
    background_opacity = NumericProperty(0)
    animation_duration = NumericProperty(0.1)
    __events__ = ('on_open', 'on_dismiss', )

    def __init__(self, **kwargs):
        kwargs.setdefault('pos_hint', {'center_x': 0.5, 'center_y': 0.5, })
        super().__init__(**kwargs)

    def open(self, *largs):
        from kivy.core.window import Window
        if self.parent:
            return
        self.background_opacity = 0
        parent = self.attach_to or Window
        parent.add_widget(self)
        animation = Animation(
            background_opacity=0.7,
            duration=self.animation_duration)
        animation.bind(on_complete=lambda *__: self.dispatch('on_open'))
        animation.start(self)

    def dismiss(self, *largs, **kwargs):
        if self.parent is None:
            return
        if self.dispatch('on_dismiss') is True:
            if kwargs.get('force', False) is not True:
                return
        animation = Animation(
            background_opacity=0,
            duration=self.animation_duration)

        def on_complete(*args):
            parent = self.parent
            if parent:
                parent.remove_widget(self)
        animation.bind(on_complete=on_complete)
        animation.start(self)

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
<Widget>:
    canvas.after:
        Line:
            rectangle: self.x+1,self.y+1,self.width-1,self.height-1
            dash_offset: 5
            dash_length: 3
BoxLayout:
    button: button
    modalviews_parent: modalviews_parent
    Widget:
        Button:
            id: button
            text: 'open modalview'
    # FloatLayout:
    RelativeLayout:
        RelativeLayout:
            size_hint: 0.9, 0.9
            pos_hint: dict(center_x=0.5, center_y=0.5, )
            id: modalviews_parent
    ''')

    def on_press(button):
        label = Factory.Label(
            font_size=40,
            text='Yeah')
        # modalview = CustomModalView(
        #     attach_to=root.modalviews_parent)
        modalview = CustomModalView(
            attach_to=root.modalviews_parent,
            size_hint=(0.5, 0.5, ))
        modalview.add_widget(label)
        modalview.open()
    root.button.bind(on_press=on_press)
    runTouchApp(root)


if __name__ == '__main__':
    _test()
