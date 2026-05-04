import cv2 as cv
import numpy as np
import sys
from resize import rescaleFrame


# DRAWING ON IMAGES
# create  a blank image using numpy

blank = np.zeros((500,500,3), dtype='uint8')



# Paint the image a certain colour
blank[:] = 0,255,0

# Drawing a rectangle
rectangle = cv.rectangle(blank, (0,0), (500,500), (255,211,0), thickness=-1)
resized_rectangle = rescaleFrame(rectangle, 0.5)

# Writing text on an image
cv.putText(blank, 'Hello World', (225,250), cv.FONT_HERSHEY_SIMPLEX, 1.0, (255,0,0), thickness=2)
cv.imshow('Blank',blank)
cv.imshow('Rectangle', resized_rectangle)
cv.waitKey(0)
