from manim import *

class GeneratedScene(Scene):
    def construct(self):
        title = Text("Eigenvalues & Eigenvectors").to_edge(UP)
        self.play(Write(title))
        
        # Variables
        matrix = [[2, 1], [1, 2]]
        
        grid = NumberPlane()
        self.play(Create(grid))
        
        # Vectors
        v1 = Vector([1, 1], color=YELLOW)
        v2 = Vector([-1, 1], color=RED)
        v3 = Vector([1, 0], color=GREEN)
        
        self.play(GrowArrow(v1), GrowArrow(v2), GrowArrow(v3))
        
        # Apply matrix transformation
        # Instead of Matrix(), use text to show transformation
        matrix_mobject = Text("[[2, 1], [1, 2]]", font_size=36).to_corner(UL)
        self.play(Write(matrix_mobject))
        
        # Deform
        self.play(
            grid.animate.apply_matrix(matrix),
            v1.animate.put_start_and_end_on(ORIGIN, [3, 3, 0]),
            v2.animate.put_start_and_end_on(ORIGIN, [-1, 1, 0]),
            v3.animate.put_start_and_end_on(ORIGIN, [2, 1, 0]),
            run_time=2
        )
        
        # Highlight eigenvectors
        v1_label = Text("Eigenvector (scaled)", font_size=20, color=YELLOW).next_to(v1.get_end(), RIGHT)
        v2_label = Text("Eigenvector (preserved)", font_size=20, color=RED).next_to(v2.get_end(), UP)
        
        self.play(Write(v1_label), Write(v2_label))
        self.wait(2)
