from math import sin,acos,sqrt,pi
import cv2
import numpy as np 
import pytesseract
from tool import *
import datetime
#############################Feuille Etalon#############################
#p0
x0=107
y0=31
#p1
x1=884
y1=y0
#p2
x2=x0
y2=668

#position zone à détecter
posidCSE=[771,167,125,17]
posCLient=[234,167,666,17,4]#[x0,y0,w,h,space]
wsociete=451
wtel=350
posTotal=[693,617,73,21]#[x0,y0,w,h]
posCode=[96,360,134,21,7]#[x0,y0,w,h,space]
posLib=[235,295]#[x0,w]
posPrix=[533,78]#[x0,w]
posQte=[613,73]#[x0,w]
posAto=[800,367,8,8,20]#[x0,y0,w,h,space]
##########################################################################
#PARAMS pour detection carré
Lrc=0
Hrc=80
Lvc=0
Hvc=80
Lbc=0
Hbc=80
dx=0.3
areaMin=100
#PARAM détection Ecriture
dilation=1
config = ("-l fra --oem 1 --psm 7")
element = cv2.getStructuringElement(cv2.MORPH_RECT, (dilation,dilation))
sigma=0.33
####################################################################
pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'

repertoireImgClient='C:/Users/jeann/Desktop/Parfumerie/CE V4/bdd/static/image_client'
repertoireImgCmd='C:/Users/jeann/Desktop/Parfumerie/CE V4/CE/bdd/static/image_cmd'
bdd="C:/Users/jeann/Desktop/Parfumerie/CE V4/bdd/bdd_hist_extraction.db"

# repertoireImgClient='/home/jamessou/CEPROG/bdd/static/image_client'
# repertoireImgCmd='/home/jamessou/CEPROG/bdd/static/image_cmd'
# bdd="/home/jamessou/CEPROG/bdd/bdd_hist_extraction.db"

parasites=[",",".",":",";"," ","-","_","None",'REFERENCE','Reference','Référence','reference','référence','REF','Ref','ref','Réf','réf','/']
LparasiteQte=["l","L","i","I"]
###################################

def transformImg(X0,Y0,X1,Y1,X2,Y2,img):
    #changement de repère de X1 pour calcul de theta
    t1=x0-X0
    t2=y0-Y0
    Xa1=X1+t1
    Ya1=Y1+t2
    #Rotation
    a=sqrt((Xa1-x1)**2+(Ya1-y1)**2)
    b=sqrt((Xa1-x0)**2+(Ya1-y0)**2)
    c=abs(x1-x0)
    #Signe 
    if Ya1<y1:
        s=1
    else:
        s=-1
    #Angle
    cosT=(b**2+c**2-a**2)/(2*b*c)
    sinT=s*sin(acos(cosT))
    teta=s*acos(cosT)
    angle=teta*180/pi
    #nvl coord de P'1 et P'2 après rotation/P'0
    Xb1=(X1-X0)*cosT-(Y1-Y0)*sinT+X0
    Yb2=(X2-X0)*sinT+(Y2-Y0)*cosT+Y0
    #Dilatation
    d1=(x1-x0)/(Xb1-X0)
    d2=(y2-y0)/(Yb2-Y0)
    
    ############## Transformation de l'image #################
    #Rotattion/centre image
    height, width = img.shape[:2]
    image_center = (width/2, height/2)
    bound_w = int(height * abs(sinT) + width * abs(cosT))
    bound_h = int(height * abs(cosT) + width * abs(sinT))
    M = cv2.getRotationMatrix2D(image_center,-angle,1)
    M[0, 2] += bound_w/2 - image_center[0]
    M[1, 2] += bound_h/2 - image_center[1]
    img_rot = cv2.warpAffine(img,M,(bound_w,bound_h))
    #Rescale avec d1 et d2
    width = int(img_rot.shape[1] * d1)
    height = int(img_rot.shape[0] * d2)
    dim = (width, height)
    resized = cv2.resize(img_rot, dim, interpolation = cv2.INTER_AREA)
    #nv coord de P'0 après rotation/centre
    Xr0=(X0-image_center[0])*cosT-(Y0-image_center[1])*sinT + image_center[0]+bound_w/2 - image_center[0]
    Yr0=(X0-image_center[0])*sinT+(Y0-image_center[1])*cosT + image_center[1]+bound_h/2- image_center[1]
    #nv coord de P'0 après dilatation
    Xd0=Xr0*d1
    Yd0=Yr0*d2
    #cv2.imshow("resized",resized)
    #Translation
    t1=x0-Xd0
    t2=y0-Yd0
    T = np.float32([ [1,0,t1], [0,1,t2] ])
    translated = cv2.warpAffine(resized, T, (width, height))
    return translated

