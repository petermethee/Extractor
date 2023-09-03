from difflib import SequenceMatcher
import email
from time import time
import unicodedata
import sqlite3 as lite
from lxml import etree
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import PyPDF2
from flask import send_file
from simplecrypt import encrypt, decrypt
import datetime


bdd="C:/Users/jeann/Desktop/Parfumerie/CE_V4/bdd/bdd_hist_extraction.db"
bddCP="C:/Users/jeann/Desktop/Parfumerie/CE_V4/bdd/bdd_code_postal.db"
xmlARTICLE="C:/Users/jeann/Desktop/Parfumerie/CE_V4/xml/ARTICLE.xml"
xmlARTMAG="C:/Users/jeann/Desktop/Parfumerie/CE_V4/xml/ARTMAG.xml"
fact="C:/Users/jeann/Desktop/Parfumerie/CE_V4/Factures"

# bdd="/home/jamessou/CEPROG/bdd/bdd_hist_extraction.db"
# bddCP="/home/jamessou/CEPROG/bdd/bdd_code_postal.db"
# xmlARTICLE="/home/jamessou/xmlpm/ARTICLE.xml"
# xmlARTMAG="/home/jamessou/xmlpm/ARTMAG.xml"
# fact="/home/jamessou/CE/Factures"

EMAIL_ADDRESS="cseparfums@gmail.com"
PASSWORD="rdlyghzgsadlfeue"
Lcode=[]
passkey="par84fumerie700"

############Récupération BDD##############
#region
def lecture_BDD(requete):
    con=lite.connect(bdd)
    con.row_factory=lite.Row
    cur = con.cursor()
    cur.execute(requete[0], requete[1]) 
    lignes = cur.fetchall()
    con.close()
    return lignes

def ecriture_BDD(requete):
    con = lite.connect(bdd)
    cur = con.cursor()
    cur.execute(requete[0], requete[1])
    con.commit()
    con.close()
#endregion

#################Fonctions Jeanne#############
#region
def majusca(chaine):
    chaine = chaine.upper()
    chnorm = unicodedata.normalize('NFKD', chaine)
    return "".join([car for car in chnorm if not unicodedata.combining(car)])

def getSocietor(txt,liste):
    Lmots=majusca(txt).split(" ")
    LidSoc=[]
    for i in range (len(Lmots)):
        bloc=Lmots[i]
        for j in range (len(liste)):
            try:
                societe=majusca(liste[j]["entreprise"])
                LblocSoc=societe.split(" ")
                for blocSoc in LblocSoc:
                    ratio=SequenceMatcher(None, bloc, blocSoc).ratio()
                    if ratio==1:
                        LidSoc.append(j)
                        break
            except:
                pass
    if len(LidSoc)==0:
        txt=majusca(txt)
        motmax=""
        ratiomax=0
        for mot in liste:
            societe=mot['entreprise']
            try:
                ratio=SequenceMatcher(None, txt, majusca(societe)).ratio() 
                if ratio> ratiomax:
                    motmax=societe
                    ratiomax=ratio
            except:
                pass
    else:
        max=0
        idMax=0
        for x in LidSoc:
            qte=LidSoc.count(x)
            if qte>max:
                max=qte
                idMax=x
        motmax=liste[idMax]["entreprise"]
        ratiomax=1  
    return motmax,ratiomax
#endregion

