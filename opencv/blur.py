# =============================================================
# BLURRING TECHNIQUES IN OPENCV
# =============================================================
import cv2 as cv
from resize import rescaleFrame
import numpy as np

# Converting BGR to Grayscale
resized_img = rescaleFrame(cv.imread('photos/func.jpeg'),0.55)
cv.imshow('Original Image', resized_img)

gray = cv.cvtColor(resized_img,cv.COLOR_BGR2GRAY)
cv.imshow('Grayscale Image', gray)

# AVERAGING BLUR
average_blur = cv.blur(resized_img,(3,3))
cv.imshow('Average Blur', average_blur)

# GAUSSIAN BLUR
gaussian_blur = cv.GaussianBlur(resized_img,(3,3),0)
cv.imshow('Gaussian Blur', gaussian_blur)

# MEDIAN BLUR
median_blur = cv.medianBlur(resized_img,3)
cv.imshow('Median Blur',median_blur)

# BILATERAL BLUR
bilateral_blur = cv.bilateralFilter(resized_img,5,15,15)
cv.imshow('Bilateral Blur',bilateral_blur)

cv.waitKey(0)

cv.destroyAllWindows()