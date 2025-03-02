import csv
import os
import shutil
from flask import request
from tool import *
from constantes import *
from datetime import datetime, timedelta



def getListRef():
    req=["SELECT prenom,id FROM utilisateur WHERE niveau='REF'",()]
    listeRef=lecture_BDD(req)
    req=["SELECT prenom,id FROM utilisateur WHERE niveau='TOUT LE MONDE'",()]
    listeAll=lecture_BDD(req)
    return(listeRef,listeAll)

def filtre(valeur_user,variable):
    boolean=False
    if valeur_user!='-1':
        if variable=="" or variable==None or variable=="None":
            variable=valeur_user
        else:
            valeur_user=variable
    else:
        if variable=="" or variable==None  or variable=="None":
            valeur_user='-1'
            boolean=True
            variable=""
        else:
            valeur_user=variable
    return(valeur_user,variable,boolean)

def getValeurFormulaire(variable):
    valeur=request.form.get(variable)
    return(valeur)

def getListeForm(variable):
    valeur=request.form.getlist(variable)
    return(valeur)


def export_CSV1():
    req=["SELECT distinct idReliquat,reliquats.code,ean,libW,prix,reliquats.qte,id_commande,reliquats.lot,commande.idCE,entreprise,client.client,dateLot,utilisateur.prenom from reliquats join facturation on reliquats.code=facturation.code join commande on id_commande=facturation.idCmd  join listingCE on listingCE.idCE=commande.idCE JOIN utilisateur ON listingCE.referente=utilisateur.id JOIN client ON client.idclient=commande.idclientCmd where commande.lot=reliquats.lot and etatMin<2 and commande.corbeille=0 order by reliquats.code",()]
    Linfo=lecture_BDD(req)
    with open(exportFold+"/listing_reliquats.csv","w", encoding="utf-8") as csvfile:
        csvfile.write("Identifiant Unique reliquat;Code;EAN;Libelle;Prix unitaire;Quantite;ID Commande;Num Lot;CE;Nom du CE;Nom du client;Date lot;Referente\n")
        for row in Linfo:
            csvfile.write(';'.join(str(r) for r in row) + '\n')

def export_CSV2():
    dateMin=datetime.today().strftime('%Y-%m-%d')
    dateMax=(datetime.today()-timedelta(365)).strftime('%Y-%m-%d')
    req=["SELECT  commande.date,facturation.code,facturation.libW,facturation.ean, facturation.qte, facturation.prix, facturation.idCmd,entreprise,commande.idCE,utilisateur.prenom from facturation JOIN commande ON facturation.idCmd=commande.id_commande join listingCE on listingCE.idCE=commande.idCE JOIN utilisateur ON listingCE.referente=utilisateur.id where etatProd like '%3%' AND date >? and date<?",(dateMin,dateMax)]
    Linfo=lecture_BDD(req)
    with open(exportFold+"/Ruptures.csv","w", encoding="utf-8") as csvfile:
        csvfile.write("Date Commande;Code;Libelle;EAN;Quantite;Prix unitaire;ID Commande;Nom du CE;Num CE;Referente\n")
        for row in Linfo:
            csvfile.write(';'.join(str(r) for r in row) + '\n')

def export_CSV3():
    req=["SELECT distinct id_commande,date,commande.idCE,entreprise,client.client,dateLot,utilisateur.prenom from commande join listingCE on listingCE.idCE=commande.idCE JOIN utilisateur ON listingCE.referente=utilisateur.id  JOIN client ON client.idclient=commande.idclientCmd where commande.etatCmd=2 order by date",()]
    Linfo=lecture_BDD(req)
    with open(exportFold+"/Commande_a_livrer.csv","w", encoding="utf-8") as csvfile:
        csvfile.write("ID Commande;Date commande;ID CE;Nom du CE;Nom du client;Date lot;Referente\n")
        for row in Linfo:
            csvfile.write(';'.join(str(r) for r in row) + '\n')

