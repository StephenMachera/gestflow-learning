# =============================================================
# COLOR SPACES IN OPENCV
# =============================================================
# 1.HSV
# 2.BGR
# 3.LAB
import cv2 as cv
from resize import rescaleFrame
import matplotlib.pyplot as plt

# Converting BGR to Grayscale
resized_img = rescaleFrame(cv.imread('photos/func.jpeg'),0.55)
cv.imshow('Original Image', resized_img)

gray = cv.cvtColor(resized_img,cv.COLOR_BGR2GRAY)
cv.imshow('Grayscale Image', gray)

# Converting BGR to HSV
hsv = cv.cvtColor(resized_img, cv.COLOR_BGR2HSV)
cv.imshow('HSV image', hsv)

# Converting BGR to LAB
lab = cv.cvtColor(resized_img, cv.COLOR_BGR2LAB)
cv.imshow('LAB Image', lab)

# Converting BGR from Grayscale

bgr = cv.cvtColor(gray,cv.COLOR_GRAY2BGR)
cv.imshow('bgr Image', bgr)

# Converting BGR from HSV
bgr = cv.cvtColor(hsv, cv.COLOR_HSV2BGR)
cv.imshow('bgr image', bgr)

# Converting BGR from LAB
bgr = cv.cvtColor(lab, cv.COLOR_LAB2BGR)
cv.imshow('bgr Image', bgr)


# COnverting BGR to RBG for other libraries
rgb = cv.cvtColor(resized_img, cv.COLOR_BGR2RGB)
plt.imshow(rgb)
plt.show()
cv.waitKey(25000)