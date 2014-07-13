from kivent import GameSystem
from kivy.properties import StringProperty, ListProperty
from math import cos, sin, radians

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
