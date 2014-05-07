from kivy.app import App

from kivy.uix.widget import Widget
from kivy.uix.effectwidget import EffectWidget, FXAAEffect
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.vector import Vector
from kivy.properties import (ListProperty, DictProperty,
                             NumericProperty, ObjectProperty,
                             BooleanProperty, StringProperty)

import kivent
from kivent import GameSystem

from random import randint
from math import radians, sqrt, atan2, sin, cos
from functools import partial

import ipdb

class MyProjectileSystem(GameSystem):

    def fire_projectile(self, pos, angle):
        shape_dict = {'inner_radius': 0,
                      'outer_radius': 10,
                      'mass': 50,
                      'offset': (0, 0)}
        col_shape = {'shape_type': 'circle',
                     'elasticity': 1.,
                     'collision_type': 1,
                     'shape_info': shape_dict,
                     'friction': 10.0}
        col_shapes = [col_shape]
        vel = (500*cos(angle), 500*sin(angle))
        physics_component = {'main_shape': 'circle',
                             'velocity': vel,
                             'position': pos,
                             'angle': angle,
                             'angular_velocity': 0,
                             'vel_limit': 500,
                             'ang_vel_limit': radians(200),
                             'mass': 50,
                             'col_shapes': col_shapes}
        create_component_dict = {'physics': physics_component,
                                 'physics_renderer': {'texture': 'fireball',
                                                      'size': (20, 20)},
                                 'position': pos,
                                 'player': {},
                                 'rotate': 0}
        component_order = ['position', 'rotate', 'physics', 'player',
                           'physics_renderer']
        result = self.gameworld.init_entity(create_component_dict,
                                            component_order)
        return result

class WallSystem(GameSystem):

    building = BooleanProperty(False)
    prelim_start = ListProperty([0, 0])
    prelim_end = ListProperty([10, 10])

    def create_wall(self, pos, length, angle):
        shape_dict = {'width': length,
                      'height': 10,
                      'mass': 50}
        col_shape = {'shape_type': 'box',
                     'elasticity': 1.,
                     'collision_type': 4,
                     'shape_info': shape_dict,
                     'friction': 10.0}
        col_shapes = [col_shape]

        centre_x = pos[0] + 0.5*length*cos(angle)
        centre_y = pos[1] + 0.5*length*sin(angle)
        physics_component = {'main_shape': 'box',
                             'velocity': (0, 0),
                             'position': (centre_x, centre_y),
                             'angle': angle,
                             'angular_velocity': 0,
                             'vel_limit': 0,
                             'ang_vel_limit': 0,
                             'mass': 50,
                             'col_shapes': col_shapes}
        create_component_dict = {'physics': physics_component,
                                 'physics_renderer': {'texture': 'fireball',
                                                      'size': (length, 10)},
                                 'position': pos,
                                 'wall': {},
                                 'rotate': 0}
        component_order = ['position', 'rotate', 'physics', 'wall',
                           'physics_renderer']
        result = self.gameworld.init_entity(create_component_dict,
                                            component_order)
        return result

    def confirm_wall(self):
        pos = tuple(self.prelim_start)
        length = sqrt((self.prelim_end[0] - self.prelim_start[0])**2 +
                      (self.prelim_end[1] - self.prelim_start[1])**2)
        angle = atan2(self.prelim_end[1] - self.prelim_start[1],
                      self.prelim_end[0] - self.prelim_start[0])
        self.create_wall(pos, length, angle)


class InputSystem(GameSystem):

    touch_mode = StringProperty('wall')

    def __init__(self, *args, **kwargs):
        super(InputSystem, self).__init__(*args, **kwargs)
        Window.bind(on_key_down=self.on_key_down,
                    on_key_up=self.on_key_up)

    def on_key_down(self, window, keycode, *args):
        if keycode not in (273, 274, 275, 276):
            return
        self.gameworld.systems['player'].keys_pressed.add(keycode)

    def on_key_up(self, window, keycode, *args):
        if keycode not in (273, 274, 275, 276):
            return
        self.gameworld.systems['player'].keys_pressed.remove(keycode)

    def on_touch_down(self, touch):
        if self.touch_mode == 'player':
            self.gameworld.systems['player'].handle_touch_down(touch)
        elif self.touch_mode == 'wall':
            ws = self.gameworld.systems['wall']
            ws.prelim_start = touch.pos
            ws.prelim_end = touch.pos
            ws.building = True

    def on_touch_move(self, touch):
        if self.touch_mode == 'wall':
            ws = self.gameworld.systems['wall']
            ws.prelim_end = touch.pos

    def on_touch_up(self, touch):
        if self.touch_mode == 'wall':
            ws = self.gameworld.systems['wall']
            if ws.building:
                ws.confirm_wall()
            ws.building = False
    