def export_CSV4():
    dateMin=datetime.today().strftime('%Y-%m-%d')
    dateMax=(datetime.today()-timedelta(365)).strftime('%Y-%m-%d')
    req=["SELECT distinct paiement.idCd,type,paiement.date,paiement.montant,commande.date,entreprise,client.client,dateLot,utilisateur.prenom from paiement join commande ON commande.id_commande=paiement.idCd join listingCE on listingCE.idCE=commande.idCE JOIN utilisateur ON listingCE.referente=utilisateur.id JOIN client ON client.idclient=commande.idclientCmd where paiement.etat=1 AND commande.date>? AND commande.date<? order by commande.id_commande",(dateMin,dateMax)]
    Linfo=lecture_BDD(req)
    with open(exportFold+"/Paiements_payes_1_an.csv","w", encoding="utf-8") as csvfile:
        csvfile.write("ID Commande;Type de paiement;Date demande paiement;Montant;Date commande;Nom du CE;Nom du client;Date lot;Referente\n")
        for row in Linfo:
            csvfile.write(';'.join(str(r) for r in row) + '\n')

def export_CSV5():
    req=["SELECT id_commande,client,client.mail,client.tel,listingCE.idCE,entreprise,utilisateur.prenom from commande JOIN client ON idclientCmd=idclient join listingCE on commande.idCE=listingCE.idCE join utilisateur ON utilisateur.id=listingCE.referente WHERE etatCmd<2",()]
    Linfo=lecture_BDD(req)
    with open(exportFold+"/Commandes_en_preparation_et_en_facturation.csv","w", encoding="utf-8") as csvfile:
        csvfile.write("ID Commande;Nom du client;Mail client;Tel client;ID CE;Nom du CE;Referente\n")
        for row in Linfo:
            csvfile.write(';'.join(str(r) for r in row) + '\n')

def export_CSV6():
    dateMin=datetime.today().strftime('%Y-%m-%d')
    dateMax=(datetime.today()-timedelta(365)).strftime('%Y-%m-%d')
    req=["SELECT min(lot) from commande WHERE datelot>?",(dateMax)]
    lot=lecture_BDD(req)[0][0]
    req=["SELECT idReliquat,dateLot,reliquats.code,libW,ean,mag,reliquats.qte,facturation.prix,reliquats.lot,entreprise from reliquats join commande on reliquats.lot=commande.lot join facturation on id_commande=idCmd join listingCE on listingCE.idCE=commande.idCE WHERE reliquats.lot>?",(lot)]
    Linfo=lecture_BDD(req)
    with open(exportFold+"/Reliquats_et_ruptures_1_an.csv","w", encoding="utf-8") as csvfile:
        csvfile.write("Identifiant Unique reliquat;Date lot;Code;Libelle;EAN;Magasin;Quantite;Prix unitaire;Num Lot;Nom du CE\n")
        for row in Linfo:
            csvfile.write(';'.join(str(r) for r in row) + '\n')
def export_Impayes():
    req=["SELECT idUnique,idCd,type,paiement.date,heure,montant,idPaiement,relance,client,client.mail,client.tel,listingCE.idCE,entreprise,utilisateur.prenom from paiement JOIN commande ON id_commande=idCd JOIN client ON idclientCmd=idclient join listingCE on commande.idCE=listingCE.idCE join utilisateur ON utilisateur.id=listingCE.referente WHERE lastOne=1 AND paiement.etat=0",()]
    Linfo=lecture_BDD(req)
    with open(exportFold+"/Impayes.csv","w", encoding="utf-8") as csvfile:
        csvfile.write("Identifiant Unique Paiement;ID Commande;Type de paiement;Date demande paiement;Heure demande paiement;Montant;ID Paiement;Numero relance;Nom du client;Mail client;Tel client;ID CE;Nom du CE;Referente\n")
        for row in Linfo:
            csvfile.write(';'.join(str(r) for r in row) + '\n')

def export_Impayes_Synthese_CE():
    req=["SELECT listingCE.idCE,entreprise,utilisateur.prenom,SUM(montant) from paiement JOIN commande ON id_commande=idCd JOIN client ON idclientCmd=idclient join listingCE on commande.idCE=listingCE.idCE join utilisateur ON utilisateur.id=listingCE.referente WHERE lastOne=1 AND paiement.etat=0 GROUP BY listingCE.idCE ORDER BY listingCE.idCE",()]
    Linfo=lecture_BDD(req)
    with open(exportFold+"/Impayes_Synthese_CE.csv","w", encoding="utf-8") as csvfile:
        csvfile.write("ID CE;Nom du CE;Referente;Montant total estime\n")
        for row in Linfo:
            csvfile.write(';'.join(str(r) for r in row) + '\n')

