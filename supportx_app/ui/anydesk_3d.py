from vispy import scene, app
from vispy.scene import visuals
from PySide6.QtWidgets import QWidget, QVBoxLayout
from vispy.app import use_app, Timer

# S'assurer que vispy utilise PySide6
use_app('pyside6')

class Anydesk3DWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        # Canvas Vispy intégré

        self.canvas = scene.SceneCanvas(keys='interactive', bgcolor=(0,0,0,0), parent=self)
        self.canvas.create_native()
        self.canvas.native.setMinimumSize(320, 240)
        self.canvas.native.setMaximumSize(640, 480)
        # Style transparent (le WA_TranslucentBackground n'est pas supporté par vispy natif)
        self.canvas.native.setStyleSheet("background: transparent;")
        layout.addWidget(self.canvas.native)

        # Création de la scène 3D
        view = self.canvas.central_widget.add_view()
        view.camera = scene.cameras.TurntableCamera(fov=45, azimuth=30, elevation=30, distance=6)
        # Cube 3D
        cube = visuals.Box(width=2, height=2, depth=2, color=(0.8, 0.1, 0.1, 1), edge_color='white')
        view.add(cube)
        # Lumière
        visuals.XYZAxis(parent=view.scene)
        # Animation simple
        self._cube = cube
        self._angle = 0
        self._timer = Timer(0.016, connect=self._animate, start=True)

    def _animate(self, event):
        self._angle += 1
        self._cube.transform = scene.transforms.MatrixTransform()
        self._cube.transform.rotate(self._angle, (0, 1, 0))
        self._cube.transform.rotate(self._angle / 2, (1, 0, 0))
        self.canvas.update()
