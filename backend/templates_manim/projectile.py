from manim import *

class GeneratedScene(Scene):
    def construct(self):
        title = Text("Projectile Motion").to_edge(UP)
        self.play(Write(title))
        
        axes = Axes(
            x_range=[0, 10, 1],
            y_range=[0, 5, 1],
            axis_config={"include_numbers": False}
        )
        self.play(Create(axes))
        
        # Variables
        vx = 4.0
        vy = 6.0
        gravity = -9.8
        
        t_tracker = ValueTracker(0)
        
        projectile = Dot(color=RED)
        projectile.add_updater(
            lambda m: m.move_to(axes.c2p(
                vx * t_tracker.get_value(),
                max(0, vy * t_tracker.get_value() + 0.5 * gravity * t_tracker.get_value()**2)
            ))
        )
        
        path = TracedPath(projectile.get_center, stroke_color=YELLOW)
        self.add(path, projectile)
        
        vx_arrow = Arrow(ORIGIN, RIGHT, color=BLUE, buff=0)
        vy_arrow = Arrow(ORIGIN, UP, color=GREEN, buff=0)
        
        vx_arrow.add_updater(
            lambda m: m.put_start_and_end_on(
                projectile.get_center(),
                projectile.get_center() + RIGHT * vx * 0.2
            )
        )
        vy_arrow.add_updater(
            lambda m: m.put_start_and_end_on(
                projectile.get_center(),
                projectile.get_center() + UP * (vy + gravity * t_tracker.get_value()) * 0.2
            )
        )
        self.add(vx_arrow, vy_arrow)
        
        time_of_flight = -2 * vy / gravity
        self.play(t_tracker.animate.set_value(time_of_flight), run_time=3, rate_func=linear)
        self.wait(2)