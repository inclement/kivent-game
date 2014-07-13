from kivent import GameSystem
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import (ObjectProperty, BooleanProperty,
                             OptionProperty, NumericProperty,
                             StringProperty)
from kivy.core.window import Window
from kivy.animation import Animation

class EditSystem(GameSystem):

    active = BooleanProperty(False)

    interface = ObjectProperty(None, allownone=True)

    touch_mode = OptionProperty('add_wall',
                                options=['add_wall', 'add entity',
                                         'move_map'])

    active_touch = ObjectProperty(None, allownone=True)

    def on_touch_mode(self, instance, value):
        print 'touch mode is', self.touch_mode
    
    def receive_touch_down(self, touch):
        cam_pos = self.gameworld.systems['gameview'].camera_pos
        touch_pos = touch.pos[0] - cam_pos[0], touch.pos[1] - cam_pos[1]
        if self.touch_mode == 'add_wall':
            ws = self.gameworld.systems['wall']
            ws.prelim_start_at(touch_pos)
        elif self.touch_mode == 'move_map':
            if self.active_touch is None:
                self.active_touch = touch
            
    def receive_touch_move(self, touch):
        cam_pos = self.gameworld.systems['gameview'].camera_pos
        touch_pos = touch.pos[0] - cam_pos[0], touch.pos[1] - cam_pos[1]
        if self.touch_mode == 'add_wall':
            ws = self.gameworld.systems['wall']
            ws.prelim_end_at(touch_pos)
        elif self.touch_mode == 'move_map':
            if touch is self.active_touch:
                print 'move touch gameview'
                gv = self.gameworld.systems['gameview']
                print 'gv is', gv, touch.dx, touch.dy, gv.camera_pos
                gv.camera_pos = [gv.camera_pos[0] + touch.dx,
                                 gv.camera_pos[1] + touch.dy]
                print gv.camera_pos

    def receive_touch_up(self, touch):
        if self.touch_mode == 'add_wall':
            ws = self.gameworld.systems['wall']
            if ws.building:
                ws.confirm_wall()
            ws.building = False
        if touch is self.active_touch:
            self.active_touch = None

    def on_active(self, instance, value):
        if value:
            self.enable_edit_shader()
            self.open_edit_interface()
        else:
            self.disable_edit_shader()
            self.close_edit_interface()

    def enable_edit_shader(self):
        edit_renderer = self.gameworld.systems['grid_renderer']
        edit_renderer.shader_source = 'assets/glsl/grid.glsl'

    def disable_edit_shader(self):
        edit_renderer = self.gameworld.systems['grid_renderer']
        edit_renderer.shader_source = 'assets/glsl/trivial.glsl'

    def open_edit_interface(self):
        if self.interface is None:
            self.interface = EditInterface(editsystem=self)
        self.interface.open()

    def close_edit_interface(self):
        if self.interface is not None:
            self.interface.close()


class EditInterface(BoxLayout):

    visible = BooleanProperty(False)

    top = BooleanProperty(False)
    '''True if widget is at the top of the screen.'''

    editsystem = ObjectProperty()

    y_shift = NumericProperty()

    mode = StringProperty('walls')
    
    def open(self):
        if not self.visible:
            Window.add_widget(self)

    def close(self):
        if self.visible:
            Window.remove_widget(self)

    def on_top(self, instance, value):
        Animation.cancel_all(self)
        if value:
            Animation(y_shift=1, t='out_cubic', duration=0.5).start(self)
        else:
            Animation(y_shift=0, t='out_cubic', duration=0.5).start(self)

    def on_mode(self, instance, value):
        if value == 'walls':
            self.editsystem.touch_mode = 'add_wall'
        elif value == 'manipulate':
            self.editsystem.touch_mode = 'move_map'
