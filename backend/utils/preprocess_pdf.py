import cv2
import numpy as np

def crop_right_rect(img_arr):
    img = cv2.cvtColor(img_arr, cv2.COLOR_RGB2BGR)

    # 2. convert to HSV and threshold pink+blue
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # define pink range 
    pink_low = np.array([140,  50,  50])
    pink_high= np.array([170, 255, 255])
    # define blue range
    blue_low = np.array([ 90,  50,  50])
    blue_high= np.array([130, 255, 255])
    mask_pink = cv2.inRange(hsv, pink_low,  pink_high)
    mask_blue = cv2.inRange(hsv, blue_low, blue_high)
    mask = cv2.bitwise_or(mask_pink, mask_blue)
    
    # 3. clean it up and find contours
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15,15))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # # pick the largest
    c = max(cnts, key=cv2.contourArea)
    # cv2.imshow("mask", mask)
    # cv2.waitKey(0)
    x,y,w,h = cv2.boundingRect(c)

    # 4. instead of cropping, fill everything to the right of x with white
    img[:, x:] = [255, 255, 255]  

    # cv2.imshow("processed", img)
    # cv2.waitKey(0)
    
    # cv2.destroyAllWindows()

    return img
