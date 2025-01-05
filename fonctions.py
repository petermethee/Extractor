import csv
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

#TODO
def export_CSV1():
    req=["SELECT distinct idReliquat,reliquats.code,ean,libW,prix,reliquats.qte,id_commande,reliquats.lot,commande.idCE,entreprise,client.client,dateLot,utilisateur.prenom from reliquats join facturation on reliquats.code=facturation.code join commande on id_commande=facturation.idCmd  join listingCE on listingCE.idCE=commande.idCE JOIN utilisateur ON listingCE.referente=utilisateur.id JOIN client ON client.idclient=commande.idclientCmd where commande.lot=reliquats.lot and etatMin<2 and commande.corbeille=0 order by reliquats.code",()]
    Linfo=lecture_BDD(req)
    with open(exportFold+"/listing_reliquats.csv","w", encoding="utf-8") as csvfile:
        csvfile.write("Identifiant Unique reliquat;Code;EAN;Libelle;Prix unitaire;Quantite;ID Commande;Num Lot;CE;Nom du CE;Nom du client;Date lot;Referente\n")
        for row in Linfo:
            csvfile.write(';'.join(str(r) for r in row) + '\n')
#TODO
def export_CSV2():
    dateMin=datetime.today().strftime('%Y-%m-%d')
    dateMax=(datetime.today()-timedelta(365)).strftime('%Y-%m-%d')
    req=["SELECT  commande.date,facturation.code,facturation.libW,facturation.ean, facturation.qte, facturation.prix, facturation.idCmd,entreprise,commande.idCE,utilisateur.prenom from facturation JOIN commande ON facturation.idCmd=commande.id_commande join listingCE on listingCE.idCE=commande.idCE JOIN utilisateur ON listingCE.referente=utilisateur.id where etatProd like '%3%' AND date >? and date<?",(dateMin,dateMax)]
    Linfo=lecture_BDD(req)
    with open(exportFold+"/Ruptures.csv","w", encoding="utf-8") as csvfile:
        csvfile.write("Date Commande;Code;Libelle;EAN;Quantite;Prix unitaire;ID Commande;Nom du CE;Num CE;Referente\n")
        for row in Linfo:
            csvfile.write(';'.join(str(r) for r in row) + '\n')
#TODO
def export_CSV3():
    req=["SELECT distinct id_commande,date,commande.idCE,entreprise,client.client,dateLot,utilisateur.prenom from commande join listingCE on listingCE.idCE=commande.idCE JOIN utilisateur ON listingCE.referente=utilisateur.id  JOIN client ON client.idclient=commande.idclientCmd where commande.etatCmd=2 order by date",()]
    Linfo=lecture_BDD(req)
    with open(exportFold+"/Commande_a_livrer.csv","w", encoding="utf-8") as csvfile:
        csvfile.write("ID Commande;Date commande;ID CE;Nom du CE;Nom du client;Date lot;Referente\n")
        for row in Linfo:
            csvfile.write(';'.join(str(r) for r in row) + '\n')
#TODO
def export_CSV4():
    req=["SELECT idUnique,idCd,type,paiement.date,heure,montant,idPaiement,relance,client,client.mail,client.tel,listingCE.idCE,entreprise,utilisateur.prenom from paiement JOIN commande ON id_commande=idCd JOIN client ON idclientCmd=idclient join listingCE on commande.idCE=listingCE.idCE join utilisateur ON utilisateur.id=listingCE.referente WHERE lastOne=1 AND paiement.etat=0",()]
    Linfo=lecture_BDD(req)
    with open(exportFold+"/Impayes.csv","w", encoding="utf-8") as csvfile:
        csvfile.write("Identifiant Unique Paiement;ID Commande;Type de paiement;Date demande paiement;Heure demande paiement;Montant;ID Paiement;Numero relance;Nom du client;Mail client;Tel client;ID CE;Nom du CE;Referente\n")
        for row in Linfo:
            csvfile.write(';'.join(str(r) for r in row) + '\n')
#TODO
def export_CSV5():
    req=["SELECT idUnique,idCd,type,paiement.date,heure,montant,idPaiement,relance,client,client.mail,client.tel,listingCE.idCE,entreprise,utilisateur.prenom from paiement JOIN commande ON id_commande=idCd JOIN client ON idclientCmd=idclient join listingCE on commande.idCE=listingCE.idCE join utilisateur ON utilisateur.id=listingCE.referente WHERE lastOne=1 AND paiement.etat=0",()]
    Linfo=lecture_BDD(req)
    with open(exportFold+"/Impayes.csv","w", encoding="utf-8") as csvfile:
        csvfile.write("Identifiant Unique Paiement;ID Commande;Type de paiement;Date demande paiement;Heure demande paiement;Montant;ID Paiement;Numero relance;Nom du client;Mail client;Tel client;ID CE;Nom du CE;Referente\n")
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
    print(filename)
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