######################fonction XML###########################
def getXML():
    global marque_ART,categorie_ART,produit_ART,gencod,libelle1,libelle2,longueur_ART,Lcode
    global marque_MAG,categorie_MAG,produit_MAG,mag_MAG,qte,longueur_MAG,prix
    #Liste xml ARTICLE
    print("1/4 Commencement")
    treeARTICLE=etree.parse(xmlARTICLE)
    marque_ART=treeARTICLE.xpath("/HF_DOCUMENT/Data/CMARQ")
    categorie_ART=treeARTICLE.xpath("/HF_DOCUMENT/Data/CCATEG")
    produit_ART=treeARTICLE.xpath("/HF_DOCUMENT/Data/CPROD")
    gencod=treeARTICLE.xpath("/HF_DOCUMENT/Data/GENCOD")
    libelle1=treeARTICLE.xpath("/HF_DOCUMENT/Data/DESIGN1")
    libelle2=treeARTICLE.xpath("/HF_DOCUMENT/Data/DESIGN2")
    longueur_ART=len(marque_ART)
    print("2/4 Fin de récupération du xml ARTICLE")

    #Liste xml ARTMAG
    treeARTMAG=etree.parse(xmlARTMAG)
    print("3/4 Fin de etree MAG")
    marque_MAG=treeARTMAG.xpath("/HF_DOCUMENT/Data/CMARQ")
    categorie_MAG=treeARTMAG.xpath("/HF_DOCUMENT/Data/CCATEG")
    produit_MAG=treeARTMAG.xpath("/HF_DOCUMENT/Data/CPROD")
    mag_MAG=treeARTMAG.xpath("/HF_DOCUMENT/Data/CMAG")
    qte=treeARTMAG.xpath("/HF_DOCUMENT/Data/QTESTK")
    prix=treeARTMAG.xpath("/HF_DOCUMENT/Data/PVAR")
    longueur_MAG=len(marque_MAG)

    indiceD=4*longueur_ART
    indiceF=5*longueur_ART
    #prix=prix[indiceD:indiceF]
    #marque_MAG=marque_MAG[:longueur_ART]
    #categorie_MAG=categorie_MAG[:longueur_ART]
    #produit_MAG=produit_MAG[:longueur_ART]
    print('len(mag_MAG)')
    print(len(mag_MAG))
    print('len(marque_MAG)')
    print(len(marque_MAG))

    for i in range (longueur_ART):
        code=marque_MAG[i].text+categorie_MAG[i].text+produit_MAG[i].text
        Lcode.append(code)
    longueur_MAG=len(marque_MAG)
    print("4/4 Fin : ARTMAG  ok")

def find_id_art(mq,ct,prod,marque,categorie,produit):
    for a in range (longueur_ART):
        if mq==marque[a].text:
            if ct==categorie[a].text:
                if prod==produit[a].text:
                    return a
    return(-1)

def find_id_art_v2(mq,ct,prod,mag,marque,categorie,produit,magasin):
    #print("Je recherche l'article :"+str(mq)+"."+str(ct)+"."+str(prod)+"dans le magasin"+str(mag))
    for a in range (longueur_MAG):
        if mq==marque[a].text:
            if ct==categorie[a].text:
                if prod==produit[a].text:
                    #print(magasin[a].text)
                    if mag==magasin[a].text:
                        #ligne=7+8*a
                        #print("Je suis à la ligne :" +str(ligne))
                        return a
    #print('je ne suis pas dans le XML')
    return(-1)

def getLcode():
    return Lcode

def checkCode(strCode):
    Lparariste=[".","-",",","_","/"]
    if len(strCode)>=8:
        for parasite in Lparariste:
            strCode=strCode.replace(parasite,"")
        strCode=strCode[:8]
        mq=strCode[:3]
        ct=strCode[3:5]
        prod=strCode[5:9]
        index=find_id_art(mq,ct,prod,marque_ART,categorie_ART,produit_ART)
        if index==-1:
            errone=1
            ean=""
            libW=""
        else :
            errone=0
            libW=libelle1[index].text+" "+libelle2[index].text
            ean=gencod[index].text
    else:
        errone=1
        ean=""
        libW=""
    return errone,strCode,ean,libW

def checkPrix(prixW ,strCode):
    mq=strCode[:3]
    ct=strCode[3:5]
    prod=strCode[5:9]
    index=find_id_art_v2(mq,ct,prod,'0004',marque_MAG,categorie_MAG,produit_MAG,mag_MAG)
    try:
        if float(prixW)==float(prix[index].text):
            errone=0
        else:
            errone=2
    except:
        errone=2
    return errone
    
def getPrix(strCode):
    strCode=strCode[:8]
    mq=strCode[:3]
    ct=strCode[3:5]
    prod=strCode[5:9]
    index=find_id_art_v2(mq,ct,prod,'0004',marque_MAG,categorie_MAG,produit_MAG,mag_MAG)
    return prix[index].text

