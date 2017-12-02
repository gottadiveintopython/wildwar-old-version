# -*- coding: utf-8 -*-

__all__ = ('StencilViewEx', )

r'''StencilViewとは違って任意の多角形で切り抜ける


例:子Widgetの描画を二等辺三角形で切り抜く

StencilViewEx:
    mesh_points: (0, 0, ), (0.5, 1, ), (1, 0, )
    mesh_indices: range(3)
    mesh_mode: 'triangles'
    Button:
        text: 'AAAAAAA'
        font_size: 40
        size: root.size
'''

from kivy.app import runTouchApp
from kivy.lang import Builder
from kivy.factory import Factory
from kivy.clock import Clock
from kivy.properties import StringProperty, ListProperty


Builder.load_string(r'''
<StencilViewEx>:
    canvas:
        StencilPush:
        Mesh:
            vertices: self.mesh_vertices
            indices: self.mesh_indices
            mode: self.mesh_mode
        StencilUse:
    canvas.after:
        StencilUnUse:
        StencilPop:
''')


TEMPLATE_DICT = {
    'arrow1': {
        'mesh_points': (
            (0.0, 0.3, ),
            (0.0, 0.7, ),
            (0.7, 0.3, ),
            (0.7, 0.7, ),
            (0.7, 0.0, ),
            (0.7, 1.0, ),
            (1.0, 0.5, ),
        ),
        'mesh_indices': (
            0, 1, 2, 1, 2, 3, 4, 5, 6,
        ),
        'mesh_mode': 'triangles',
    },
    'arrow2': {
        'mesh_points': (
            (0.0, 0.5, ),
            (0.7, 0.3, ),
            (0.7, 0.7, ),
            (0.7, 0.0, ),
            (0.7, 1.0, ),
            (1.0, 0.5, ),
        ),
        'mesh_indices': (
            0, 1, 2, 3, 4, 5,
        ),
        'mesh_mode': 'triangles',
    },
}


class StencilViewEx(Factory.Widget):

    mesh_points = ListProperty()
    r'''Maskを形作る頂点Data

    ((x1, y1, ), (x2, x2, ), ...) の形式で値を入れる。座標の原点はこのWidgetの左下
    で、xはこのWidgetの幅を1とした時の割合、yはこのWidgetの高さを1とした時の割合で
    入れる。
    '''

    mesh_indices = ListProperty()
    r'''この属性の意味はcanvas命令'Mesh'のindicesと同じ'''

    mesh_mode = StringProperty()
    r'''この属性の意味はcanvas命令'Mesh'のmodeと同じ'''

    mesh_vertices = ListProperty()
    r'''(internal) canvasのMesh命令の引数verticesにこの値が渡される。

    mesh_points, size, posが変化する度にこの値は自動的に更新されるので、直接扱って
    はいけない。'''

    @staticmethod
    def create_from_template(name):
        return StencilViewEx(**TEMPLATE_DICT[name])

    def __init__(self, **kwargs):
        self._update_vertices_trigger = \
            Clock.create_trigger(self._update_vertices, -1)
        super().__init__(**kwargs)

    def _update_vertices(self, __):
        points = self.mesh_points
        # print('points', points)
        vertices = self.mesh_vertices
        if (len(vertices) // 4) < len(points):
            vertices = [0, ] * (len(points) * 4)
        x, y = self.pos
        width, height = self.size

        for i, (sx, sy, ) in enumerate(points):
            vertices[i * 4] = sx * width + x
            vertices[i * 4 + 1] = sy * height + y
        self.mesh_vertices = vertices
        # print('vertices', vertices)

    def on_mesh_points(self, __, value):
        self._update_vertices_trigger()

    def on_size(self, __, value):
        self._update_vertices_trigger()

    def on_pos(self, __, value):
        self._update_vertices_trigger()


def _test():
    root = StencilViewEx.create_from_template('arrow2')
    button = Factory.Button(
        text='All your base are belong to us.',
        font_size=40)
    root.bind(size=button.setter('size'))
    root.bind(pos=button.setter('pos'))
    root.add_widget(button)
    runTouchApp(root)

# if __name__ == '__main__':
#     root = Builder.load_string(r'''
# FloatLayout:
#     StencilViewEx:
#         pos: 30, 30
#         size: 300, 300
#         size_hint: None, None
#         mesh_points: (0, 0, ), (0.5, 1, ), (1, 0, ), (0.7, 1, ), (1.2, 0, ), (1.7, 1, ), (1.4, 0, ), (1.9, 1, ), (2.5, 0, ),
#         mesh_indices: range(9)
#         mesh_mode: 'triangles'
#         Button:
#             text: 'All your base are belong to us.'
#             font_size: 40
#             size: root.size
#     ''')
#     runTouchApp(root)


if __name__ == '__main__':
    _test()
