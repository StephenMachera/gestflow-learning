import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
from resize import rescaleFrame

# =============================================================
# COMPUTING HISTOGRAMS
# =============================================================

# load images first
res_img = rescaleFrame(cv.imread('photos/func.jpeg'),0.55)

# Change the image to grayscale
gray_img = cv.cvtColor(res_img,cv.COLOR_BGR2GRAY)
cv.imshow('Grayscale Image', gray_img)

# compute the histogram and display the distbution of pixels using the matplotlib

hist = cv.calcHist([gray_img],[0],None,[256],[0,256])
plt.figure()
plt.title('GrayScale Histogram')
plt.xlabel('Bins')
plt.ylabel('# of pixels')
plt.plot(hist)
plt.xlim([0,256])
plt.show()

cv.waitKey(0)


