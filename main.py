from kivy.app import App

from kivy import config
config.Config.set('input', 'mouse', 'mouse,disable_multitouch')

from kivy.uix.widget import Widget
from kivy.uix.effectwidget import EffectWidget, FXAAEffect
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.vector import Vector
from kivy.properties import (ListProperty, DictProperty,
                             NumericProperty, ObjectProperty,
                             BooleanProperty, StringProperty,
                             OptionProperty)
from kivy.utils import platform

import kivent
from kivent import GameSystem, DynamicRenderer

from random import randint, choice, random, normalvariate
from math import radians, sqrt, atan2, sin, cos, pi
from functools import partial

#import ipdb

# Import to register widgets in all of these:
import interface
import shields
import projectiles
import walls
import fire
import renderers
import edit

class TimingSystem(GameSystem):

    updateable = BooleanProperty(True)

    def update(self, dt):
        super(TimingSystem, self).update(dt)

        for entity_id in self.entity_ids:
            entity = self.gameworld.entities[entity_id]
            timing_data = getattr(entity, self.system_id)

            timing_data.current_time -= dt

            opacity = timing_data.current_time / timing_data.original_time
            entity.color.a = opacity

            if timing_data.current_time < 0.:
                self.gameworld.remove_entity(entity_id)
        


class InputSystem(GameSystem):
    mode = StringProperty('play')

    touches = ListProperty([])

    projectile_element = OptionProperty('air', options=['earth', 'air',
                                                        'fire', 'water'])

    shield_element = OptionProperty('fire', options=['earth', 'air',
                                                     'fire', 'water'])

    def __init__(self, *args, **kwargs):
        super(InputSystem, self).__init__(*args, **kwargs)
        Window.bind(on_key_down=self.on_key_down,
                    on_key_up=self.on_key_up)
        self.keys_down = set()

    def to_map(self, coords):
        cam_pos = self.gameworld.systems['gameview'].cam_pos
        return (coords[0] - cam_pos[0], coords[1] - cam_pos[1])

    def on_mode(self, instance, value):
        if value == 'edit':
            self.gameworld.systems['edit'].active = True
        else:
            self.gameworld.systems['edit'].active = False

    def on_key_down(self, window, keycode, *args):
        if keycode in (273, 274, 275, 276):
            self.gameworld.systems['player'].keys_pressed.add(keycode)

        self.keys_down.add(keycode)
        print keycode

        if 306 in self.keys_down and keycode == 101:
            self.mode = {'play': 'edit', 'edit': 'play'}[self.mode]
        if keycode == 286:
            self.mode = 'play'
        if keycode == 287:
            self.mode = 'edit'

    def on_key_up(self, window, keycode, *args):
        if keycode in (273, 274, 275, 276):
            self.gameworld.systems['player'].keys_pressed.remove(keycode)

        try:
            self.keys_down.remove(keycode)
        except KeyError as err:
            print err

    def on_touch_down(self, touch):
        if self.mode == 'edit':
            gw = self.gameworld
            edit_system = self.gameworld.systems['edit']
            edit_system.receive_touch_down(touch)
            
        else:
            if 'button' in touch.profile:
                if touch.button == 'left':
                    self.gameworld.systems['player'].fire_projectile(
                        touch, self.projectile_element)
                elif touch.button == 'right':
                    ss = self.gameworld.systems['{}_shield'.format(
                        self.shield_element)]
                    ss.new_touch(touch)
            elif 'pos' in touch.profile:
                ss = self.gameworld.systems['{}_shield'.format(
                    self.shield_element)]
                ss.new_touch(touch)

    def on_touch_move(self, touch):
        if self.mode == 'edit':
            gw = self.gameworld
            edit_system = gw.systems['edit']
            edit_system.receive_touch_move(touch)

        else:
            if 'button' in touch.profile:
                if touch.button == 'right':
                    ss = self.gameworld.systems['{}_shield'.format(
                        self.shield_element)]
                    ss.touch_move(touch)
            elif 'pos' in touch.profile:
                ss = self.gameworld.systems['{}_shield'.format(
                    self.shield_element)]
                ss.touch_move(touch)

    def on_touch_up(self, touch):
        if self.mode == 'edit':
            gw = self.gameworld
            edit_system = gw.systems['edit']
            edit_system.receive_touch_up(touch)
        if 'button' in touch.profile:
            if touch.button == 'right':
                ss = self.gameworld.systems['{}_shield'.format(
                    self.shield_element)]
                ss.touch_released(touch)
        elif 'pos' in touch.profile:
            ss = self.gameworld.systems['{}_shield'.format(
                self.shield_element)]
            ss.touch_released(touch)
    
        


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
        self.update_physics_velocity()

    def update_physics_velocity(self, *args):
        entity = self.gameworld.entities[self.entity_ids[0]]
        mag = sqrt(sum([i**2 for i in self.velocity]))
        if mag == 0:
            mag = 1.

        new_velocity = (500./mag*self.velocity[0],
                        500./mag*self.velocity[1])

        old_velocity = entity.physics.body.velocity
        old_velocity = (old_velocity.x, old_velocity.y)

        change = (new_velocity[0] - old_velocity[0],
                  new_velocity[1] - old_velocity[1])

        mass = entity.physics.body.mass

        entity.physics.body.apply_impulse((mass*change[0], mass*change[1]))

    def fire_projectile(self, touch, element):
        entity = self.gameworld.entities[self.entity_ids[0]]
        angle = self.angle
        # self.gameworld.systems['fire'].spawn_at_point(
        #     (entity.position.x + 37*cos(angle),
        #      entity.position.y + 37*sin(angle)),
        #     (200*cos(angle), 200*sin(angle)))
        self.gameworld.systems['{}_projectile'.format(element)].fire_projectile(
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
                                 'physics_renderer': {'texture': 'wizardhat',
                                                      'size': (64, 64)},
                                 'position': pos,
                                 'player': {},
                                 'rotate': 0}
        component_order = ['position', 'rotate', 'physics', 'player',
                           'physics_renderer']
        result = self.gameworld.init_entity(create_component_dict,
                                            component_order)
        # gv = self.gameworld.systems['gameview']
        # gv.entity_to_focus = result
        # gv.focus_entity = True
        return result

