from manim import *

class GeneratedScene(Scene):
    def construct(self):
        # Variables
        learning_rate = 0.15
        start_x = 3.0
        
        title = Text("Gradient Descent: Finding the Minimum").to_edge(UP)
        self.play(Write(title))
        
        axes = Axes(
            x_range=[-4, 4, 1],
            y_range=[-1, 10, 2],
            axis_config={"include_numbers": False}
        )
        self.play(Create(axes))
        
        # Function y = x^2
        graph = axes.plot(lambda x: x**2, color=BLUE)
        graph_label = Text("y = x²", font_size=24, color=BLUE).next_to(graph, UP)
        self.play(Create(graph), FadeIn(graph_label))
        
        # Moving point
        current_x = start_x
        point = Dot(axes.c2p(current_x, current_x**2), color=RED, radius=0.1)
        self.play(FadeIn(point))
        
        for step in range(5):
            gradient = 2 * current_x
            loss = current_x**2
            
            # Text to show current variables
            info = Text(f"Step {step+1}: x={current_x:.2f}, grad={gradient:.2f}, loss={loss:.2f}", font_size=24)
            info.to_edge(DOWN)
            self.play(Write(info), run_time=0.5)
            
            # Gradient arrow
            dx = -0.5 if gradient > 0 else 0.5
            dy = dx * gradient
            arrow = Arrow(
                start=axes.c2p(current_x, loss),
                end=axes.c2p(current_x + dx, loss + dy),
                color=YELLOW,
                buff=0,
                max_tip_length_to_length_ratio=0.15
            )
            self.play(GrowArrow(arrow), run_time=0.5)
            
            # Move
            next_x = current_x - learning_rate * gradient
            self.play(
                point.animate.move_to(axes.c2p(next_x, next_x**2)),
                FadeOut(arrow),
                run_time=0.5
            )
            current_x = next_x
            self.play(FadeOut(info), run_time=0.2)
            
        final_info = Text("Reached Minimum!", font_size=32, color=GREEN).next_to(point, UP)
        self.play(Write(final_info))
        self.wait(2)
