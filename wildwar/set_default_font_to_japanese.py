all = (r'apply')

from kivy.core.text import LabelBase
from kivy.lang import Builder


REGISTRATION_NAME = 'DefaultJapaneseFont'


def apply():
    LabelBase.register(
        REGISTRATION_NAME,
        fn_regular='RictyDiminished-Regular.ttf',
        fn_bold='RictyDiminished-Bold.ttf')
    Builder.load_string(
        '<Label,TextInput>:\n    font_name: r"{}"'.format(REGISTRATION_NAME)
    )