def export_Impayes_Synthese_Referente():
    req=["SELECT utilisateur.prenom,SUM(montant) from paiement JOIN commande ON id_commande=idCd JOIN client ON idclientCmd=idclient join listingCE on commande.idCE=listingCE.idCE join utilisateur ON utilisateur.id=listingCE.referente WHERE lastOne=1 AND paiement.etat=0 GROUP BY utilisateur.prenom ORDER BY utilisateur.prenom",()]
    Linfo=lecture_BDD(req)
    with open(exportFold+"/Impayes_Synthese_Referente.csv","w", encoding="utf-8") as csvfile:
        csvfile.write("Referente;Montant total estime\n")
        for row in Linfo:
            csvfile.write(';'.join(str(r) for r in row) + '\n')

def export_Mail_Clients():
    req=["SELECT client,mail FROM client",()]
    Lmail=lecture_BDD(req)
    with open(exportFold+"/Mail_Clients.csv","w", encoding="utf-8") as csvfile:
        csvfile.write("Nom/Prénom;Mail\n")
        for row in Lmail:
            csvfile.write(';'.join(str(r) for r in row) + '\n')

def export_Infos_CE():
    req=["SELECT idCE,entreprise,referente,intermediaire,mail,tel,adresse,mailCl,mailInterPrep,mailInterFact,mailInterRelFact,mailInterRel,mailInterRupt,qteFact,sac,retraitMag,colisIndiv,colisCol,colisExpe,catalogue,commentaires FROM listingCE",()]
    Lmail=lecture_BDD(req)
    with open(exportFold+"/Infos_CE.csv","w") as csvfile:
        csvfile.write("Numero;Nom du CE;Referente;Intermediaire;Mail;Telephone;Adresse;Mail CLient;Mail CE Preparation;Mail CE Facturation;Mail CE Facturation+Reliquat;;Mail CE Reliquat;Mail CE Rupture;Factures;Sacs;Retrait Mag;Colis Individuel;Colis Collectif;Expedition;Catalogue;Commentaires\n")
        for row in Lmail:
            csvfile.write(';'.join(str(r) for r in row) + '\n')

def export_Commandes(maxD,minD):
    req=["SELECT * FROM commande WHERE date<=? and date>=? ",(maxD,minD)]
    Lcmd=lecture_BDD(req)
    with open(exportFold+"/Commandes.csv","w") as csvfile:
        csvfile.write("ID Client;ID extraction;ID CE;Societe;Nom prénom;Mail;Telephone;Adresse;Commentaire\n")
        for row in Lcmd:
            csvfile.write(';'.join(str(r) for r in row) + '\n')

def export_Paiements(maxD,minD):
    req=["SELECT * FROM paiement WHERE date<=? and date>=?",(maxD,minD)]
    Lcmd=lecture_BDD(req)
    with open(exportFold+"/Paiements.csv","w") as csvfile:
        csvfile.write("ID Unique;ID Commande;Type;Date;Etat;Heure;Relance;IDpaiement;LastOne\n")
        for row in Lcmd:
            csvfile.write(';'.join(str(r) for r in row) + '\n')

def export_Extractor_Stat():
    req=["SELECT qte,prix,code,libW,idHW,id_commande,date,dateLot,dateFact,referente,entreprise,listingCE.idCE from facturation join commande on id_commande=idCmd,listingCE where listingCE.idCE=commande.idCE and commande.corbeille=0",()]
    export=lecture_BDD(req)
    with open(statFold+"/Extractor_Stat.csv","w") as csvfile:
        csvfile.write("qte;prix;code;Libelle;idHW;id_commande;date;dateLot;dateFact;referente;entreprise;idCE\n")
        for row in export:
            csvfile.write(';'.join(str(r) for r in row) + '\n')

