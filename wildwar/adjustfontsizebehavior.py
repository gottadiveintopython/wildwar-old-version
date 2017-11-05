# -*- coding: utf-8 -*-

r'''Label(SubClassであるButtonも含む)のfont_sizeを自動調節する



使い方(Usage)

from adjustfontsizebehavior import AdjustFontsizeBehavior

class CustomLabel(AdjustFontsizeBehavior, Label):
    pass
label = CustomLabel(text='Hello', adjust_font_size_scaling=0.9)



adjust_font_size_scaling属性を使うことで自動調節のしかたを制御できます。
この値が1(既定値)ならLabelのtextが丁度収まるように調節しますし、1より小さくすればす
る程文字が小さくなり端に余白を作ることになります。そして1より大きくすればする程文字
は大きくなり、Labelからはみ出る事になります。

使う上での注意点があり、まずは自動調節の精度が高くない事です。
adjust_font_size_scalingに1を渡してもはみでる事はありますし、逆にたくさん余白をとっ
てしまう事もあります。特にtextが横にすごく長い時は大きく精度が落ちます。あくまで大雑
把な調節をしてくれる物だと思って下さい。そしてもう一つの注意点はLabelのtext_sizeを
既定値の(None, None, )にしておく必要があるという事です。
'''

from kivy.clock import Clock
from kivy.factory import Factory
from kivy.properties import NumericProperty


__all__ = ('AdjustFontsizeBehavior', )


def _adjust_font_size(label, *, scaling=1.0):
    r"""labelのtextがwidgetの範囲内に収まるようにfont_sizeを調節する関数"""

    texture_width = label.texture_size[0]
    texture_height = label.texture_size[1]
    label_width = label.width
    label_height = label.height
    if label.text == '' or texture_width == 0 or \
            texture_height == 0 or label_width == 0 or label_height == 0:
        return
    texture_aspect_ratio = texture_width / texture_height
    label_aspect_ratio = label_width / label_height
    if texture_aspect_ratio < label_aspect_ratio:
        factor = (label_height / texture_height) * scaling
    else:
        factor = (label_width / texture_width) * scaling
    label.font_size = int(factor * label.font_size)


class AdjustFontsizeBehavior:

    adjust_font_size_scaling = NumericProperty(1)

    def __init__(self, **kwargs):
        self._afb_need_to_update_texture = False
        self._afb_trigger = Clock.create_trigger(
            self._adjust_font_size_callback,
            -1
        )
        super(AdjustFontsizeBehavior, self).__init__(**kwargs)

    def on_text(self, *args):
        self._afb_need_to_update_texture = True
        self._afb_trigger()

    def on_size(self, *args):
        self._afb_trigger()

    def on_adjust_font_size_scaling(self, *args):
        self._afb_trigger()

    def _adjust_font_size_callback(self, *args):
        if self._afb_need_to_update_texture:
            self.texture_update()
            self._afb_need_to_update_texture = False
        _adjust_font_size(self, scaling=self.adjust_font_size_scaling)


Factory.register('AdjustFontsizeBehavior', cls=AdjustFontsizeBehavior)


def _test():
    from kivy.lang import Builder
    from kivy.base import runTouchApp

    root = Builder.load_string(r'''
<CustomLabel@AdjustFontsizeBehavior+Label>:

BoxLayout:
    orientation: 'vertical'
    AnchorLayout:
        size_hint_y: 0.8
        anchor_x: 'center'
        anchor_y: 'center'
        CustomLabel:
            size_hint: 0.5, 0.5
            adjust_font_size_scaling: id_slider.value
            text: id_textinput.text
            canvas.after:
                Color:
                    rgba: 1, 1, 1, 1
                Line:
                    rectangle: self.x, self.y, self.width, self.height
                    dash_offset: 4
                    dash_length: 2
    TextInput:
        size_hint_y: 0.1
        id: id_textinput
        text: 'Morning\nAfternoon\nEvening\nNight'
    BoxLayout:
        size_hint_y: 0.1
        orientation: 'horizontal'
        Slider:
            size_hint_x: 0.8
            id: id_slider
            min: 0.1
            max: 2.0
            step: 0.02
            value: 1.0
        Label:
            size_hint_x: 0.2
            text: 'scaling: {:.3}'.format(id_slider.value)
''')

    runTouchApp(root)


if __name__ == '__main__':
    _test()