def getStockSorgues(strCode):
    stock=['0','0']
    strCode=strCode[:8]
    mq=strCode[:3]
    ct=strCode[3:5]
    prod=strCode[5:9]
    index1=find_id_art_v2(mq,ct,prod,'0001',marque_MAG,categorie_MAG,produit_MAG,mag_MAG)
    index0=find_id_art_v2(mq,ct,prod,'0000',marque_MAG,categorie_MAG,produit_MAG,mag_MAG) 
    index=find_id_art(mq,ct,prod,marque_MAG,categorie_MAG,produit_MAG)
    stock[0]=qte[index0].text
    stock[1]=qte[index1].text
    return stock

def getStockAutres(strCode):
    stock=['0','0','0','0']
    if len(strCode)>=8:
        strCode=strCode[:8]
        mq=strCode[:3]
        ct=strCode[3:5]
        prod=strCode[5:9]
        index2=find_id_art_v2(mq,ct,prod,'0002',marque_MAG,categorie_MAG,produit_MAG,mag_MAG)
        index3=find_id_art_v2(mq,ct,prod,'0003',marque_MAG,categorie_MAG,produit_MAG,mag_MAG)
        index5=find_id_art_v2(mq,ct,prod,'0005',marque_MAG,categorie_MAG,produit_MAG,mag_MAG)
        index6=find_id_art_v2(mq,ct,prod,'0006',marque_MAG,categorie_MAG,produit_MAG,mag_MAG)
        stock[0]=qte[index2].text
        stock[1]=qte[index3].text
        stock[2]=qte[index5].text
        stock[3]=qte[index6].text
    return stock


####################COLISSIMO#######################
def lecture_BDDCP(requete):
    con=lite.connect(bddCP)
    con.row_factory=lite.Row
    cur = con.cursor()
    cur.execute(requete[0], requete[1]) 
    lignes = cur.fetchall()
    con.close()
    return lignes

def listeA(adr):
    Lnombre=[]
    Llettre=[]
    positionN=[]
    positionL=[]
    Lbloc=adr.split(" ")
    for i in range (len(Lbloc)):
        try:
            _=int(Lbloc[i])
            Lnombre.append(Lbloc[i])
            positionN.append(i)
        except Exception:
            Llettre.append(Lbloc[i])
            positionL.append(i)
    return(Lnombre,Llettre,positionN,positionL)

# forme les différentes possibilités de codes postaux
def CodePossible(nombre):
    LcodePossible=[]
    taille=int(len(nombre))
    for i in range (taille):
        j=0
        a=str(nombre[i])
        while len(a)<4 and i+j<taille:
            j=j+1
            a=a+str(nombre[i+j])
        if len(a)==5:
            LcodePossible.append(a)
    return(LcodePossible)
    
def codepostal(LcodePossible):
    BDDvilles=[]
    BDDcodes=[]
    for code in LcodePossible:
        req=["SELECT Commune FROM CodePostal WHERE Code=?",(str(code),)]
        valeurBDD=lecture_BDDCP(req)
        if len(valeurBDD)>0:
            BDDvilles.append(valeurBDD[0]['Commune'])
            BDDcodes.append(code)
    return([BDDvilles,BDDcodes])

def getVille(Lville,Llettre,LCP):
    LCommune=[]
    Lmot=[]
    res=[]
    for bloc in Llettre:
        Lmot.append(majusca(bloc))
    for ville in Lville:
        LCommune.append(majusca(ville))
        motmax=""
        ratiomax=0
        if ville.count(" ")!=0:
            sousville=ville.split(" ")
            RM=0
            for sousV in sousville:
                ratio=0
                for mot in Lmot:
                    try:
                        ratio=SequenceMatcher(None,sousV,mot).ratio()
                        if ratio> ratiomax:
                            ratiomax=ratio
                    except:
                        pass
                RM=RM+ratiomax
            ratiomoy=RM/len(sousville)
            res.append([ville,ratiomoy])
        else:
            for mot in Lmot:
                try:
                    ratio=SequenceMatcher(None, ville,mot).ratio()
                    if ratio> ratiomax:
                        motmax=ville
                        ratiomax=ratio
                except:
                    pass
            res.append([motmax,ratiomax])
    resRatio=0
    villeMax=""
    CP=""
    for i in range (len(res)):
        ratioelement=res[i][1]
        if ratioelement>resRatio:
            villeMax=res[i][0]
            resRatio=ratioelement
            CP=LCP[i]
    return (villeMax,CP)

