# -*- coding: utf-8 -*-

from kivy.config import Config
Config.set('modules', 'inspector', '')

from kivy.app import runTouchApp
from kivy.lang import Builder
from kivy.factory import Factory


class GradientPolygon(Factory.Scatter):

    def __init__(self, *, gradientfill, stencilviewex, **kwargs):
        super().__init__(**kwargs)
        stencilviewex.bind(pos=gradientfill.setter('pos'))
        stencilviewex.bind(size=gradientfill.setter('size'))
        stencilviewex.add_widget(gradientfill)
        self.bind(size=stencilviewex.setter('size'))
        self.add_widget(stencilviewex)
        self._gradientfill = gradientfill

    def start_animation(self):
        self._gradientfill.start_animation()

    def stop_animation(self):
        self._gradientfill.stop_animation()


# if __name__ == '__main__':
#     root = Builder.load_string(r'''
# BoxLayout:
#     orientation: 'vertical'
#     RelativeLayout:
#         size_hint_y: 0.9
#         GradientPolygon:
#             # do_scale: False
#             id: id_gradient
#             size_hint: None, None
#             size: 300, 300
#             # pos: 100, 100
#     BoxLayout:
#         size_hint_y: 0.1
#         spacing: 5
#         padding: 5
#         Button:
#             text: 'start animation'
#             on_press: id_gradient.start_animation()
#         Button:
#             text: 'stop animation'
#             on_press: id_gradient.stop_animation()
#         Button:
#             text: 'change size'
#             on_press: id_gradient.size = (300, 100, )
#     ''')
#     runTouchApp(root)
