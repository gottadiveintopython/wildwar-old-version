# -*- coding: utf-8 -*-

r"""
"""

__all__ = ('UnitPrototypeDetailViewer', )

import kivy
kivy.require(r'1.10.0')
from kivy.factory import Factory
from kivy.lang import Builder
# from kivy.properties import NumericProperty

from basicwidgets import AutoLabel, RectangleBackground, replace_widget


Builder.load_string(r'''
#:set CARD_ASPECT_RATIO 0.7
#:set BORDER_WIDTH 2
#:set BACKGROUND_COLOR 0, 0, 0, 0.7
#:set BORDER_COLOR 1, 1, 1, 0.2
<Label4DetailViewer@Label+RectangleBackground>:
<AutoLabel4DetailViewer@AutoLabel+RectangleBackground>:

<UnitPrototypeDetailViewer>:
    BoxLayout:
        spacing: 10
        BoxLayout:
            size_hint_x: 1.2
            orientation: 'vertical'
            spacing: 10
            AutoLabel4DetailViewer:
                border_color: BORDER_COLOR
                background_color: BACKGROUND_COLOR
                size_hint_y: 0.2
                text: root.prototype.name
            Widget
                id: id_dummy
        Label4DetailViewer:
            border_color: BORDER_COLOR
            background_color: BACKGROUND_COLOR
            padding_x: 10
            id: id_label_detail
            font_size: self.width / 10
            text_size: self.width, None
            # height: self.texture_size[1]
''')


class UnitPrototypeDetailViewer(Factory.RelativeLayout):

    def __init__(
            self, *, prototype, widget=None, localize_str,
            tag_translation_dict, skill_dict, **kwargs):
        self.prototype = prototype
        super().__init__(**kwargs)
        translated_tags = [tag_translation_dict[tag] for tag in prototype.tag_list]
        if len(translated_tags) == 0:
            translated_tags.append(localize_str('無し'))
        skill_names = [skill_dict[skill_id].name for skill_id in prototype.skill_id_list]
        if len(skill_names) == 0:
            skill_names.append(localize_str('無し'))
        self.ids.id_label_detail.text = '{}:\n  {}\n{}:\n  {}\n\n{}'.format(
            localize_str('Tag'),
            '\n  '.join(translated_tags),
            localize_str('技能'),
            '\n  '.join(skill_names),
            prototype.description)
        if widget:
            replace_widget(self.ids.id_dummy, widget)
