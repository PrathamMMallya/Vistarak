from manim import *
import numpy as np

class GeneratedScene(Scene):
    def construct(self):
        title = Text("Fourier Series").to_edge(UP)
        self.play(Write(title))
        
        axes = Axes(
            x_range=[0, 4*PI, PI/2],
            y_range=[-1.5, 1.5, 1],
            axis_config={"include_numbers": False}
        )
        self.play(Create(axes))
        
        # Base wave (Square wave target)
        def square_wave(x):
            return 1 if np.sin(x) > 0 else -1
            
        target_graph = axes.plot(square_wave, color=GRAY, use_smoothing=False)
        self.play(Create(target_graph))
        
        n_terms = 5
        current_graph = None
        
        for n in range(1, n_terms * 2, 2):
            frequency = n
            amplitude = 4 / (PI * n)
            
            def fourier_approx(x, terms=n):
                return sum((4 / (PI * k)) * np.sin(k * x) for k in range(1, terms + 1, 2))
                
            new_graph = axes.plot(lambda x: fourier_approx(x, n), color=YELLOW)
            
            info = Text(f"Adding Harmonic: n={n}", font_size=24).to_corner(UR)
            self.play(Write(info), run_time=0.5)
            
            if current_graph:
                self.play(Transform(current_graph, new_graph))
            else:
                current_graph = new_graph
                self.play(Create(current_graph))
                
            self.play(FadeOut(info), run_time=0.5)
            
        final_info = Text("Final Waveform", font_size=24, color=GREEN).to_corner(UR)
        self.play(Write(final_info))
        self.wait(2)