def write_log(user,texte):
    now = datetime.now()
    # Formater la date pour l'utiliser comme nom de fichier
    filename = logFold+"/"+now.strftime("%Y-%m")+".txt"
    # print(filename)
    # Créer et écrire dans le fichier
    with open(filename, "a") as f:
        log=str(now)+" user : "+user+" "+texte+"\n"
        f.write(log)
    # log=str(now)+" user : "+user+" "+texte+"\n"
    # fichier=open(filename,"w")
    # fichier.write(log)

def hist_paiement(type,idDetailCmd):
    req=["SELECT idUnique,date,heure,montant,etat,lastOne,idPaiement,relance from paiement where idCd=? AND type=? ORDER BY idPaiement DESC, relance DESC",(idDetailCmd,type)]
    return(lecture_BDD(req))

def f_particule(Particule):
    if Particule=="ChequeR":
        particule="chequeR"
    elif Particule=="ChequeAV":
        particule="chequeAV"
    elif Particule=="ChequeAP":
        particule="chequeAP"
    elif Particule=="Lien":
        particule="lien"
    elif Particule=="Rib":
        particule="rib"
    elif Particule=="Espece":
        particule="espece"
    else:
        particule="autre"
    return(particule)

def infos_dans_csv(chemin,nom,idExtraction,user):
    #nom='names.csv'
    with open(chemin+nom, newline='') as csvfile:
        lecture=csv.reader(csvfile, delimiter=';')
        liste=[]
        for row in lecture:
            liste.append(row)
            #print(row)
    n=len(liste)
    #Infos client
    client=liste[1][0]
    mail=liste[1][1]
    adresse=liste[1][2]
    tel=liste[1][3]
    idCE=int(liste[1][4])
    total=liste[1][9]
    req=["SELECT entreprise FROM listingCE where idCE=?",(idCE,)]
    try:
        societe=lecture_BDD(req)[0]['entreprise']
    except:
        idCE="900900"
        societe="Société non existante dans Extractor"
    req=["insert into client(idExtraction,client,mail,tel,adresse,societe,idCEclient) values (?,?,?,?,?,?,?)",(idExtraction,client,mail,tel,adresse,societe,idCE)]
    ecriture_BDD(req)
    req=["SELECT max(idclient) from client",()]
    idclient=lecture_BDD(req)[0]['max(idclient)']
    date=datetime.today().strftime('%Y-%m-%d')
    req=["insert into commande(idclientCmd,idExtractionCmd,total,idCE,idclientHW,etatCmd,date,corbeille,extractedBy,total) values (?,?,?,?,?,?,?,0,?,?)",(idclient,idExtraction,total,idCE,-1,0,date,user,total)]
    ecriture_BDD(req)
    req=["SELECT max(id_commande) from commande",()]
    idCmd=lecture_BDD(req)[0]['max(id_commande)']
    n=len(liste)
    #infos produit
    for i in range (1,n):
        strCode=str(liste[i][5])
        txtlib=liste[i][6]
        strQte=liste[i][7]
        rupture=liste[i][8]
        total=liste[i][9]
        if rupture =="OUI":
            ato="oui"
        else:
            ato="non"
        errone,strCode,ean,libW=checkCode(strCode)
        prix=getPrix(strCode)
        E=0
        req=["insert into facturation(idCmd,code,ean,lib,libW,prix,qte,ato,errone,idHW,etatProd,etatMin,etatMax) values (?,?,?,?,?,?,?,?,?,?,?,?,?)",(idCmd,strCode,ean,txtlib,libW,prix,strQte,ato,errone,-1,E,E,E)]
        ecriture_BDD(req)
    return(liste,idclient)  

def check_produit(etats):
    livre=False
    for etat in etats:
        if etat>2:
            livre=True
    return(livre)

def check_caracteres(texte):
    #vérifie si les caractères / \ ; sont présents dans le texte
    car=False
    value1=texte.find('/')
    value2=texte.find(';')
    value3=texte.find('\\')
    if value1>0 or value2>0 or value3>0:
        car=True
    return(car) 

