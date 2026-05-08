import cv2 as cv
import sys
from resize import rescaleFrame
# Reading images
img = cv.imread('photos/my.jpeg')

if img is None:
    sys.exit("Could not read the image.")

resized_image = rescaleFrame(img, 0.15)
cv.imshow('wal', resized_image)

cv.waitKey(0)


# READING VIDEOS
cap = cv.VideoCapture('videos/test2.mp4')
while True:
    isTrue, frame = cap.read()
    # if not isTrue:
    #     sys.exit("Could not read the video.")
    resized_video = rescaleFrame(frame , 0.15)
    cv.imshow('video', resized_video)
    if cv.waitKey(20) & 0xFF == ord('d'):
        break
cap.release()

cv.destroyAllWindows()

