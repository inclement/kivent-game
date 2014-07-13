from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import (StringProperty, BooleanProperty,
                             DictProperty, ObjectProperty)


class ImageButton(ButtonBehavior, Image):
    pass

class ElementPicker(BoxLayout):
    element = StringProperty('fire')
    projectile_image = StringProperty('atlas://assets/images_atlas/airball')
    shield_image = StringProperty('atlas://assets/images_atlas/fireball')
    projectile_active = BooleanProperty(False)
    shield_active = BooleanProperty(False)

class LevelInterface(FloatLayout):
    gameworld = ObjectProperty(None)

    projectile_element = StringProperty('air')
    shield_element = StringProperty('fire')

    element_pickers = DictProperty({})

    def on_projectile_element(self, instance, elt):
        if self.gameworld is not None:
            gw = self.gameworld
            gw.systems['input'].projectile_element = elt

        for picker_element in ('earth', 'air', 'fire', 'water'):
            if picker_element != elt:
                self.element_pickers[
                    picker_element].projectile_active = False
            else:
                self.element_pickers[
                    self.projectile_element].projectile_active = True

    def on_shield_element(self, instance, elt):
        if self.gameworld is not None:
            gw = self.gameworld
            gw.systems['input'].shield_element = elt

        for picker_element in ('earth', 'air', 'fire', 'water'):
            if picker_element != elt:
                self.element_pickers[
                    picker_element].shield_active = False
            else:
                self.element_pickers[
                    self.shield_element].shield_active = True
