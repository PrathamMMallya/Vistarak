from manim import *
import numpy as np

class GeneratedScene(Scene):
    def construct(self):
        title = Text("Electric Field & Potential").to_edge(UP)
        self.play(Write(title))
        
        charge1 = Dot(LEFT * 2, color=RED, radius=0.2)
        charge1_label = Text("+", color=WHITE, font_size=24).move_to(charge1)
        
        charge2 = Dot(RIGHT * 2, color=BLUE, radius=0.2)
        charge2_label = Text("-", color=WHITE, font_size=24).move_to(charge2)
        
        self.play(FadeIn(charge1), FadeIn(charge1_label), FadeIn(charge2), FadeIn(charge2_label))
        
        def field_func(pos):
            # field due to + charge
            r1 = pos - charge1.get_center()
            dist1 = np.linalg.norm(r1)
            e1 = r1 / (dist1**3 + 0.1) if dist1 > 0 else np.array([0, 0, 0])
            
            # field due to - charge
            r2 = pos - charge2.get_center()
            dist2 = np.linalg.norm(r2)
            e2 = -r2 / (dist2**3 + 0.1) if dist2 > 0 else np.array([0, 0, 0])
            
            return e1 + e2
            
        vector_field = ArrowVectorField(field_func, x_range=[-6, 6, 1], y_range=[-4, 4, 1])
        self.play(Create(vector_field))
        self.wait(2)
