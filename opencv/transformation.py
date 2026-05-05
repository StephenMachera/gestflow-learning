import cv2 as cv
import numpy as np
from resize import rescaleFrame

# =============================================================
# TRANSLATION
# ==============================================================

def translate(img,x,y):
    transMat = np.float32([[1,0,x],[0,1,y]])
    dimensions = (img.shape[1],img.shape[0])
    return cv.warpAffine(img,transMat,dimensions)

img = cv.imread('photos/func.jpeg')

# Resizing an image
resized_img = rescaleFrame(img, 0.55)
translate_img = translate(resized_img,10,100)

cv.imshow('Translated Image', translate_img)

# =============================================================
# ROTATION
# ==============================================================
def rotation(img,angle,rotpoint):
    (height,width) = img.shape[:2]
    if rotpoint is None:
        rotpoint = (width//2, height//2)
    rotMat = cv.getRotationMatrix2D(rotpoint,angle,1.0)
    dimension = (width, height)
    return cv.warpAffine(img,rotMat,dimension)


rotated_img = rotation(resized_img,-129,None)
cv.imshow('Rotate_img', rotated_img)

# =============================================================
# FLIPPING
# =============================================================
# Flipping horizontally
flip = cv.flip(resized_img,1)
cv.imshow('ORIN', resized_img)
cv.imshow('Flipped Image', flip)
# Flipping vertically
v_flip = cv.flip(resized_img, 0)
cv.imshow('Verical Flip', v_flip)
# Flipping both vertiacally and horizontally
v_h_flip = cv.flip(resized_img,-1)
cv.imshow('Both Flip', v_h_flip)


cv.waitKey(0)
cv.destroyAllWindows()