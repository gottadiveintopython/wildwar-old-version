# -*- coding: utf-8 -*-

r"""
"""

__all__ = ('UnitInstanceDetailViewer', )

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

<UnitInstanceDetailViewer>:
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


class UnitInstanceDetailViewer(Factory.RelativeLayout):

    def __init__(
            self, *, uniti, prototype, widget=None, localize_str,
            tag_translation_dict, skill_dict, **kwargs):
        self.uniti = uniti
        self.prototype = prototype
        super().__init__(**kwargs)
        lcstr = localize_str
        translated_tags = [tag_translation_dict[tag] for tag in uniti.tag_list]
        if len(translated_tags) == 0:
            translated_tags.append(lcstr('無し'))
        skill_names = [skill_dict[skill_id].name for skill_id in uniti.skill_id_list]
        if len(skill_names) == 0:
            skill_names.append(lcstr('無し'))
        n_turns_until_movable = uniti.n_turns_until_movable
        self.ids.id_label_detail.text = r'''
{}

{}:
  {}
{}:
  {}

{}:
  {}: {}
  {}: {}
  {}: {}


{}'''.format(
            lcstr('行動可能') if n_turns_until_movable == 0
            else lcstr('行動可能まで{}turn').format(n_turns_until_movable),

            lcstr('Tag'),
            '\n  '.join(translated_tags),
            lcstr('技能'),
            '\n  '.join(skill_names),
            lcstr('元のStats'),
            lcstr('攻撃力'),
            uniti.o_attack,
            lcstr('基本値'),
            uniti.o_power,
            lcstr('防御力'),
            uniti.o_defense,
            prototype.description)
        if widget:
            replace_widget(self.ids.id_dummy, widget)
