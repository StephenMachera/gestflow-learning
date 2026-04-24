import cv2 as cv
import sys
# Reading images
img = cv.imread('photos/my.jpeg')

if img is None:
    sys.exit("Could not read the image.")
cv.imshow('wal', img)

cv.waitKey(0)


# READING VIDEOS
cap = cv.VideoCapture('videos/test2.mp4')
while True:
    isTrue, frame = cap.read()
    # if not isTrue:
    #     sys.exit("Could not read the video.")
    cv.imshow('video', frame)
    if cv.waitKey(20) & 0xFF == ord('d'):
        break
cap.release()

cv.destroyAllWindows()

