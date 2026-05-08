import cv2 as cv
import numpy as np
from resize import rescaleFrame

# =============================================================
# BITWISE OPERATIONS AND MASKING IN OPENCV
# =============================================================
# create  a blank image using numpy
blank = np.zeros((500,500,3), dtype='uint8')
# Create a rectangle
rectangle = cv.rectangle(blank.copy(), (100,100), (400,400), (255,255,255), thickness=-1)

cv.imshow('Rectangle', rectangle)
# Create a circle
circle = cv.circle(blank.copy(), (250,250), 180, (255,255,255), thickness=-1)
cv.imshow('Circle', circle)

# BITWISE AND showing intersection of the two shapes
bitwise_and = cv.bitwise_and(rectangle, circle)

cv.imshow('Bitwise AND', bitwise_and)

# BITWISE OR showing union of the two shapes
bitwise_or = cv.bitwise_or(rectangle, circle)
cv.imshow('Bitwise OR', bitwise_or)

# BITWISE XOR showing non-overlapping regions of the two shapes
bitwise_xor = cv.bitwise_xor(rectangle, circle)
cv.imshow('Bitwise XOR', bitwise_xor)

# BITWISE NOT showing inverse of the shapes
bitwise_not = cv.bitwise_not(rectangle)
cv.imshow('Bitwise NOT', bitwise_not)



# MASKING - bitwise AND operation between an image and a mask
# Loading an image
resized_image = rescaleFrame(cv.imread('photos/func.jpeg'),0.55)

blank_img = np.zeros(resized_image.shape[:2],dtype='uint8')
cv.imshow('Blank Image', blank_img)

circle = cv.circle(blank_img, (resized_image.shape[1]//2,resized_image.shape[0]//2),120,255,-1)
cv.imshow("Circle", circle)

rectangle = cv.rectangle(blank_img.copy(), (150,150), (350,350), (255,255,255), thickness=-1)

mask = cv.bitwise_or(rectangle,circle)

masked_image = cv.bitwise_and(resized_image,resized_image,mask=mask)
cv.imshow('Masked image', masked_image)

# Convert to Grayscale
gray = cv.cvtColor(masked_image,cv.COLOR_BGR2GRAY)
# Blur the image using bilateral
blur = cv.bilateralFilter(gray,5,15,15)
cv.imshow("Bilateral Image", blur)

# Edge detection using Canny
canny = cv.Canny(blur,100,200)
cv.imshow('Canny image', canny)
cv.waitKey(25000)

