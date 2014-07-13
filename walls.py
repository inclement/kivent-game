from kivent import GameSystem
from kivy.properties import (BooleanProperty, ListProperty,
                             NumericProperty)
from math import sin, cos, radians, sqrt, atan2

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
