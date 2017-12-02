# -*- coding: utf-8 -*-

r'''横方向のグラデーションで自身を塗りつぶすWidget
'''

__all__ = ('GradientFill', )


from kivy.app import runTouchApp
from kivy.lang import Builder
from kivy.factory import Factory
from kivy.clock import Clock
from kivy.properties import ObjectProperty, ListProperty, NumericProperty
from kivy.graphics.texture import Texture


Builder.load_string(r'''
<GradientFill>:
    canvas:
        Mesh:
            vertices: self.vertices
            indices: 0, 1, 2, 3
            mode: 'triangle_strip'
            texture: self.texture
''')


class GradientFill(Factory.Widget):

    n_repeating = NumericProperty(1)
    r'''Textureを敷き詰める回数

    数を増やすほど、細かい縞模様になる
    '''

    hexcolors = ListProperty()
    r'''Gradationに使う色のlist

    例: 赤緑白のGradation  ['ff0000', '00ff00', 'ffffff', ]
    '''

    texture = ObjectProperty()
    r'''(internal) 敷き詰めるTexture'''

    vertices = ListProperty([0, ] * 16)
    r'''(internal) 長方形の頂点Data

    16は、頂点1つあたりの要素数4(x, y, u, v, )に頂点の数4を掛けた値
    '''

    def __init__(self, **kwargs):
        self._clock_event = None
        self._update_xy_trigger = \
            Clock.create_trigger(self._update_xy, -1)
        kwargs.setdefault('n_repeating', 1)
        kwargs.setdefault('hexcolors', ('ff0000', '00ff00', '0000ff', ))
        super().__init__(**kwargs)

    def on_pos(self, __, value):
        self._update_xy_trigger()

    def on_size(self, __, value):
        self._update_xy_trigger()

    def _update_xy(self, __):
        width, height = self.size
        x, y = self.pos
        vertices = self.vertices
        vertices[0:2] = self.pos
        vertices[4:6] = (x, y + height, )
        vertices[8:10] = (x + width, y, )
        vertices[12:14] = (x + width, y + height, )

    def on_n_repeating(self, __, value):
        vertices = self.vertices
        vertices[2:4] = (0, 0, )
        vertices[6:8] = (0, 1, )
        vertices[10:12] = (value, 0, )
        vertices[14:16] = (value, 1, )

    def on_hexcolors(self, __, hexcolors):
        texture = Texture.create(size=(len(hexcolors), 1, ), colorfmt='rgb')
        texture.wrap = 'repeat'
        buf = b''.join(bytes.fromhex(hexcolor) for hexcolor in hexcolors)
        texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
        self.texture = texture

    def start_animation(self, timeout=0):
        if self._clock_event is None:
            self._clock_event = \
                Clock.schedule_interval(self._progress_animation, timeout)

    def stop_animation(self):
        if self._clock_event is not None:
            self._clock_event.cancel()
            self._clock_event = None

    def _progress_animation(self, deltatime):
        vertices = self.vertices
        for i in range(2, 16, 4):
            vertices[i] -= deltatime


def _test():
    root = Builder.load_string(r'''
<Label>:
    font_size: 20

BoxLayout:
    orientation: 'vertical'
    GradientFill:
        size_hint_y: 0.9
        id: id_gradientrectangle
        hexcolors: 'dd0000', '00dd00', '000000'
        n_repeating: int(id_spinner.text)
    BoxLayout:
        size_hint_y: 0.1
        spacing: 5
        padding: 5
        Button:
            text: 'start animation'
            on_press: id_gradientrectangle.start_animation()
        Button:
            text: 'stop animation'
            on_press: id_gradientrectangle.stop_animation()
        Spinner:
            id: id_spinner
            text: '2'
            values: [str(i) for i in range(1, 10)]
    ''')
    runTouchApp(root)


if __name__ == '__main__':
    _test()
