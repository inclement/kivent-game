from kivent import DynamicRenderer
from kivy.clock import Clock

class TimeDynamicRenderer(DynamicRenderer):
    def update(self, dt):
        super(TimeDynamicRenderer, self).update(dt)
        self.canvas['time'] = Clock.get_boottime()
