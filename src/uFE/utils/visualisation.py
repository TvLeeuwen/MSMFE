import time
import matplotlib.pyplot as plt

# Classes ---------------------------------------------------------------------
class IndexTracker(object):
    def __init__(self, ax, X, view=0):
        self.ax = ax
        ax.set_title("Scroll or j and k to navigate images")

        self.X = X
        self.view = view
        self.slices = X.shape[self.view]

        self.ind = self.slices // 2

        if self.view == 0:
            self.im = ax.imshow(
                self.X[self.ind, :, :],
                cmap="gray",
            )
        if self.view == 1:
            self.im = ax.imshow(
                self.X[:, self.ind, :],
                cmap="gray",
            )
        if self.view == 2:
            self.im = ax.imshow(
                self.X[:, :, self.ind],
                cmap="gray",
            )

        self.update()

    def onjk(self, event, sc=5):
        if event.key == "k":
            self.ind = (self.ind + sc) % self.slices
            time.sleep(0.001)
        elif event.key == "j":
            self.ind = (self.ind - sc) % self.slices
            time.sleep(0.001)
        self.update()

    def onscroll(self, event, sc=1):
        print(f"{event.button} {event.step}")
        if event.button == "up":
            self.ind = (self.ind + sc) % self.slices
        else:
            self.ind = (self.ind - sc) % self.slices
        self.update()

    def update(self):
        # self.im.set_data(self.X[:, :, self.ind])
        if self.view == 0:
            self.im.set_data(self.X[self.ind, :, :])
        elif self.view == 1:
            self.im.set_data(self.X[:, self.ind, :])
        elif self.view == 2:
            self.im.set_data(self.X[:, :, self.ind])
        self.ax.set_ylabel(f"slice {self.ind}")
        self.im.axes.figure.canvas.draw()


# defs ------------------------------------------------------------------------
def visualize_stack(img):
    """
    Visualize image stack.

    :param img list: Image stack to visualized.
    """
    fig, ax = plt.subplots(1, 1)
    tracker = IndexTracker(ax, img, view=2)
    fig.canvas.mpl_connect("key_release_event", tracker.onjk)
    plt.show()