def coordQRMire(img):
    ListCntCarre=[]
    ListHierarchy=[]
    kernel = np.ones((7,7),np.uint8)
    #Filtrage
    mask=cv2.inRange(img,(Lrc,Lvc,Lbc),(Hrc,Hvc,Hbc))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)#dilataion puis erosion
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    i=0
    for cnt in contours:
        #Detection si cnt est un carré
        rect = cv2.minAreaRect(cnt)
        box = cv2.boxPoints(rect)
        x0=box[0][0]
        y0=box[0][1]
        x1=box[1][0]
        y1=box[1][1]
        x2=box[2][0]
        y2=box[2][1]
        w=sqrt((x0-x1)**2+(y0-y1)**2)
        h=sqrt((x1-x2)**2+(y1-y2)**2)
        area = cv2.contourArea(cnt)
    
        if h>0:
            q=w/h
            if q>(1-dx) and q<(1+dx) and area>areaMin:
                ListCntCarre.append([cnt,i])
                ListHierarchy.append(hierarchy[0][i])
        i+=1
    #Vérification si les carré sont de type QR carré avec HIERARCHY
    coord=[]
    for i in range(len(ListCntCarre)-2):
        A=ListHierarchy[i]
        B=ListHierarchy[i+1]
        C=ListHierarchy[i+2]

        if A[2]==ListCntCarre[i+1][1] and B[0]==-1 and B[1]==-1 and B[2]==ListCntCarre[i+2][1] and C[0]==-1 and C[1]==-1 and C[2]==-1 :
            #récupération du carré extrérieur
            rect = cv2.minAreaRect(ListCntCarre[i][0])
            box = cv2.boxPoints(rect)
            x0=box[0][0]
            y0=box[0][1]
            x1=box[1][0]
            y1=box[1][1]
            x2=box[2][0]
            y2=box[2][1]
            x3=box[3][0]
            y3=box[3][1]
            box = np.int0(box)
            x=int((x0+x1+x2+x3)/4)
            y=int((y0+y1+y2+y3)/4)
            coord.append([x,y])
    return coord