def fixoumobile(tel):
    if len(tel)>1:
        indicatif=tel[0]+tel[1]
    else:
        indicatif=""
    mobile=""
    fixe=""
    liste=['.',',',' ','-','_','/']
    for c in liste:
        print(c)
        tel=tel.replace(c,'')
    if indicatif=='06' or indicatif=='07':
        mobile=tel
    else :
        fixe=tel   
    return(fixe,mobile)

###################### MAIL ##################

def send_email(clients,facture,rupt):
    #Récupération données clients
    
    email_clients=clients[0]
    print("email_clients")
    print(email_clients)
    prenom=clients[1]
    n_cde=clients[2]
    etat=clients[3:]
    print("etat f° send email")
    print(etat)
    html=getHTML(etat,prenom,n_cde,rupt,email_clients)

    #Écriture du message
    if len(etat)==1:
        subject="CSE Parfums - Suivi de votre commande n°"+n_cde
    else:
        subject="CSE Parfums - Paiement de votre commande n°"+n_cde
    print("apres if esle")
    msg=MIMEMultipart()
    msg['Subject'] = subject
    msg['To']=email_clients
    print("apres message")
    part=MIMEText(html,"html")
    print("apres part")
    for fact in facture:
        print("facture A")
        pdf = MIMEApplication(open(fact, 'rb').read())
        print("facture B")
        pdf.add_header('Content-Disposition', 'attachment', filename= "Facture.pdf")
        print("facture C")
        msg.attach(pdf)
        print("facture D")
    msg.attach(part) 
    try:
        """
        server = smtplib.SMTP('mail.cseparfums.com',25)
        """
        server = smtplib.SMTP('smtp.gmail.com',587)
        print("serveur")
        # server=smtplib.SMTP('SSL0.OVH.NET',587)
        # server.set_debuglevel(1)
        server.ehlo()
        print("serveur ehlo")
        server.starttls()
        print("serveur strat tls")
        server.login(EMAIL_ADDRESS,PASSWORD)
        print("serveur login")
        """message = 'Subject: {}\n\n{}'.format(subject, msg)"""
        print("EMAIL_ADDRESS")
        print(EMAIL_ADDRESS)
        print("email_clients")
        print(email_clients)
        server.sendmail(EMAIL_ADDRESS,email_clients, msg.as_string())
        print("serveur send mail")
        server.quit()
        print("serveur quit")
    except Exception as e:
        print("Echec : ",e)