def livrer_commande(idCmd,user):
    #Récuperer les différents produits de la commande
    req=["SELECT idProd FROM facturation WHERE idCmd=?",(idCmd,)]
    listePdt=lecture_BDD(req)
    print("listePdt")
    print(listePdt)
    en_cours=False
    for produit in listePdt:
        print("produit['idProd']")
        print(produit['idProd'])
        idProd=produit['idProd']
        #Changement état des produits livrés
        en_cours_prod,rupt_prod=change_etat_produit_livraison(idProd,user)
        print("en_cours_prod")
        print(en_cours_prod)
        if en_cours_prod==True:
            en_cours=True
    print("en_cours")
    print(en_cours)
    if en_cours==True:
        #Pas de changement d'états de la commande
        texte="Livraison de la commande n°"+str(idCmd)+" a été partiellement livré par "+str(user)
    else:
        #Changement état de la commande
        req=["UPDATE commande SET etatCmd=3,deliveredBy=? WHERE id_commande=?",(user,idCmd)]
        ecriture_BDD(req)    
        #Changement état des paiements
        req=["UPDATE paiement SET etat=3 WHERE idCd=? and etat=0",(idCmd,)]
        ecriture_BDD(req)
        texte="Livraison de la commande n°"+str(idCmd)+" a été livré par "+str(user)
    req=["SELECT etatCmd from commande where id_commande=?",(idCmd,)]
    etatCmd=lecture_BDD(req)[0]["etatCmd"]
    write_log(user,texte)
    return()

def change_etat_produit_livraison(idProd,user):#TODO
    etat='5'
    req=["SELECT qte,etatProd,etatMin,etatMax FROM facturation WHERE idProd=?",(idProd,)]
    liste=lecture_BDD(req)
    qte=liste[0]['qte']
    etatProd=liste[0]['etatProd']
    en_cours=False
    rupt=False
    print("qte")
    print(qte)
    print("etatProd")
    print(etatProd)
    #Cas qté =1
    if qte=='1':
        if etatProd=="1":
            en_cours=True
            texte="Le produit n°"+str(idProd)+" est toujours à l'état "+str(1)+" par "+str(user)
        elif etatProd=="2":
            req=["UPDATE facturation SET etatProd=?,etatMin=?,etatMax=? WHERE idProd=?",(etat,int(etat),int(etat),idProd)]
            ecriture_BDD(req)
            texte="Le produit n°"+str(idProd)+" a été mis à l'état "+str(etat)+" par "+str(user)
        elif etatProd=="3":
            rupt=True
            texte="Le produit n°"+str(idProd)+" est toujours à l'état "+str(3)+" par "+str(user)
        elif etatProd=="4":
            texte="Le produit n°"+str(idProd)+" est toujours à l'état "+str(4)+" par "+str(user)
        elif etatProd=="0":
            en_cours=True
            texte="Le produit n°"+str(idProd)+" est toujours à l'état "+str(0)+" par "+str(user)
        elif etatProd=="5":
            texte="Le produit n°"+str(idProd)+" est toujours à l'état "+str(5)+" par "+str(user)
    #Cas qté >1
    else:
        L=etatProd.split(";")
        Lfinale=""
        mini=5
        maxi=0
        for etats in L:
            #Définition du mini
            valeur_etats=int(etats)
            if valeur_etats<mini:
                mini=valeur_etats
            #Définition du maxi
            if valeur_etats>maxi:
                maxi=valeur_etats
            #Livraison de la commande
            if etat=='5':
                #Produit reliquat
                if etats=="1":
                    en_cours=True
                #Produit facturé
                if etats=="2":
                    etats="5"
                #Produit rupture
                elif etats=="3":
                    rupt=True
                #Produit annulé
                elif etats=="4": 
                    pass
                #en prepartion
                elif etats=="0":
                    en_cours=True
            Lfinale=Lfinale+etats+";"
        #Suppression du dernier point virgule
        Lfinale=Lfinale[:-1]
        req=["UPDATE facturation SET etatProd=?,etatMin=?,etatMax=? WHERE idProd=?",(Lfinale,mini,maxi,idProd)]
        ecriture_BDD(req)
        texte="Le produit n°"+str(idProd)+" a été mis à l'état "+str(Lfinale)+" par "+str(user)
    write_log(user,texte)
    return(en_cours,rupt)
    
