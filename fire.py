from kivent import GameSystem

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