class PlayerSystem(GameSystem):

    velocity = ListProperty([0, 0])
    keys_pressed = ObjectProperty(set())
    mouse_pos = ListProperty([0, 0])
    angle = NumericProperty(0)

    updateable = BooleanProperty(True)

    def __init__(self, *args, **kwargs):
        super(PlayerSystem, self).__init__(*args, **kwargs)
        Window.bind(mouse_pos=self.setter('mouse_pos'))

    def update(self, dt):
        super(PlayerSystem, self).update(dt)
        mp = self.mouse_pos
        entity = self.gameworld.entities[self.entity_ids[0]]
        body = entity.physics.body
        pos = Vector((body.position.x, body.position.y))
        diff = Vector(mp) - pos
        angle = atan2(diff[1], diff[0])
        body.angle = angle
        self.angle = angle
        self.recalculate_velocity()

    def recalculate_velocity(self, *args):
        vel = Vector([0, 0])
        for keycode in self.keys_pressed:
            vel = vel + Vector(
                {273: (0, 1), 274: (0, -1),
                 275: (1, 0), 276: (-1, 0)}[keycode])
        self.velocity = vel

    def on_velocity(self, *args):
        entity = self.gameworld.entities[self.entity_ids[0]]
        entity.physics.body.velocity = (500*self.velocity[0],
                                        500*self.velocity[1])

    def handle_touch_down(self, touch):
        entity = self.gameworld.entities[self.entity_ids[0]]
        angle = self.angle
        self.gameworld.systems['projectile'].fire_projectile(
            (entity.position.x + 37*cos(angle),
             entity.position.y + 37*sin(angle)), self.angle)
    
    def spawn_player(self, pos):
        shape_dict = {'inner_radius': 0,
                      'outer_radius': 32,
                      'mass': 50,
                      'offset': (0, 0)}
        col_shape = {'shape_type': 'circle',
                     'elasticity': 1.,
                     'collision_type': 1,
                     'shape_info': shape_dict,
                     'friction': 10.0}
        col_shapes = [col_shape]
        physics_component = {'main_shape': 'circle',
                             'velocity': (0, 0),
                             'position': pos,
                             'angle': 0,
                             'angular_velocity': 0,
                             'vel_limit': 250,
                             'ang_vel_limit': radians(200),
                             'mass': 50,
                             'col_shapes': col_shapes}
        create_component_dict = {'physics': physics_component,
                                 'physics_renderer': {'texture': 'black_stone',
                                                      'size': (64, 64)},
                                 'position': pos,
                                 'player': {},
                                 'rotate': 0}
        component_order = ['position', 'rotate', 'physics', 'player',
                           'physics_renderer']
        result = self.gameworld.init_entity(create_component_dict,
                                            component_order)
        return result

class KiventGame(Widget):

    def __init__(self, **kwargs):
        super(KiventGame, self).__init__(**kwargs)
        Clock.schedule_once(self.init_game)

    def init_game(self, dt):
        self.setup_map()
        self.setup_states()
        self.set_state()
        self.gameworld.systems['player'].spawn_player((150, 150))
        Clock.schedule_interval(self.update, 0)

    def update(self, dt):
        self.gameworld.update(dt)

    def setup_map(self):
        gameworld = self.gameworld
        gameworld.currentmap = gameworld.systems['map']

    def setup_states(self):
        self.gameworld.add_state(state_name='main',
                                 systems_added=['debug_renderer',
                                                'physics_renderer',
                                                'player'],
                                 systems_removed=[],
                                 systems_paused=[],
                                 systems_unpaused=['debug_renderer',
                                                   'physics_renderer'],
                                 screenmanager_screen='main')

    def set_state(self):
        self.gameworld.state = 'main'

class Interface(BoxLayout):
    pass

class KiventApp(App):
    def build(self):
        Window.clearcolor = (0.9, 0.9, 0.9, 1)



if __name__ == "__main__":
    KiventApp().run()
