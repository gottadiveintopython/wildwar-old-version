# -*- coding: utf-8 -*-

__all__ = ('BgmPlayer', )

from kivy.core.audio import SoundLoader


class BgmPlayer:

    def __init__(self, soundfile_dict, *, cache=False):
        self.info_dict = {
            key: {
                'filename': filename,
                'offset': 0,
                'sound': None, }
            for key, filename in soundfile_dict.items()}
        self.current = None
        self.cache = cache

    def play(self, key, *, save_previous_bgm_offset=False):
        current = self.current
        if current == key:
            return
        if current:
            if save_previous_bgm_offset:
                self._pause(current)
            else:
                self._stop(current)
        self._play(key)
        self.current = key

    def stop(self):
        current = self.current
        if current:
            self._stop(current)
        self.current = None

    def pause(self):
        current = self.current
        if current:
            self._pause(current)
        self.current = None

    def _play(self, key):
        info = self.info_dict[key]
        sound = info.get('sound')
        if sound:
            if sound.state == 'stop':
                sound.play()
                sound.seek(info['offset'])
        else:
            info['sound'] = sound = SoundLoader.load(info['filename'])
            sound.loop = True
            sound.play()
            sound.seek(info['offset'])

    def _stop(self, key):
        info = self.info_dict[key]
        sound = info.get('sound')
        if sound:
            if sound.state == 'play':
                sound.stop()
            info['offset'] = 0
            if not self.cache:
                sound.unload()
                info['sound'] = None

    def _pause(self, key):
        info = self.info_dict[key]
        sound = info.get('sound')
        if sound:
            if sound.state == 'play':
                info['offset'] = sound.get_pos()
                sound.stop()
            if not self.cache:
                sound.unload()
                info['sound'] = None


def _test():
    import os
    from kivy.resources import resource_add_path, resource_find
    from kivy.factory import Factory
    from kivy.lang import Builder
    from kivy.base import runTouchApp
    from kivy.properties import DictProperty, ObjectProperty
    import yaml

    for parent, __1, __2 in os.walk('./data'):
        resource_add_path(parent)

    Builder.load_string(r'''
<Button>:
    font_size: 30
<RootWidget>:
    BoxLayout:
        BoxLayout:
            orientation: 'vertical'
            Button:
                text: 'play'
                on_press: root.bgmplayer.play(spinner.text)
            Button:
                text: 'play(save_previous)'
                on_press: root.bgmplayer.play(spinner.text, save_previous_bgm_offset=True)
            Button:
                text: 'stop'
                on_press: root.bgmplayer.stop()
            Button:
                text: 'pause'
                on_press: root.bgmplayer.pause()
        AnchorLayout:
            anchor_y: 'top'
            anchor_x: 'center'
            Spinner:
                id: spinner
                sync_height: True
                size_hint_y: None
                height: 50
    ''')

    class RootWidget(Factory.FloatLayout):
        soundfile_dict = DictProperty()
        bgmplayer = ObjectProperty()

        def __init__(self, *, soundfile_dict, **kwargs):
            super().__init__(soundfile_dict=soundfile_dict, **kwargs)
            self.bgmplayer = BgmPlayer(soundfile_dict)
            spinner = self.ids.spinner
            spinner.values = list(soundfile_dict.keys())
            spinner.text = spinner.values[0]

    with open(resource_find('soundfile_dict.yaml'), 'rt') as reader:
        soundfile_dict = {
            key: filename for key, filename in yaml.load(reader).items()
            if key.startswith('bgm_')
        }
    print(soundfile_dict)
    runTouchApp(RootWidget(soundfile_dict=soundfile_dict))


if __name__ == '__main__':
    _test()