def detectTxt(img_rot,idExtraction,nCE):
    req=["insert into client (idExtraction) values(?)",(idExtraction,)]
    ecriture_BDD(req)
    req=["select max(idclient) from client",()]
    idclient=lecture_BDD(req)[0]['max(idclient)']

    req=["insert into commande (idExtractionCmd,idclientCmd,corbeille) values(?,?,0)",(idExtraction,idclient)]
    ecriture_BDD(req)
    req=["select max(id_commande) from commande",()]
    idCmd=lecture_BDD(req)[0]['max(id_commande)']

    #getInfo client###########################
    x0=posCLient[0]
    y0=posCLient[1]
    w=posCLient[2]
    h=posCLient[3]
    space=posCLient[4]
    Ltext=[]
    for i in range(5):
        if i==0:
            w=wsociete
        elif i==3:
            w=wtel
        cropped,text=getImgText(x0,y0,h,w,space,i,img_rot)
        Ltext.append(text)
        if text!="no text":
            nom=str(idCmd)+"_"+str(i)
            cv2.imwrite(repertoireImgClient+"/"+nom+".jpg", cropped)

    #getIDCSE
    x0=posidCSE[0]
    y0=posidCSE[1]
    w=posidCSE[2]
    h=posidCSE[3]
    _,idCSE=getImgText(x0,y0,h,w,0,0,img_rot)

    #getTotal#######
    x0=posTotal[0]
    y0=posTotal[1]
    w=posTotal[2]
    h=posTotal[3]
    cropped,text=getImgText(x0,y0,h,w,0,0,img_rot)
    Ltext.append(text)
    if text!="no text":
        nom=str(idCmd)+"_5"
        cv2.imwrite(repertoireImgClient+"/"+nom+".jpg", cropped)

    req=["select entreprise from listingCE where corbeille=0",()]
    listingCE=lecture_BDD(req)
    
    if nCE=="":
        if idCSE=="no text":
            req=["select entreprise from listingCE where corbeille=0",()]
            listingCE=lecture_BDD(req)
            societeMax,ratio=getSocietor(Ltext[0],listingCE)
            if societeMax!="":
                req=["select idCE from listingCE where entreprise=? and corbeille=0",(societeMax,)]
                idCE=lecture_BDD(req)[0]['idCE']
            else:
                idCE="900099"
        else:
            idCE="900"+idCSE
    else:
        idCE=nCE

    date=datetime.datetime.today().strftime('%Y-%m-%d')
    #write client infos
    req=["update client set societe=?,client=?,mail=?,tel=?,adresse=?,idCEclient=? where idclient=?",(Ltext[0],Ltext[1],Ltext[2],Ltext[3],Ltext[4],idCE,idclient)]
    ecriture_BDD(req)
    req=["update commande set total=?,idCE=?,etatCmd=?,idclientHW=?,date=? where id_commande=?",(Ltext[5],idCE,0,1,date,idCmd)]
    ecriture_BDD(req)
    #############getInfo code############################
    x0Code=posCode[0]
    x0Lib=posLib[0]
    x0Prix=posPrix[0]
    x0Qte=posQte[0]
    y0=posCode[1]
    wCode=posCode[2]
    wLib=posLib[1]
    wPrix=posPrix[1]
    wQte=posQte[1]
    wAto=posAto[1]
    h=posCode[3]
    space=posCode[4]
    x0Ato=posAto[0]
    y0Ato=posAto[1]
    wAto=posAto[2]
    hAto=posAto[3]
    spaceAto=posAto[4]
    
    for i in range(9):
        #code
        imgCode,code=getImgText(x0Code,y0,h,wCode,space,i,img_rot)
        if code!="no text":
            req=["insert into facturation (idCmd) values (?)",(idCmd,)]
            ecriture_BDD(req)
            req=["select max(idProd) from facturation",()]
            idProd=lecture_BDD(req)[0]['max(idProd)']

            nom=str(idProd)+"_code"
            cv2.imwrite(repertoireImgCmd+"/"+nom+".jpg", imgCode)

            #lib
            imgLib,lib=getImgText(x0Lib,y0,h,wLib,space,i,img_rot)
            if lib!="no text":
                nom=str(idProd)+"_lib"
                cv2.imwrite(repertoireImgCmd+"/"+nom+".jpg", imgLib)

            #prix
            imgPrix,prix=getImgText(x0Prix,y0,h,wPrix,space,i,img_rot)
            if prix!="no text":
                nom=str(idProd)+"_prix"
                cv2.imwrite(repertoireImgCmd+"/"+nom+".jpg", imgPrix)

            #qte
            imgQte,qte=getImgText(x0Qte,y0,h,wQte,space,i,img_rot)
            if qte!="no text":
                nom=str(idProd)+"_qte"
                cv2.imwrite(repertoireImgCmd+"/"+nom+".jpg", imgQte)

            #atomiseur
            _,ato=getImgText(x0Ato,y0Ato,hAto,wAto,spaceAto,i,img_rot)
            if ato!="no text":
                ato="oui"
            else:
                ato="non"

            #verif si cmd errone
            for parasite in parasites:
                code=code.replace(parasite,"")
            errone,code,ean,libW=checkCode(code)
            if errone==0:
                errone=checkPrix(prix,code)
                if errone==0:
                    try:
                        for p in LparasiteQte:
                            if qte==p:
                                qte=1
                        intQte=int(qte)
                        if intQte<=0:
                            raise ValueError
                    except ValueError:
                        errone=3
            E=0
            req=["update facturation set code=?,ean=?,lib=?,libW=?,prix=?,qte=?,ato=?,errone=?,etatProd=?,idHW=?,etatMin=?,etatMax=? where idProd=?",(code,ean,lib,libW,prix,qte,ato,errone,E,1,E,E,idProd)]
            ecriture_BDD(req)
    return idCmd