def getHTML(etats,prenom,n_cde,rupt,mail):
    etat=etats[0]
    print("etat")
    print(etat)
    if len(etats)>1:
        montant=etats[1]
        nbrPdt=etats[2]
        adr=etats[3]
        idCmd=etats[4]
        idClient=etats[5]
        idCE=etats[6]
    else:
        adr=""
    HTML="""\
    <html>
    <style>
    body {
        font-family: 'Math';
        color:#000000;
        font-weight:normal;
        }
    h1 {
        font-size:15px;
        font-weight:normal;
        }
    h2 {
        font-size:15px;
        text-indent:2em;
        font-weight:normal;
        }
    h3 {
        font-size:10px;
        color:#555555;  
        font-style: italic;
        font-weight:normal;
        }
    h4 {
        font-size:15px;
        color:#fd4748;  
        font-style: italic;
        font-weight:normal;
        }

    </style>        
        <body>
        <h1>Bonjour """+prenom+""",</h1> """
    #Commande=préparation
    if etat==1:
        HTML+="""
            <br><h2>Nous vous informons que votre commande n°"""+n_cde+""" est en cours de préparation.</h2>
            <h2>Vous recevrez un mail, accompagné de votre facture, une fois que vos produits seront facturés.</h2>"""
        if adr!="":
            HTML+="""<h2>À noter que seule l'adresse notifiée sur le bon de commande sera prise en compte :"""+adr+"""</h2>"""
    #Commande=Facturée
    elif etat==2:
        HTML+="""
        <br><h2>Nous vous informons que votre commande n°"""+n_cde+""" est facturée.</h2>
            <h2>Vous trouverez ci-joint votre facture.</h2>
            <h2>Vous allez recevoir prochainement un mail pour le paiement de votre commande.</h2>
            <h2>Nous espérons vous revoir bientôt sur CSE Parfums ou dans nos boutiques.</h2>
        <h4>Attention :</h4> <h4>Pour les paiements en CB via le lien sécurisé, pensez à regarder également dans vos SPAM.</h4>"""
    #Commande=Reliquat+facturé
    elif etat==3:
        HTML+="""
        <br><h2>Nous vous informons que certains produits votre commande n°"""+n_cde+""" sont facturés.
            Vous trouverez ci-joint la facture concernant ces produits.</h2>
            <h2> Les autres produits sont en cours de préparation, vous recevrez prochainement un mail avec la facture associée.</h2>
        """
    #Commande=Reliquat uniquement
    elif etat==3.5:
        req=["SELECT idCE FROM commande WHERE id_commande=?",(n_cde,)]
        liste=lecture_BDD(req)
        idCE=liste[0]['idCE']
        req=["SELECT prenom,utilisateur.mail,niveau FROM utilisateur JOIN listingCE ON utilisateur.id=listingCE.referente WHERE idCE=?",(idCE,)]
        liste=lecture_BDD(req)
        niveau=liste[0]['niveau']
        mailRef=liste[0]['mail']
        HTML+="""
        <br><h2>Nous vous informons que les produits de votre commande n°"""+n_cde+""" ne sont pas présents dans notre stock. Afin de palier à ce problème, nous tentons de nous procurer les produits suivants dans nos boutiques partenaires :"""
        for x in rupt:
            HTML+="""<h2>- """+x[1]+""" : """+x[0]+""" </h2>"""
        HTML+="""
            <h2>Vous recevrez prochainement un mail vous indiquant l'état d'avancement de votre commande.</h2>
        """
    #Commande=rupture
    elif etat==4:
        req=["SELECT idCE FROM commande WHERE id_commande=?",(n_cde,)]
        liste=lecture_BDD(req)
        idCE=liste[0]['idCE']
        req=["SELECT prenom,utilisateur.mail,niveau FROM utilisateur JOIN listingCE ON utilisateur.id=listingCE.referente WHERE idCE=?",(idCE,)]
        liste=lecture_BDD(req)
        niveau=liste[0]['niveau']
        mailRef=liste[0]['mail']
        HTML+="""  
        <br><h2>Nous vous informons que certains produits de votre commande n°"""+n_cde+""" sont en rupture:</h2>"""
        for x in rupt:
            HTML+="""<h2>- """+x[1]+""" : """+x[0]+""" </h2>"""
        HTML+="""
            <h2> Revenez vers votre correspondant(e) CSE Parfums si vous souhaitez remplacer le(s) produit(s) en renseignant :</h2>
            <h2>-Le numéro de la commande :"""+n_cde+"""</h2>
            <h2>-La référence, la quantité et la désignation du (ou des) produit(s) en rupture</h2>
            <h2>-La référence, la quantité et la désignation du (ou des) produit(s)  remplaçant(s)</h2>"""
        if niveau=="REF":
            ref=liste[0]['prenom']
        else:
            ref="L'équipe CSE Parfums"
        HTML+="""<h2>Référent(e) :  """+ref+"""</h2>
        <h2>Coordonnées :  """+mailRef+"""</h2>"""   
    
    #Factures
    elif etat==99:
        HTML+="""
        <br><h2>Vous trouverez ci-joint les factures associées à votre commande n°"""+n_cde+""".</h2>
        """
    #Paiement RIB
    elif etat=="rib":
        n_commande=n_cde.split('-')[0]
        HTML+="""  
        <br><h2>Vous souhaitez un paiement par virement de votre commande n°"""+n_commande+""" : le montant est de """+montant+""" €.</h2>
        <h2> Voici les coordonnées IBAN :</h2>
        <h2> FR76 1130 6000 8492 5236 9205 037</h2>
        <h2> SAS PARFUMERIE MIREILLE</h2>
        <h2> 38 Place de la république</h2>
        <h2> 84700 Sorgues</h2>
        """
    #Paiement Lien
    elif etat=="lien":
        ref="Commande_"+idCmd+"_Client"+idClient+"_CE"+idCE
        n_commande=n_cde.split('-')[0]
    
        liste=prenom.split(" ")
        prenom1=liste[0]
        nom=""
        if len(liste)>1:
            for i in range (1,len(liste),1):
                nom+=str(liste[i])
        adresse,codePostal,ville=decompAdresse(adr)
        
        HTML+="""  
        <br><h2>Vous souhaitez un paiement de votre commande n°"""+n_commande+""" par lien CB:</h2>
        <h2> Voici le lien :</h2>
        <a href='https://www.parfumerie-en-ligne.com/testjdf/formulaire_CSE_HMAC.php?Mt="""+montant+"""&Ref="""+ref+"""&Mail="""+mail+"""&NbreProd="""+nbrPdt+"""&Prenom="""+prenom1+"""&Nom="""+nom+"""&Adr1="""+adresse+"""&Adr2=&CP="""+codePostal+"""&Ville="""+ville+"""'> Lien paiement</a>
        """
    #Paiement par espèces
    elif etat=="espece":
        n_commande=n_cde.split('-')[0]
        HTML+="""  
        <br><h2>Vous souhaitez un paiement par espèces de votre commande n°"""+n_commande+""" : le montant est de """+montant+""" €.</h2>
        """
    #Paiement par chèque recu
    elif etat=="chequeR":
        n_commande=n_cde.split('-')[0]
        HTML+="""  
        <br><h2>Vous souhaitez un paiement par chèque de votre commande n°"""+n_commande+""" : le montant est de """+montant+""" €.</h2>
        """
    #Paiement par chèque avant envoi
    elif etat=="chequeAV":
        n_commande=n_cde.split('-')[0]
        HTML+="""  
        <br><h2>Vous souhaitez un paiement par chèque de votre commande n°"""+n_commande+""" : le montant est de """+montant+""" €.</h2>
        """
    #Paiement par chèque après réception
    elif etat=="chequeAP":
        n_commande=n_cde.split('-')[0]
        HTML+="""  
        <br><h2>Vous souhaitez un paiement par chèque de votre commande n°"""+n_commande+""" : le montant est de """+montant+""" €.</h2>
        """
    #Paiement par autre
    elif etat=="autre":
        n_commande=n_cde.split('-')[0]
        HTML+="""  
        <br><h2>Paiement de votre commande n°"""+n_commande+""" : le montant est de """+montant+""" €.</h2>
        """

    #Pour tous les mails
    HTML+="""<br><br>
        <h1>Bonne réception,</h1>
        <br>
        <h1>Votre Equipe CSE Parfums / Parfumerie MPB</h1>
        <br><br>
        <h3>Veuillez noter que ce message vous a été envoyé d'une adresse qui ne peut recevoir d'e-mails. Merci de ne pas y répondre.</h3>
        <body>
    </html>
    """
    print("htmlOK")
    return(HTML)

