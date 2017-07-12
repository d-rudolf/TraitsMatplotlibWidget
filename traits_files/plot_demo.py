import matplotlib.pyplot as plt
import numpy as np
class Plot():
    def __init__(self):
        sigma = 0.1
        num = 100.
        x = np.arange(0,2*np.pi,2*np.pi/num)
        err = np.random.normal(0,sigma,num)
        y = np.sin(x)**2/x**2+err
        z = np.sin(x)
        plt.figure(1)
        for value in [y,z]:
            ax = plt.gca()
            ax.errorbar(x, value, err, label = '1', fmt = 'o')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.legend()
        plt.show()

if __name__ == '__main__':
    Pl = Plot()

