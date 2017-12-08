# -*- coding: utf-8 -*-

__all__ = ('play_stretch_animation', )

# from kivy.config import Config
# Config.set('modules', 'inspector', '')
import math

from kivy.factory import Factory
from kivy.vector import Vector
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics.transformation import Matrix


def play_stretch_animation(
        *, parent, widget, root_pos, head_pos,
        anim_duration=1, on_complete=None):
    r'''parent上のroot_posからhead_posにかけてwidgetが伸びるAnimationを表示する

    :Parameters:
        `parent`:
            widgetの親となるWidget
        `widget`:
            伸ばすAnimation対象のWidget
        `root_pos`: tuple
            widgetの根本の位置
        `head_pos`: tuple
            widgetの先端が向かう位置
        `anim_duration`: int, defaults to 1.
            Animation全体の長さ。この値の半分の時間をかけて矢印はhead_posへ到達し、
            残りの時間も過ぎた時にwidgetが消える。
        `on_complete`: callable, defaults to None.
            Animationが完了した時に呼ばれるcallable

    '''

    vector = Vector(head_pos) - root_pos

    # x軸とvectorの成す角度を弧度法で求めている
    angle = -math.atan2(-vector.y, vector.x)

    scatter = Factory.Scatter(
        do_scale=False,
        do_rotation=False,
        do_translation=False,
        size_hint=(None, None, ))
    scatter.bind(size=widget.setter('size'))
    scatter.add_widget(widget)

    scatter.size = (10, 50, )
    scatter.pos = (0, -25, )
    scatter.apply_transform(Matrix().rotate(angle, 0, 0, 1))
    scatter.apply_transform(Matrix().translate(*root_pos, 0))

    parent.add_widget(scatter)
    animation = Animation(
        width=vector.length(),
        duration=anim_duration / 2)

    def on_animation_complete(__):
        parent.remove_widget(scatter)
        if on_complete:
            on_complete()

    def on_arrow_reached(animation, widget):
        Clock.schedule_once(on_animation_complete, anim_duration / 2)

    animation.bind(on_complete=on_arrow_reached)
    animation.start(scatter)


def _test():
    from kivy.app import runTouchApp
    from kivy.lang import Builder

    root = Builder.load_string(r'''
FloatLayout:
    Widget:
        id: target
        size_hint: 0.6, 0.6
        pos_hint: {'center_x': 0.5, 'center_y': 0.5, }
        canvas:
            Rectangle:
                pos: 98, 198
                size: 3, 3
    ''')

    def on_touch_down(widget, touch):
        play_stretch_animation(
            parent=widget,
            widget=Factory.Button(),
            root_pos=(100, 200, ),
            head_pos=touch.pos,
            anim_duration=2)

    root.bind(on_touch_down=on_touch_down)
    runTouchApp(root)


if __name__ == '__main__':
    _test()
