# -*- coding: utf-8 -*-

__all__ = ('play_arrow_animation', )

# from kivy.config import Config
# Config.set('modules', 'inspector', '')
import math

from kivy.factory import Factory
from kivy.vector import Vector
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics.transformation import Matrix

if __name__ == '__main__':
    from gradientfill import GradientFill
    from gradientpolygon import GradientPolygon
    import sys
    sys.path.append('..')
else:
    from .gradientfill import GradientFill
    from .gradientpolygon import GradientPolygon
from stencilviewex import StencilViewEx


def play_arrow_animation(
        *, parent, root_pos, head_pos, anim_duration=1,
        hexcolors=('ffffff', '008800', '0000ff', ), on_complete=None):
    r'''parent上のroot_posからhead_posにかけて矢印が伸びるAnimationを表示する

    :Parameters:
        `parent`:
            矢印の親となるWidget
        `root_pos`: tuple
            矢印の根本の位置
        `head_pos`: tuple
            矢印の先端が向かう位置
        `anim_duration`: int, defaults to 1.
            Animation全体の長さ。この値の半分の時間をかけて矢印はhead_posへ到達し、
            残りの時間はグラデーションのAnimationのみを行う。
        `hexcolors`: tuple, defaults to ('ffffff', '008800', '0000ff', ).
            矢印を塗りつぶすグラデーションの色
        `on_complete`: callable, defaults to None.
            Animationが完了した時に呼ばれるcallable

    '''
    vector = Vector(head_pos) - root_pos

    # x軸とvectorの成す角度を弧度法で求めている
    angle = -math.atan2(-vector.y, vector.x)

    arrow = GradientPolygon(
        gradientfill=GradientFill(
            n_repeating=3,
            hexcolors=hexcolors),
        stencilviewex=StencilViewEx.create_from_template('arrow2'))
    scatter = Factory.Scatter(
        do_scale=False,
        do_rotation=False,
        do_translation=False,
        size_hint=(None, None, ))
    scatter.bind(size=arrow.setter('size'))
    scatter.add_widget(arrow)

    scatter.size = (10, 50, )
    scatter.pos = (0, -25, )
    scatter.apply_transform(Matrix().rotate(angle, 0, 0, 1))
    scatter.apply_transform(Matrix().translate(*root_pos, 0))

    parent.add_widget(scatter)
    animation = Animation(
        width=vector.length(),
        duration=anim_duration / 2)

    def on_animation_complete(__):
        arrow.stop_animation()
        parent.remove_widget(scatter)
        if on_complete:
            on_complete()

    def on_arrow_reached(animation, widget):
        Clock.schedule_once(on_animation_complete, anim_duration / 2)

    animation.bind(on_complete=on_arrow_reached)
    animation.start(scatter)
    arrow.start_animation()


def _test():
    from kivy.app import runTouchApp
    from kivy.lang import Builder

    root = Builder.load_string(r'''
BoxLayout:
    RelativeLayout:
        id: left_pane
    RelativeLayout:
        id: right_pane
    ''')

    def on_touch_down(widget, touch):
        play_arrow_animation(
            parent=widget.ids.left_pane,
            root_pos=(100, 200, ),
            head_pos=(200, 100, ),
            anim_duration=2)
        play_arrow_animation(
            parent=widget.ids.right_pane,
            root_pos=(100, 200, ),
            head_pos=(200, 100, ),
            anim_duration=2)

    root.bind(on_touch_down=on_touch_down)
    runTouchApp(root)


if __name__ == '__main__':
    _test()