def getImgText(x0,y0,h,w,space,i,img_rot):
    x1,y1=x0,y0+i*(h+space)
    x2,y2=x0+w,y0+i*(h+space)+h
    cropped=img_rot[y1:y2, x1:x2]
    min_y, min_x, _ = cropped.shape
    max_x=max_y = 0

    # apply automatic Canny edge detection using the computed median
    v = np.median(cropped)
    lower = int(max(0, (1.0 - sigma) * v))
    upper = int(min(255, (1.0 + sigma) * v))
    dilated = cv2.erode(cropped, element, iterations = 1)
    edged = cv2.Canny(dilated, lower, upper)
    contours,_ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) 
    for cnt in contours:
        (xcrop,ycrop,wcrop,hcrop) = cv2.boundingRect(cnt)
        min_x, max_x = min(xcrop, min_x), max(xcrop+wcrop, max_x)
        min_y,max_y=min(ycrop, min_y), max(ycrop+hcrop, max_y)
    if min_x<max_x-3 and min_y<max_y-3:
        analyse=dilated[min_y:max_y,min_x:max_x]
        cropped=cropped[min_y:max_y,min_x:max_x]
        #cv2.rectangle(img_rot,(x1,y1),(x2,y2),(255,60,60),1)
        try:
            text = pytesseract.image_to_string(analyse,config=config)
            text=text.replace("\n","")
            text=text[:-1]
        except :
            text="no text"
    else:
        text="no text"
    #cv2.putText(img_rot, text, (x1,y1), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)
    #cv2.imshow(str(i),analyse)
    return cropped,text

def reperator_angle(coord):
    #Récuperer les coordonnées
    x0=coord[2][0]
    y0=coord[2][1]
    x1=coord[1][0]
    y1=coord[1][1]
    x2=coord[0][0]
    y2=coord[0][1]
    Lpos=[[x0,y0],[x1,y1],[x2,y2]]
    #Calcul des distances
    a=sqrt((x0-x1)**2+(y0-y1)**2)
    b=sqrt((x0-x2)**2+(y0-y2)**2)
    c=sqrt((x2-x1)**2+(y2-y1)**2)
    L=[c,b,a]
    idMax=L.index(max(L))
    idMin=L.index(min(L))
    X0=Lpos[idMax][0]
    Y0=Lpos[idMax][1]
    X1=Lpos[idMin][0]
    Y1=Lpos[idMin][1]
    idLast=3-idMin-idMax
    X2=Lpos[idLast][0]
    Y2=Lpos[idLast][1]
    return(X0,Y0,X1,Y1,X2,Y2)

def extractHandwrite(lien,idExtraction,nCE):
    global Hrc
    global Hbc
    global Hvc
    global areaMin
    img = cv2.imread(lien)
    coord=coordQRMire(img)
    while len(coord)!=3 and Hrc<220:
        while areaMin<1000 and len(coord)!=3:
            copyImg=img.copy()
            areaMin+=100
            coord=coordQRMire(copyImg)
        Hrc+=5
        Hbc+=5
        Hvc+=5

    if len(coord)==3:
        X0,Y0,X1,Y1,X2,Y2=reperator_angle(coord)
        imgTrans=transformImg(X0,Y0,X1,Y1,X2,Y2,img)
        idCmd=detectTxt(imgTrans,idExtraction,nCE)
        #cv2.imshow("img",imgTrans)
        #cv2.waitKey()
        return idCmd
    else:
        raise TypeError

#extractHandwrite("C:/Users/ggpro/Desktop/prgrm detect handwriting/qrfeuille/bonCE.jpg",0,0)