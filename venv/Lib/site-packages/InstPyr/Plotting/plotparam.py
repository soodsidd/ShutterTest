import numpy as np
class PlotParam:
    def __init__(self, title=None, ytitle=None, color=None):
        self.title=title
        self.oneaxis=False
        self.colorchoices=['b','g','r','c','m','y','k']
        if color is not None:
            self.color=color
        else:
            #randomize colors
            self.color=self.colorchoices[np.random.randint(len(self.colorchoices))]


