import cv2 as cv
from resize import rescaleFrame
import numpy as np

# ESSENTIAL FUNCTIONS FOR COMPUTER VISION
img = cv.imread('photos/func.jpeg')

# Resizing an image
resized_img = rescaleFrame(img, 0.55)
cv.imshow('Resized Image', resized_img)


# =============================================================
# CONVERTING AN IMAGE TO GRAYSCALE
# ==============================================================

gray = cv.cvtColor(resized_img,cv.COLOR_BGR2GRAY)
cv.imshow('Gray',gray)

# =============================================================
# BLUR AN IMAGE USING GAUSSIAN BLUR
# ==============================================================

blur = cv.GaussianBlur(gray,(7,7),0)
cv.imshow('Blur',blur)


# =============================================================
# EDGE CASCADE USING CANNY EDGE DETECTION ALGORITHM
# ==============================================================

edges = cv.Canny(blur,100,200)
cv.imshow('Canny edges', edges)

# =============================================================
# DILATING THE IMAGE
# ==============================================================
kernel = np.ones((5,5),np.uint8)
dilated = cv.dilate(edges,kernel,iterations=1)
cv.imshow('Dilated image', dilated)

# =============================================================
# ERODED THE IMAGE
# ==============================================================
erode = cv.erode(dilated,kernel,iterations=1)
cv.imshow('Erode image', erode)











cv.waitKey(14000)