def decompAdresse(adresse):
    if adresse=="" or None:
        return("","","")
    else:
        Lnombre,Llettre,_,_=listeA(adresse)
        LcodePossible=CodePossible(Lnombre)
        Lville,LCP=codepostal(LcodePossible)
        ville,CP=getVille(Lville,Llettre,LCP)
        ville=majusca(ville)
        adresse=majusca(adresse)
        rue1=adresse.replace(ville,"")
        rue=majusca(rue1.replace(CP,""))
        adr=rue.replace(" ","%20")
        return(adr,CP,ville)


def fusionnerPDF(liste,id):
    mergeFile = PyPDF2.PdfFileMerger()
    for _pdf in liste:
        if "pdf" in _pdf:
            mergeFile.append(PyPDF2.PdfFileReader(_pdf, 'rb'))
    titre=fact+"/factures-n°"+id+".pdf"
    mergeFile.write(titre)
    return(titre)

####### CONNEXION SESSION #####

def crypter(mdp):
    date1=datetime.datetime.today().strftime('%d-%m-%Y_%H:%M:%S')
    heure=date1.split('_')[1]
    print(heure)
    cipher = encrypt(passkey, mdp)
    date2=datetime.datetime.today().strftime('%d-%m-%Y_%H:%M:%S')
    heure2=date2.split('_')[1]   
    print(heure2)
    return(cipher)

def decrypter(mdpCrypt):
    date1=datetime.datetime.today().strftime('%d-%m-%Y_%H:%M:%S')
    heure=date1.split('_')[1]
    print(heure)
    cipher = decrypt(passkey, mdpCrypt)
    date2=datetime.datetime.today().strftime('%d-%m-%Y_%H:%M:%S')
    heure2=date2.split('_')[1]
    print(heure2)
    return(cipher)

