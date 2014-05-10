from kivy.app import App

from kivy import config
config.Config.set('input', 'mouse', 'mouse,disable_multitouch')

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

from random import randint, choice
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
        texture = choice(['fireball', 'waterball', 'earthball', 'airball'])
        create_component_dict = {'physics': physics_component,
                                 'physics_renderer': {'texture': texture,
                                                      'size': (20, 20)},
                                 'position': pos,
                                 'player': {},
                                 'rotate': 0}
        component_order = ['position', 'rotate', 'physics', 'player',
                           'physics_renderer']
        result = self.gameworld.init_entity(create_component_dict,
                                            component_order)
        return result

class ShieldSystem(GameSystem):

    building = BooleanProperty(False)
    current_entity = ObjectProperty(None, allownone=True)

    building_points = ListProperty([])

    current_touches = DictProperty({})

    def new_touch(self, touch):
        self.current_touches[touch] = (list(touch.pos), None)

    def touch_move(self, touch):
        if touch not in self.current_touches:
            return

        points, entity = self.current_touches[touch]

        pos = touch.pos
        diff = (pos[0] - points[-2], pos[1] - points[-1])
        dist = sqrt(diff[0]**2 + diff[1]**2)

        if dist > 25:
            points.extend(pos)

        if len(points) > 2:
            if entity is None:
                entity = self.init_new_shield(points)
            else:
                self.extend_shield(points, entity)

        self.current_touches[touch] = (points, entity)

    def touch_released(self, touch):
        if touch in self.current_touches:
            self.current_touches.pop(touch)
                
    def init_new_shield(self, points):
        start = (points[0], points[1])
        end = (points[-2], points[-1])
        dr = (end[0] - start[0], end[1] - start[1])

        angle = atan2(dr[1], dr[0])
        length = sqrt(dr[0]**2 + dr[1]**2)
        
        shape_dict = {'width': length,
                      'height': 10,
                      'mass': 50}
        col_shape = {'shape_type': 'box',
                     'elasticity': 1.,
                     'collision_type': 4,
                     'shape_info': shape_dict,
                     'friction': 10.0}
        col_shapes = [col_shape]

        centre_x = start[0] + 0.5*length*cos(angle)
        centre_y = start[1] + 0.5*length*sin(angle)
        physics_component = {'main_shape': 'box',
                             'velocity': (0, 0),
                             'position': (centre_x, centre_y),
                             'angle': angle,
                             'angular_velocity': 0,
                             'vel_limit': 0,
                             'ang_vel_limit': 0,
                             'mass': 0,
                             'col_shapes': col_shapes}
        texture = choice(['fireball', 'waterball', 'earthball', 'airball'])
        create_component_dict = {'physics': physics_component,
                                 'physics_color_renderer': {'texture': texture,
                                                            'size': (length, 10)},
                                 'position': start,
                                 'wall': {},
                                 'timing': {'original_time': 3.,
                                            'current_time': 3.},
                                 'color': (1, 1, 1, 1),
                                 'rotate': 0}
        component_order = ['position', 'rotate', 'color', 'physics', 'wall',
                           'timing',
                           'physics_color_renderer']
        result = self.gameworld.init_entity(create_component_dict,
                                            component_order)
        return self.gameworld.entities[result]

    def extend_shield(self, points, entity):
        start = (points[0], points[1])
        end = (points[-2], points[-1])
        dr = (end[0] - start[0], end[1] - start[1])

        angle = atan2(dr[1], dr[0])
        length = sqrt(dr[0]**2 + dr[1]**2)

        self.init_new_shield(points[-4:])


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
                             'mass': 0,
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
        if 'button' in touch.profile:
            if touch.button == 'left':
                self.gameworld.systems['player'].handle_touch_down(touch)
            elif touch.button == 'middle':
                ws = self.gameworld.systems['wall']
                ws.prelim_start = touch.pos
                ws.prelim_end = touch.pos
                ws.building = True
            elif touch.button == 'right':
                ss = self.gameworld.systems['shield']
                ss.new_touch(touch)

    def on_touch_move(self, touch):
        if 'button' in touch.profile:
            if touch.button == 'middle':
                ws = self.gameworld.systems['wall']
                ws.prelim_end = touch.pos
            elif touch.button == 'right':
                ss = self.gameworld.systems['shield']
                ss.touch_move(touch)

    def on_touch_up(self, touch):
        if 'button' in touch.profile:
            if touch.button == 'middle':
                ws = self.gameworld.systems['wall']
                if ws.building:
                    ws.confirm_wall()
                ws.building = False
            elif touch.button == 'right':
                ss = self.gameworld.systems['shield']
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

        create_component_dict = {'grid_renderer': {'texture': 'fireball',
                                                      'size': (5000, 5000)},
                                 'position': (2500, 2500)}
        self.gameworld.init_entity(create_component_dict,
                                   ['position', 'grid_renderer'])

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