class KiventGame(Widget):

    def __init__(self, **kwargs):
        super(KiventGame, self).__init__(**kwargs)
        Clock.schedule_once(self.init_game, 1)

    def init_game(self, dt):
        try:
            self._init_game(0)
        except KeyError:
            Clock.schedule_once(self.init_game)

    def _init_game(self, dt):
        self.setup_map()
        self.setup_states()
        self.set_state()
        self.init_collisions()
        self.gameworld.systems['player'].spawn_player((150, 150))
        Clock.schedule_interval(self.update, 0)

        # Hack to make grid fragment shader work
        create_component_dict = {'grid_renderer': {'texture': 'fireball',
                                                      'size': (5000, 5000)},
                                 'position': (0, 0)}
        self.gameworld.init_entity(create_component_dict,
                                   ['position', 'grid_renderer'])

    def init_collisions(self):
        physics = self.gameworld.systems['physics']
        fire = self.gameworld.systems['fire']
        # physics.add_collision_handler(10, 20,
        #                               begin_func=

    def update(self, dt):
        self.gameworld.update(dt)

    def setup_map(self):
        gameworld = self.gameworld
        print 'systems are', gameworld, gameworld.systems
        print 'children are', self.children
        print 'gameworld children are', self.children[-1].children
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


class KiventApp(App):
    def build(self):
        Window.clearcolor = (0.9, 0.9, 0.9, 1)
        return KiventGame()



if __name__ == "__main__":
    KiventApp().run()
