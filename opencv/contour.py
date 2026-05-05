# =============================================================
# CONTOUR DETECTION IN OPENCV
# =============================================================
import cv2 as cv
import sys
from resize import rescaleFrame

img = cv.imread('photos/func.jpeg')
cv.imshow('Origin image',img)
# Resizing the Image
resized_img = rescaleFrame(img,0.55)
cv.imshow("Resized Image", resized_img)

# Change the resized image from the BGR to Grayscale
gray = cv.cvtColor(resized_img,cv.COLOR_BGR2GRAY)
cv.imshow('GrayScale Image', gray)

# Blurring the grayscale image to remove noise using bilateral blurring technique
blur = cv.bilateralFilter(gray,5,15,15)
cv.imshow('Bilateral Image',blur)

# Contour detection using Canny edges
canny = cv.Canny(blur,125,185)
cv.imshow("Canny Image", canny)

contours, hierarchies = cv.findContours(canny,cv.RETR_LIST,cv.CHAIN_APPROX_NONE)
print(f'{len(contours)} contour(s) found!')

# Contour detection using Binary Threshold
ret ,threshold = cv.threshold(gray,125,255,cv.THRESH_BINARY)
cv.imshow('Threshold Image', threshold)

# contours, hierarchies = cv.findContours(threshold,cv.RETR_LIST,cv.CHAIN_APPROX_NONE)
# print(f'{len(contours)} contour(s) found!')


# =============================================================
# CONTOUR VISUALIZATION IN OPENCV
# =============================================================
import numpy as np
# Draw a blank image
blank = np.zeros(resized_img.shape,dtype='uint8')

cv.drawContours(blank,contours,-1,(0,0,255),1)
cv.imshow('Contours drawn',blank)

cv.waitKey(25000)