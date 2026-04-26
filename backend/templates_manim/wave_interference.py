from manim import *
import numpy as np

class GeneratedScene(Scene):
    def construct(self):
        title = Text("Wave Interference").to_edge(UP)
        self.play(Write(title))
        
        axes = Axes(x_range=[0, 10, 1], y_range=[-3, 3, 1])
        self.play(Create(axes))
        
        amplitude = 1.0
        frequency = 1.0
        phase_difference = PI
        
        t_tracker = ValueTracker(0)
        
        wave1 = always_redraw(lambda: axes.plot(
            lambda x: amplitude * np.sin(frequency * x - t_tracker.get_value()),
            color=BLUE
        ))
        
        wave2 = always_redraw(lambda: axes.plot(
            lambda x: amplitude * np.sin(frequency * x - t_tracker.get_value() + phase_difference),
            color=GREEN
        ))
        
        result_wave = always_redraw(lambda: axes.plot(
            lambda x: amplitude * np.sin(frequency * x - t_tracker.get_value()) + 
                      amplitude * np.sin(frequency * x - t_tracker.get_value() + phase_difference),
            color=YELLOW, stroke_width=6
        ))
        
        self.play(Create(wave1))
        self.play(Create(wave2))
        self.play(Create(result_wave))
        
        self.play(t_tracker.animate.set_value(4 * PI), run_time=4, rate_func=linear)
        self.wait(1)
