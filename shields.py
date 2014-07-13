from kivent import GameSystem, DynamicRenderer
from kivy.properties import (ObjectProperty, ListProperty,
                             DictProperty, NumericProperty,
                             BooleanProperty)
from random import randint, choice, random, normalvariate
from math import radians, sqrt, atan2, sin, cos, pi

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

        cam_pos = self.gameworld.systems['gameview'].camera_pos
        print 'cam pos is', cam_pos
        centre_x = start[0] + 0.5*length*cos(angle) - cam_pos[0]
        centre_y = start[1] + 0.5*length*sin(angle) - cam_pos[1]
        print 'centre is', centre_x, centre_y
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

        cam_pos = self.gameworld.systems['gameview'].camera_pos
        centre_x = (start[0] + 0.5*length*cos(angle) +
                    0.1*length*normalvariate(0, 1)) - cam_pos[0]
        centre_y = (start[1] + 0.5*length*sin(angle) +
                    0.1*length*normalvariate(0, 1)) - cam_pos[1]
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

        cam_pos = self.gameworld.systems['gameview'].camera_pos
        centre_x = (pos[0] + 
                    0.3*length*normalvariate(0, 1)) - cam_pos[0]
        centre_y = (pos[1] + 
                    0.3*length*normalvariate(0, 1)) - cam_pos[1]
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