def write_log_auto(user,texte):
    now = datetime.now()
    # Formater la date pour l'utiliser comme nom de fichier
    filename = logFold+"/extraction_auto"+now.strftime("%Y-%m")+".txt"
    # print(filename)
    # Créer et écrire dans le fichier
    with open(filename, "a") as f:
        log=str(now.strftime("%Y-%m-%d %H:%M:%S"))+" user : "+user+" "+texte+"\n"
        f.write(log)
    # log=str(now)+" user : "+user+" "+texte+"\n"
    # fichier=open(filename,"w")
    # fichier.write(log)    
def extraction_auto():
    #TODO mettre CE de tout le monde si vide ou non renseigné
    inc=0
    total=0
    #TODO definir le user auto
    user=0
    date=datetime.today().strftime('%Y-%m-%d')
    Lean,Lcode,Llib,Lprix,Lato,Lqte,LlibW=[],[],[],[],[],[],[]
    pas_error=True
    write_log_auto('automatique','INFO: Début de l extraction automatique')
    # fichier="commande-900900.csv"
    if os.listdir(extraction_auto_fold_todo)==[]:
        write_log_auto('automatique','INFO: Le repertoire est vide')
    for fichier in os.listdir(extraction_auto_fold_todo) :
        extension=fichier[-3:]
        write_log_auto('automatique','INFO: ---------------------------------------------')
        write_log_auto('automatique','INFO: -------------Debut du fichier '+fichier)
        write_log_auto('automatique','INFO: ---------------------------------------------')
        if extension!="csv":
            write_log_auto('automatique','WARNING: Le fichier '+fichier+' n a pas la bonne extension')
            write_log_auto('automatique','WARNING: >>>>>>>>>ECHEC de l extraction automatique<<<<<<<<')
            try:
                shutil.move(extraction_auto_fold_todo+fichier,extraction_auto_fold_KO+fichier)
                write_log_auto('automatique','INFO:Deplacement du fichier vers le repertoire Echec')
            except Exception as e:
                write_log_auto('automatique',"ERROR:"+str(e))
                write_log_auto('automatique','ERROR:>>>>>>>>>Echec du deplacement du fichier '+str(idclient)+' vers le repertoire Echec')
            write_log_auto('automatique','INFO: ---------------------------------------------')
            write_log_auto('automatique','INFO:-------------Fin du fichier '+fichier)
            write_log_auto('automatique','INFO: ---------------------------------------------')
        else:
            with open(extraction_auto_fold_todo+fichier,"r", encoding="utf-8") as csvFile:        
                for lines in csvFile:
                    #Infos titre
                    if inc==0:
                        inc+=1
                        # print("DEBUG: Je saute la première ligne")
                    #infos client / produits
                    else:
                        entreprise,idCE,client,mail,tel,adresse,livraison,adresse_livraison,type_paiement,code_pdt,designation,quantite,prix_U,sous_tot=lines.split(",")   
                        #Enlève les caractères " dans les csv
                        entreprise=entreprise.replace('"','')
                        client=client.replace('"','')
                        adresse=adresse.replace('"','')
                        livraison=livraison.replace('"','') 
                        designation=designation.replace('"','')
                        sous_tot=sous_tot.replace('\n',str())
                        sous_tot=sous_tot.replace("'",str())
                        sous_tot=sous_tot.replace('"',str())
                        # print("sous_tot")
                        # print(sous_tot)
                        #----------Check des infos
                        #Check CE
                        req=["SELECT entreprise FROM listingCE WHERE idCE=?",(idCE,)]
                        lecture_BDD(req)
                        if len(lecture_BDD(req))==0:
                            write_log_auto('automatique','WARNING: Le CE n est pas dans la liste des CE Extractor')
                            idCE=str(999410)
                            req=["SELECT entreprise FROM listingCE WHERE idCE=?",(idCE,)]
                            lecture_BDD(req)
                            if len(lecture_BDD(req))==0:
                                pas_error=False
                                write_log_auto('automatique','ERROR: Le CE 999410 n existe pas')

                        #Check client
                        if client=="":
                            pas_error=False
                            write_log_auto('automatique','ERROR: Le nom et prenom du client est vide')
                        #Check adresse
                        if adresse=="":
                            pas_error=False
                            write_log_auto('automatique','ERROR: L adresse du client est vide')
                        #Check livraison
                        if livraison=="":
                            pas_error=False
                            write_log_auto('automatique','ERROR:Le choix de livraison du client est vide')
                        #Check adresse livraison
                        if adresse_livraison=="":
                            pas_error=False
                            write_log_auto('automatique','ERROR: L adresse de livraison du client est vide')
                        #Check type paiement
                        if type_paiement=="":  
                            pas_error=False
                            write_log_auto('automatique','ERROR: Le type de paiement du client est vide')
                        #Check code produit
                        errone,code,ean,libW=checkCode(str(code_pdt))
                        # print("errone"+str(errone))
                        # print("code"+str(code))
                        # print("ean"+str(ean))
                        # print("libW"+str(libW))
                        prix=0
                        if errone==0:
                            prix=getPrix(code)
                        try:
                            total+=float(sous_tot)
                        except:
                            pass
                        Llib.append(designation)
                        LlibW.append(libW)
                        Lprix.append(prix)
                        Lcode.append(code)
                        Lean.append(ean)
                        Lqte.append(quantite)
                        Lato.append('non')
                # print("paserror"+str(pas_error))
            if pas_error:
                #TODO à relire
                print("Lcode"+str(Lcode))
                print("Lean"+str(Lean))
                commentaire="Extraction automatique"
                req=["insert into client (idCEclient,societe,client,mail,tel,adresse,commentaire) values(?,?,?,?,?,?,?)",(idCE,entreprise,client,mail,tel,adresse,commentaire)]
                ecriture_BDD(req)
                req=["SELECT max(idclient) from client",()]
                idclient=lecture_BDD(req)[0]["max(idclient)"]
                req=["insert into commande (idclientCmd,idCE,total,idclientHW,etatCmd,date,corbeille,createdBy) values(?,?,?,?,?,?,0,?)",(idclient,idCE,total,-1,0,date,user)]
                ecriture_BDD(req)
                req=["SELECT max(id_commande) from commande",()]
                idCmd=lecture_BDD(req)[0]['max(id_commande)']
                for i in range (len(Lcode)-1):
                    print("i:",i)
                    req=["insert into facturation (idCmd,code,ean,libW,lib,prix,qte,ato,errone,idHW,etatProd,etatMin,etatMax) values(?,?,?,?,?,?,?,?,?,?,?,?,?)",(idCmd,Lcode[i],Lean[i],LlibW[i],Llib[i],Lprix[i],Lqte[i],Lato[i],0,-1,0,0,0)]
                    write_log_auto('automatique','INFO: Ajout de la ligne '+str(i)+' avec le code '+str(Lcode[i])+' et la quantite '+str(Lqte[i]))
                    ecriture_BDD(req)
                try:
                    new_fichier='commande_'+str(idCmd)+'_OK.csv'
                    shutil.move(extraction_auto_fold_todo+fichier,extraction_auto_fold_OK+new_fichier)
                    write_log_auto('automatique','INFO: Deplacement du fichier '+str(idclient)+' vers le repertoire Traites')
                    write_log_auto('automatique','INFO: -----------Succes de l extraction automatique------------')

                except Exception as e:
                    write_log_auto('automatique',"ERROR:"+str(e))
                    write_log_auto('automatique','ERROR: >>>>>>>>>>Echec du deplacement du fichier vers le repertoire Traites')
                    write_log_auto('automatique','ERROR: -----------Succes de l extraction automatique mais echec du déplacement------------')
            else:
                write_log_auto('automatique','ERROR: >>>>>>>>>ECHEC de l extraction automatique<<<<<<<<')
                try:
                    shutil.move(extraction_auto_fold_todo+fichier,extraction_auto_fold_KO+fichier)
                    write_log_auto('automatique','INFO: Deplacement du fichier vers le repertoire Echec')
                except Exception as e:
                    write_log_auto('automatique',"ERROR:"+str(e))
                    write_log_auto('automatique','ERROR: >>>>>>>>>Echec du deplacement du fichier '+str(idclient)+' vers le repertoire Echec')
            write_log_auto('automatique','INFO:---------------------------------------------')
            write_log_auto('automatique','INFO:-------------Fin du fichier '+fichier)
            write_log_auto('automatique','INFO:---------------------------------------------')
    return()

