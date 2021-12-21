from picamera import PiCamera
from time import sleep
import numpy as np
import cv2 as cv
from PIL import Image
#from matplotlib import pyplot as plt

def new():
    img=np.ones((250,250,3),dtype=np.uint8)
    for i in range(50,80,1):
        for j in range(40,70,1):
            img[i][j]*=200
    cv.circle(img,(120,120),20,(100,200,80),-1)
    img=Image.fromarray(img)
    img.save('k.jpg')
def cap(name='x',sqres=250):
    pic=PiCamera()
    pic.resolution=(sqres,sqres)
    pic.zoom=(0,0,1,1)
    pic.start_preview()
    pic.color_effects=(128,128) #grayscale
    sleep(4)
    pic.capture(name+'.jpg')
    pic.stop_preview()
    return 'success'

def edg(name='y',mVal=48,MVal=95):
    img=cv.imread(name+'.jpg')
    edg=cv.Canny(img,mVal-10,MVal) #args=(target,minVal,maxVal)
    cv.imshow('1',edg)
    cv.waitKey(0)
    cv.destroyAllWindows()
    edg=cv.Canny(img,mVal+10,MVal) #args=(target,minVal,maxVal)
    cv.imshow('3',edg)
    cv.waitKey(0)
    cv.destroyAllWindows()
    edg=cv.Canny(img,mVal,MVal) #args=(target,minVal,maxVal)
    cv.imshow('2',edg)
    cv.waitKey(0)
    cv.destroyAllWindows()
    cv.imwrite(name+'-edge.jpg',edg)
    return 'success'

def circ(name='y'):
    img=cv.imread(name+'.jpg')
    img=cv.medianBlur(img,5)
    img=cv.cvtColor(img,cv.COLOR_BGR2GRAY)
    circles=cv.HoughCircles(img,cv.HOUGH_GRADIENT,1,100,
                            param1=90, #30 for k.jpg
                            param2=35, #15 for k.jpg
                            minRadius=10,
                            maxRadius=0)
    print(circles)
    if circles is None:
        return
    circles=circles[0]
    for i in circles:
        cv.circle(img,(int(i[0]),int(i[1])),int(i[2]),(0,0,0),2)
        cv.circle(img,(int(i[0]),int(i[1])),2,(0,0,0),3)
    cv.imwrite(name+'-circ.jpg',img)
    cv.imshow('circ',img)
    k=cv.waitKey(0)
    if k==27: cv.destroyAllWindows()
    
def main():
    cap('z',1000)
    circ('z')
