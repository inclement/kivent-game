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

class TimeDynamicRenderer(DynamicRenderer):
    def update(self, dt):
        super(TimeDynamicRenderer, self).update(dt)
        self.canvas['time'] = Clock.get_boottime()

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

    

class MyProjectileSystem(GameSystem):

    texture = StringProperty('black_stone')

    colour = ListProperty([1, 1, 1, 1])

    def fire_projectile(self, pos, angle):
        shape_dict = {'inner_radius': 0,
                      'outer_radius': 10,
                      'mass': 50,
                      'offset': (0, 0)}
        col_shape = {'shape_type': 'circle',
                     'elasticity': 1.,
                     'collision_type': 10,
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
        # texture = choice(['fireball', 'waterball', 'earthball', 'airball'])
        texture = self.texture
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

class EarthProjectileSystem(MyProjectileSystem):
    texture = StringProperty('earthball')

class AirProjectileSystem(MyProjectileSystem):
    texture = StringProperty('airball')

class FireProjectileSystem(MyProjectileSystem):
    texture = StringProperty('fireball')

class WaterProjectileSystem(MyProjectileSystem):
    texture = StringProperty('waterball')

class ShieldSystem(GameSystem):

    building = BooleanProperty(False)
    current_entity = ObjectProperty(None, allownone=True)

    building_points = ListProperty([])

    current_touches = DictProperty({})

    colour = ListProperty([1, 1, 1, 1])

    collision_type = NumericProperty(0)

    renderer = ObjectProperty(None)

    new_shield_dist = NumericProperty(25)

    textures = ListProperty(['black_stone'])
    available_textures = ListProperty(['black_stone'])

    def __init__(self, *args, **kwargs):
        super(ShieldSystem, self).__init__(*args, **kwargs)
        self.available_textures = self.textures

    def on_textures(self, *args):
        self.available_textures = self.textures

    def new_touch(self, touch):
        texture = self.available_textures.pop(
            randint(0, len(self.available_textures)-1))
        self.check_textures()
        self.current_touches[touch] = (list(touch.pos), None, texture)

    def check_textures(self, *args):
        if len(self.available_textures) == 0:
            self.available_textures = self.textures

    def touch_move(self, touch):
        if touch not in self.current_touches:
            return

        points, entity, texture = self.current_touches[touch]

        pos = touch.pos
        diff = (pos[0] - points[-2], pos[1] - points[-1])
        dist = sqrt(diff[0]**2 + diff[1]**2)
        print 'dist is', dist

        if dist > self.new_shield_dist:
            points.extend(pos)

            if len(points) > 2:
                if entity is None:
                    entity = self.init_new_shield(points, texture)
                else:
                    self.extend_shield(points, entity, texture)

        self.current_touches[touch] = (points, entity, texture)

    def touch_released(self, touch):
        if touch in self.current_touches:
            self.current_touches.pop(touch)
                
    def init_new_shield(self, points, texture):
        start = (points[0], points[1])
        end = (points[-2], points[-1])
        dr = (end[0] - start[0], end[1] - start[1])

        angle = atan2(dr[1], dr[0])
        length = sqrt(dr[0]**2 + dr[1]**2)

        shape_dict = {'width': length,
                      'height': 30,
                      'mass': 50}
        col_shape = {'shape_type': 'box',
                     'elasticity': 1.,
                     'collision_type': self.collision_type,
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
        create_component_dict = {'physics': physics_component,
                                 self.renderer: {'texture': texture,
                                                 'size': (length, 30)},
                                 'position': start,
                                 'wall': {},
                                 'timing': {'original_time': 3.,
                                            'current_time': 3.},
                                 'color': tuple(self.colour),
                                 'rotate': 0}
        component_order = ['position', 'rotate', 'color', 'physics',
                           'wall',
                           'timing',
                           self.renderer]
        result = self.gameworld.init_entity(create_component_dict,
                                            component_order)
        return self.gameworld.entities[result]

    def extend_shield(self, points, entity, texture):
        start = (points[0], points[1])
        end = (points[-2], points[-1])
        dr = (end[0] - start[0], end[1] - start[1])

        angle = atan2(dr[1], dr[0])
        length = sqrt(dr[0]**2 + dr[1]**2)

        self.init_new_shield(points[-4:], texture)

class EarthShieldSystem(ShieldSystem):
    collision_type = NumericProperty(20)
    textures = ListProperty(['earthball'])
    def init_new_shield(self, points, texture):
        start = (points[0], points[1])
        end = (points[-2], points[-1])
        dr = (end[0] - start[0], end[1] - start[1])

        angle = random() * 2*pi
        length = sqrt(dr[0]**2 + dr[1]**2) / 2.

        random_modifier = 0.8*(random()-0.5)
        radius = length*(1.3 + random_modifier)
        mass = 9000*(radius/(1.2*length))**2

        shape_dict = {'inner_radius': 0,
                      'outer_radius': radius,
                      'mass': mass,
                      'offset': (0, 0)}
        col_shape = {'shape_type': 'circle',
                     'elasticity': 0.7,
                     'collision_type': self.collision_type,
                     'shape_info': shape_dict,
                     'friction': 10.0}
        col_shapes = [col_shape]

        centre_x = (start[0] + 0.5*length*cos(angle) +
                    0.1*length*normalvariate(0, 1))
        centre_y = (start[1] + 0.5*length*sin(angle) +
                    0.1*length*normalvariate(0, 1))
        physics_component = {'main_shape': 'box',
                             'velocity': (0, 0),
                             'position': (centre_x, centre_y),
                             'angle': angle,
                             'angular_velocity': 0,
                             'vel_limit': 5000,
                             'ang_vel_limit': 4*pi,
                             'mass': mass,
                             'col_shapes': col_shapes}
        create_component_dict = {'physics': physics_component,
                                 self.renderer: {'texture': texture,
                                                 'size': (2*radius, 2*radius)},
                                 'position': start,
                                 'wall': {},
                                 'color': tuple(self.colour),
                                 'rotate': 0}
        component_order = ['position', 'rotate', 'color', 'physics',
                           'wall',
                           self.renderer]
        result = self.gameworld.init_entity(create_component_dict,
                                            component_order)
        return self.gameworld.entities[result]

    def touch_move(self, touch):
        super(EarthShieldSystem, self).touch_move(touch)

        points, entity, texture = self.current_touches[touch]
        if random() > 0.9 and len(points) >= 4:
            self.init_secondary_rock(touch.pos, points, texture)

    def init_secondary_rock(self, pos, points, texture):
        length = 50
        angle = random() * 2*pi
        
        random_modifier = 1.25*(random()-0.5)
        radius = 0.2*length*(1.3 + random_modifier)
        mass = 1800*(radius/(1.2*length))**2

        shape_dict = {'inner_radius': 0,
                      'outer_radius': radius,
                      'mass': mass,
                      'offset': (0, 0)}
        col_shape = {'shape_type': 'circle',
                     'elasticity': 0.7,
                     'collision_type': self.collision_type,
                     'shape_info': shape_dict,
                     'friction': 10.0}
        col_shapes = [col_shape]

        centre_x = (pos[0] + 
                    0.3*length*normalvariate(0, 1))
        centre_y = (pos[1] + 
                    0.3*length*normalvariate(0, 1))
        physics_component = {'main_shape': 'box',
                             'velocity': (0, 0),
                             'position': (centre_x, centre_y),
                             'angle': angle,
                             'angular_velocity': 0,
                             'vel_limit': 5000,
                             'ang_vel_limit': 4*pi,
                             'mass': mass,
                             'col_shapes': col_shapes}
        create_component_dict = {'physics': physics_component,
                                 self.renderer: {'texture': texture,
                                                 'size': (2*radius, 2*radius)},
                                 'position': (centre_x, centre_y),
                                 'wall': {},
                                 'color': tuple(self.colour),
                                 'rotate': 0}
        component_order = ['position', 'rotate', 'color', 'physics',
                           'wall',
                           self.renderer]
        result = self.gameworld.init_entity(create_component_dict,
                                            component_order)
        return self.gameworld.entities[result]

    
class AirShieldSystem(ShieldSystem):
    collision_type = NumericProperty(21)
    textures = ListProperty(['airball'])

class FireShieldSystem(ShieldSystem):
    collision_type = NumericProperty(22)
    textures = ListProperty(['fireball'])

class WaterShieldSystem(ShieldSystem):
    collision_type = NumericProperty(23)
    textures = ListProperty(['waterball'])


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

    grid_spacing = NumericProperty(50)

    def create_wall(self, pos, length, angle):
        shape_dict = {'width': length,
                      'height': 20,
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
                                 'physics_renderer': {'texture': 'wall',
                                                      'size': (length, 20)},
                                 'position': pos,
                                 'wall': {},
                                 'rotate': 0}
        component_order = ['position', 'rotate', 'physics', 'wall',
                           'physics_renderer']
        result = self.gameworld.init_entity(create_component_dict,
                                            component_order)
        return result

    def prelim_start_at(self, pos):
        game_map = self.gameworld.systems['map']
        spacing = self.grid_spacing

        # How to get the right x and y position in game map terms?
        rounded_x = round(pos[0] / float(spacing)) * spacing
        rounded_y = round(pos[1] / float(spacing)) * spacing

        self.prelim_start = (rounded_x, rounded_y)
        self.prelim_end = (rounded_x, rounded_y)
        self.building = True

    def prelim_end_at(self, pos):
        game_map = self.gameworld.systems['map']
        spacing = self.grid_spacing

        # How to get the right x and y position in game map terms?
        rounded_x = round(pos[0] / float(spacing)) * spacing
        rounded_y = round(pos[1] / float(spacing)) * spacing

        self.prelim_end = (rounded_x, rounded_y)

    def confirm_wall(self):
        pos = tuple(self.prelim_start)
        length = sqrt((self.prelim_end[0] - self.prelim_start[0])**2 +
                      (self.prelim_end[1] - self.prelim_start[1])**2)
        angle = atan2(self.prelim_end[1] - self.prelim_start[1],
                      self.prelim_end[0] - self.prelim_start[0])
        self.create_wall(pos, length, angle)
        self.building=False


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

    def on_mode(self, *args):
        edit_renderer = self.gameworld.systems['grid_renderer']
        if self.mode == 'edit':
            edit_renderer.shader_source = 'assets/glsl/grid.glsl'
        else:
            edit_renderer.shader_source = 'assets/glsl/trivial.glsl'
        print 'mode switched to', self.mode

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
    
class EditSystem(GameSystem):
    def receive_touch_down(self, touch):
        if 'button' in touch.profile:
            if touch.button == 'left':
                ws = self.gameworld.systems['wall']
                ws.prelim_start_at(touch.pos)

    def receive_touch_move(self, touch):
        if 'button' in touch.profile:
            if touch.button == 'left':
                ws = self.gameworld.systems['wall']
                ws.prelim_end_at(touch.pos)

    def receive_touch_up(self, touch):
        if 'button' in touch.profile:
            if touch.button == 'left':
                ws = self.gameworld.systems['wall']
                if ws.building:
                    ws.confirm_wall()
                ws.building = False
        

class FireSystem(GameSystem):

    def spawn_continuous(self, pos, velocity, *args):
        pass

    def spawn_at_point(self, pos, velocity, size=50):
        print 'spawnint at', pos, velocity, size
        shape_dict = {'inner_radius': 0,
                      'outer_radius': size/2.,
                      'mass': 50,
                      'offset': (0, 0)}
        col_shape = {'shape_type': 'circle',
                     'elasticity': 1.,
                     'collision_type': 16,
                     'shape_info': shape_dict,
                     'friction': 00.0}
        col_shapes = [col_shape]
        physics_component = {'main_shape': 'circle',
                             'velocity': velocity,
                             'position': pos,
                             'angle': 0,
                             'angular_velocity': 0,
                             'vel_limit': 500,
                             'ang_vel_limit': 0,
                             'mass': 50,
                             'col_shapes': col_shapes}
        texture = 'fireball'
        create_component_dict = {'physics': physics_component,
                                 'colour_renderer': {'texture': texture,
                                                      'size': (2*size, 2*size)},
                                 'position': pos,
                                 'rotate': 0,
                                 'player': {}}
        component_order = ['position', 'rotate', 'physics', 'player',
                           'colour_renderer']
        result = self.gameworld.init_entity(create_component_dict,
                                            component_order)
        return result
                

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
                                 'position': (2500, 2500)}
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

class Interface(BoxLayout):
    pass

class KiventApp(App):
    def build(self):
        Window.clearcolor = (0.9, 0.9, 0.9, 1)



if __name__ == "__main__":
    KiventApp().run()
