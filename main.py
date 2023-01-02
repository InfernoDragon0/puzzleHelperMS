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

targetFPS = 60 #change this to change the FPS

# data
matchFound = False
imageData = []
imageSelected = None
imageCut = None

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
        datasmol = datashow[50:800, 400:900] #800,500 downscale 4 times to 200,125
        datascaled = cv2.resize(datasmol, interpolation=cv2.INTER_AREA, dsize=(datasmol.shape[1]//6, datasmol.shape[0]//6))
        gray_version = cv2.cvtColor(datascaled, cv2.COLOR_BGR2GRAY)

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
                    imageSelected = image
                    #split imageSelected into 5 by 4
                    #
                    cutX, cutY = image.shape[1] // 5, image.shape[0] // 4
                    curX, curY = 0,0
                    imageCut = []
                    for i in range(4):
                        for j in range(5):
                            nextImage = image[curY:curY+cutY, curX:curX+cutX]
                            resized = cv2.resize(nextImage, interpolation=cv2.INTER_AREA, dsize=(nextImage.shape[1]//6, nextImage.shape[0]//6))
                            imageCut.append(resized)
                            curX += cutX
                            # cv2.imshow('image' + str(i) + str(j), imageCut)
                            # cv2.waitKey(0)
                            # cv2.destroyAllWindows()
                        curY += cutY
                        curX = 0
                

                    cv2.imshow('image', image)
                    break
                    
        else:
            #match found, now open viewer and write rectangles
            if imageCut is not None:
                #end when it is black
                countNonBlack = cv2.countNonZero(gray_version)
                hx,wx = gray_version.shape
                totalpixels = hx*wx
                countBlack = totalpixels - countNonBlack
                #print("black count is ", countBlack, " out of ", totalpixels, " pixels")
                if countBlack > 0.8*totalpixels:
                    print("BLACK SCREEN, move to next image")
                    cv2.destroyAllWindows()
                    matchFound = False
                    imageSelected = None
                    imageCut = None
                
                else:
                #loop through and match each one
                    for i in range(len(imageCut)):
                        result = cv2.matchTemplate(datascaled, imageCut[i], cv2.TM_CCOEFF_NORMED)
                        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                        #print("searching for match: " + str(max_val))
                        if max_val > 0.85:
                            #show the image in cv2
                            #print("PIECE FOUND with chance of: " + str(max_val))
                            cv2.rectangle(datasmol, (max_loc[0]*6, max_loc[1]*6), (max_loc[0]*6 + imageCut[i].shape[1]*6, max_loc[1]*6 + imageCut[i].shape[0]*6), (0, 0, 255), 2)
                            cv2.putText(datasmol, "R" + str((i//5)+1) + "C"+str((i%5)+1), (max_loc[0]*6, max_loc[1]*6), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                    cv2.imshow("finder", datasmol)
                #cv2.imshow("smaller", datascaled)
                
                       



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
            imageSelected = None
            imageCut = None


loadAllImages()
runCV()