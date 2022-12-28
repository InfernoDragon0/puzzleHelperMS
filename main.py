import time
import win32gui
import win32ui
import win32con
import numpy
import cv2
import imutils
import os

hwnds = []
#default size
w = 1366
h = 768
mouseX,mouseY = 0,0

targetFPS = 30 #change this to change the FPS

# data
matchFound = False
imageData = []


#debug to get the X Y axis
def draw_circle(event,x,y,flags,param):
    global mouseX,mouseY
    if event == cv2.EVENT_LBUTTONDBLCLK:
        cv2.circle(img,(x,y),100,(255,0,0),-1)
        mouseX,mouseY = x,y

#window finder
def winEnumHandler( hwnd, ctx ):
    if win32gui.IsWindowVisible( hwnd ):
        if (win32gui.GetWindowText(hwnd) == "MapleStory"):
            print ( hex( hwnd ), win32gui.GetWindowText( hwnd ) )
            hwnds.append(hwnd)

def loadAllImages():
    for filename in os.listdir('./lowestquality'):
        print("Loading " + filename)
        img = cv2.imread(os.path.join('./lowestquality', filename))
        img = cv2.resize(img, (800, 600))
        imageData.append(img)
        # cv2.imshow(filename, img)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()


def runCV():
    global matchFound
    win32gui.EnumWindows( winEnumHandler, None )

    hwnd = hwnds[0]
    if (len(hwnds) > 1): #player has chat external
        hwnd = hwnds[1]

    #get the correct size
    rect = win32gui.GetWindowRect(hwnd)
    x = rect[0]
    y = rect[1]
    w = rect[2] - x
    h = rect[3] - y

    # hwnd = win32gui.FindWindow(None, "MapleStory")
    wDC = win32gui.GetWindowDC(hwnd)
    dcObj=win32ui.CreateDCFromHandle(wDC)
    cDC=dcObj.CreateCompatibleDC()
    dataBitMap = win32ui.CreateBitmap()
    dataBitMap.CreateCompatibleBitmap(dcObj, w, h)
    cDC.SelectObject(dataBitMap)
    # cv2.namedWindow('image')
    # cv2.setMouseCallback('image',draw_circle)

    while True:
        #get the image from the window
        timestart = time.time()
        cDC.BitBlt((0,0),(w, h) , dcObj, (0,0), win32con.SRCCOPY)

        #make CV image
        signedIntsArray = dataBitMap.GetBitmapBits(True)
        img = numpy.fromstring(signedIntsArray, dtype='uint8')
        img.shape = (h,w,4)
        datashow = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)

        if not matchFound: #run a loop and matchTemplate on each of the images loaded
            for image in imageData:
                #cv2 matchtemplate
                result = cv2.matchTemplate(datashow, image, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                print("searching for match: " + str(max_val))
                if max_val > 0.6:
                    #show the image in cv2
                    print("MATCH FOUND with chance of: " + str(max_val))
                    matchFound = True
                    cv2.imshow('image', image)
                    break
                    
        else:
            print("match alraedy found")
            #match found, now open viewer and write rectangles



        timend = time.time()
        
        if (1/targetFPS - (timend-timestart) > 0):
            time.sleep(1/targetFPS - (timend-timestart))

        #end when Q is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
                # Free Resources
            dcObj.DeleteDC()
            cDC.DeleteDC()
            win32gui.ReleaseDC(hwnd, wDC)
            win32gui.DeleteObject(dataBitMap.GetHandle())
            break
        elif cv2.waitKey(1) & 0xFF == ord('c'): #continue to the next image
            cv2.destroyAllWindows()
            matchFound = False


loadAllImages()
runCV()