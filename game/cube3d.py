from PySide6.QtWidgets import QWidget, QVBoxLayout
from vispy import scene
from vispy.scene import visuals

class Cube3DGameWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(320, 240)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # Canvas Vispy
        self.canvas = scene.SceneCanvas(keys='interactive', bgcolor='black', parent=self, size=(400, 400), show=False)
        layout.addWidget(self.canvas.native)
        self.view = self.canvas.central_widget.add_view()
        self.view.camera = 'turntable'
        self.cube = visuals.Box(width=2, height=2, depth=2, color=(0.2, 0.7, 1, 1), edge_color='white')
        self.view.add(self.cube)
        self.view.camera.fov = 45
        self.view.camera.distance = 6
        self.canvas.show()
