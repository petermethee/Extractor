#Importations
from json import tool
import re
from time import time
import PyPDF2 as pypdf
from pdf2image import convert_from_path
import os
import os.path
import shutil
from flask import Flask, request, render_template,jsonify,send_file,make_response,session,flash
import datetime
from detectHandwrite4 import extractHandwrite
from tool import lecture_BDD,ecriture_BDD,majusca,getSocietor,getXML,getLcode,checkCode,checkPrix,getPrix,getStockAutres,getStockSorgues,listeA,CodePossible,codepostal,getVille,fixoumobile,send_email,fusionnerPDF,crypter,decrypter
import json
from datetime import timedelta,datetime
import csv
from constantes import *
from fonctions import *

###FONCTIONS PAGE WEB###

def insertHistorique(monde,page,onglet,action,numero):
    date=datetime.today().strftime('%Y-%m-%d_%H:%M:%S')
    user=session['user']['id']
    req=["INSERT INTO historique (date,idUser,monde,page,onglet,action,numero) VALUES (?,?,?,?,?,?,?)",(date,user,monde,page,onglet,action,numero)]
    ecriture_BDD(req)


####################### Page Connexion Session ##########################################
#region
@app.route('/')	
def index():
    return render_template('_login.html')

def checkUser():
    try :
        session['user']
    except:
        return(index())   
    
@app.route('/login' ,methods=['GET', 'POST'])
def login():
    #formulaire
    mail=str(getValeurFormulaire("mail"))
    mdp=getValeurFormulaire("mdp")
    etat="INEXISTANT"
    #mdp=mdp.encode()
    #bdd
    try:
        session['user']
        session.permanent = True    
        app.permanent_session_lifetime = timedelta(minutes=480)
        write_log(str(session['user']['id']),"/login - Connexion avec cookie de l'utilisateur "+str(session['user']['id']))
        if session['user']['niveau']=="ADMIN":
            return render_template('dw_debutAdmin.html')
        else:
            return start(session['user']['id'])
    except:
        try:
            if mail=="":
                flash("Nom d'utilisateur non renseigné")
                return index()
            req=["SELECT id,mdp,prenom,nom,niveau,etat FROM utilisateur WHERE mail=?",(mail,)]
            liste=lecture_BDD(req)[0]
            id=liste['id']
            mdpBDD=liste['mdp']
            mdpC=mdpBDD
            #mdpC=decrypter(mdpBDD)
            prenom=liste['prenom']
            nom=liste['nom']
            niveau=liste['niveau']
            etat=liste['etat']
        except:
            mdpC=""
        #vérification mdp et utilisateur
        if mdp==mdpC and etat=="ACTIF":
            session['user']={
                'id':id,
                'username':prenom,
                'name' : nom,
                'email': mail,
                'niveau':niveau,
                'idExtraction':'0',
                'idCE':'0',
                "lot":'-1',
                "idCELivraison":'0',
                "idDetailCmd":'-1',
                "filtreDateMin":'-1',
                "filtreDateMax":'-1',
                "filtreID":'-1',
                "filtreCE":'-1',
                "filtreNom":'-1',
                "filtreEtat":'-1',
                "filtreMail":'-1',
                "filtreMontant":'-1',
                "paiementDateMin":'-1',
                "paiementDateMax":'-1',
                "paiementID":'-1',
                "paiementCE":'-1',
                "paiementLot":'-1',
                "paiementNom":'-1',
                "paiementType":'-1',
                "paiementMontant":'-1',
                "listeRelance":[],
                "paiement2BtEnlever":'non',
                "paiement2DateMin":'-1',
                "paiement2DateMax":'-1',
                "paiement2ID":'-1',
                "paiement2CE":'-1',
                "paiement2Lot":'-1',
                "paiement2Nom":'-1',
                "paiement2Type":'-1',
                "paiement2Montant":'-1',
                "PC":'-1',
                "page":'-1',
                "firstCo":'-1',
                "dwDateMin":'-1',
                "dwDateMax":'-1',
                "rechercheCE":'-1',
                "idPC":'-1'
            }
            session.permanent = True    
            app.permanent_session_lifetime = timedelta(minutes=660)
            write_log(str(session['user']['id']),"/login - Connexion sans cookie de l'utilisateur "+str(session['user']['id']))
            if session['user']['niveau']=="ADMIN":
                return render_template('dw_debutAdmin.html')
            else:
                return start(session['user']['id'])
        elif etat=="INEXISTANT":
            flash("Compte inexistant")
            return index()        
        elif etat=="INACTIF":
            flash("Compte inactif")
            return index()
        else:
            flash("Nom d'utilisateur et/ou mot de passe incorrect")
            return index()
#endregion

####################### Page Déconnexion Session ########################################
#region
# Expiration automatique de la session
@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=660)

@app.route('/logout')
def logout():
    write_log(str(session['user']['id']),"/logout - Deconnexion de l'utilisateur "+str(session['user']['id']))
    session['user']['firstCo']='-1'
    session.clear()
    return index()
#endregion

####################### Page Session Administrateur #####################################
#region
@app.route('/admin',methods=['GET', 'POST'])
def admin():
    checkUser()
    if session['user'] and session['user']['niveau']=="ADMIN": 
        action=getValeurFormulaire("action")
        if action=="1":
            write_log(str(session['user']['id']),"/admin - Connexion admin darkword de l'utilisateur"+str(session['user']['id']))
            return connexion()
            
        else:
            write_log(str(session['user']['id']),"/admin - Connexion admin classique de l'utilisateur"+str(session['user']['id']))
            return start(session['user']['id'])
    else:
        return start(session['user']['id'])
#endregion

####################### Monde du suivi des commandes - OngletSuivi ######################
#region
@app.route('/suivi/<user>',methods=['GET', 'POST'])
def suiviCmd(user):
    checkUser()
    action=getValeurFormulaire('filtre')
    #réactulisation du filtre 
    if action=='filtre':
        session['user']['filtreDateMin']="-1"
        session['user']['filtreDateMax']="-1"
        session['user']['filtreID']="-1"
        session['user']['filtreCE']="-1"
        session['user']['filtreNom']="-1"
        session['user']['filtreEtat']="-1"
        session['user']['filtreMail']="-1"
        session['user']['filtreMontant']="-1"
    #vérification de la sauvegarde des filtres
    if (session['user']['filtreDateMin']!='-1' or session['user']['filtreDateMax']!='-1' or session['user']['filtreID']!='-1' or session['user']['filtreCE']!='-1' or session['user']['filtreNom']!='-1' or session['user']['filtreEtat']!='-1' or session['user']['filtreMail']!='-1'or session['user']['filtreMontant']!='-1'):
        return(searchSuivi(user))
    ref=getValeurFormulaire("ref")
    if ref!=None:
        req=["SELECT id_commande,idCE,client,total,etatCmd,date from client join commande on idclient=idclientCmd where commande.corbeille=0 and idCE in (SELECT idCE from listingCE where listingCE.referente=? and corbeille=0) order by id_commande DESC LIMIT 1000",(ref,)]
        ref=int(ref)
        write_log(str(session['user']['id']),"/suivi - Filtre sur la référente "+str(ref))
    else:
        write_log(str(session['user']['id']),"/suivi - Aucun fltre sur la référente")
        req=["SELECT id_commande,idCE,client,total,etatCmd,date from client join commande on idclient=idclientCmd where commande.corbeille=0  order by id_commande DESC LIMIT 1000",()]
    Lclients=lecture_BDD(req)
    listeRef,listeAll=getListRef()
    return render_template('suivi_general.html',Lclients=Lclients,user=user,ref=ref,listeRef=listeRef,listeAll=listeAll)


@app.route('/searchSuivi/<user>',methods=['GET', 'POST'])
def searchSuivi(user):
    checkUser()
    dateMin=str(getValeurFormulaire("dateMin"))
    dateMax=str(getValeurFormulaire("dateMax"))
    idCmd=str(getValeurFormulaire("idCmd"))
    idCE=str(getValeurFormulaire("idCE"))
    client=getValeurFormulaire("client")
    etat=str(getValeurFormulaire("etat"))
    ref=str(getValeurFormulaire("ref"))
    mail=str(getValeurFormulaire("mail"))
    montant=str(getValeurFormulaire("montant"))
    sansDateMini=False
    sansDateMax=False
    a=False
    #Clés du filtre par session
    session['user']['filtreDateMin'],dateMin,sansDateMini=filtre(session['user']['filtreDateMin'],dateMin)
    session['user']['filtreDateMax'],dateMax,sansDateMax=filtre(session['user']['filtreDateMax'],dateMax)
    session['user']['filtreID'],idCmd,a=filtre(session['user']['filtreID'],idCmd)
    session['user']['filtreCE'],idCE,a=filtre(session['user']['filtreCE'],idCE)
    session['user']['filtreNom'],client,a=filtre(session['user']['filtreNom'],client)
    session['user']['filtreEtat'],etat,a=filtre(session['user']['filtreEtat'],etat)
    session['user']['filtreMail'],mail,a=filtre(session['user']['filtreMail'],mail)
    session['user']['filtreMontant'],montant,a=filtre(session['user']['filtreMontant'],montant)
    if ref=="None":
        ref1=""
    else:
        ref1=ref
    if etat!="1000":
        if sansDateMini:
            if sansDateMax:
                req=["SELECT DISTINCT(id_commande),commande.idCE,client,total,etatCmd,date from client join commande on idclient=idclientCmd left join listingCE on commande.idCE=listingCE.idCE where commande.corbeille=0 and id_commande LIKE ? and commande.idCE LIKE ? and client LIKE ? and etatCmd LIKE ? and referente LIKE ? and client.mail LIKE ? and total LIKE ? order by id_commande DESC LIMIT 1000",('%'+idCmd+'%','%'+idCE+'%','%'+client+'%','%'+etat+'%','%'+ref1+'%','%'+mail+'%','%'+montant+'%')]
                Lclients=lecture_BDD(req)
            else:
                req=["SELECT DISTINCT(id_commande),commande.idCE,client,total,etatCmd,date from client join commande on idclient=idclientCmd left join listingCE on commande.idCE=listingCE.idCE where commande.corbeille=0 and id_commande LIKE ? and commande.idCE LIKE ? and client LIKE ? and date<= (?) and etatCmd LIKE ? and referente LIKE ? and client.mail LIKE ? and total LIKE ? order by id_commande DESC LIMIT 1000",('%'+idCmd+'%','%'+idCE+'%','%'+client+'%',dateMax,'%'+etat+'%','%'+ref1+'%','%'+mail+'%','%'+montant+'%')]
                Lclients=lecture_BDD(req)
        elif sansDateMax:
            req=["SELECT DISTINCT(id_commande),commande.idCE,client,total,etatCmd,date from client join commande on idclient=idclientCmd left join listingCE on commande.idCE=listingCE.idCE where commande.corbeille=0 and id_commande LIKE ? and commande.idCE LIKE ? and client LIKE ? and date>= (?) and etatCmd LIKE ? and referente LIKE ? and client.mail LIKE ? and total LIKE ? order by id_commande DESC LIMIT 1000",('%'+idCmd+'%','%'+idCE+'%','%'+client+'%',dateMin,'%'+etat+'%','%'+ref1+'%','%'+mail+'%','%'+montant+'%')]
            Lclients=lecture_BDD(req)
        else:
            req=["SELECT DISTINCT(id_commande),commande.idCE,client,total,etatCmd,date from client join commande on idclient=idclientCmd left join listingCE on commande.idCE=listingCE.idCE where commande.corbeille=0 and id_commande LIKE ? and commande.idCE LIKE ? and client LIKE ? and date >= (?) and date <= (?) and etatCmd LIKE ? and referente LIKE ? and client.mail LIKE ? and total LIKE ? order by id_commande DESC LIMIT 1000",('%'+idCmd+'%','%'+idCE+'%','%'+client+'%',dateMin,dateMax,'%'+etat+'%','%'+ref1+'%','%'+mail+'%','%'+montant+'%')]
            Lclients=lecture_BDD(req)
    else:
        if sansDateMini:
            if sansDateMax:
                req=["SELECT DISTINCT(id_commande),commande.idCE,client,total,etatCmd,date from client join commande on idclient=idclientCmd left join listingCE on commande.idCE=listingCE.idCE where commande.corbeille=0 and id_commande LIKE ? and commande.idCE LIKE ? and client LIKE ? and referente LIKE ? and client.mail LIKE ? and total LIKE ? order by id_commande DESC LIMIT 1000",('%'+idCmd+'%','%'+idCE+'%','%'+client+'%','%'+ref1+'%','%'+mail+'%','%'+montant+'%')]
                Lclients=lecture_BDD(req)
            else:
                req=["SELECT DISTINCT(id_commande),commande.idCE,client,total,etatCmd,date from client join commande on idclient=idclientCmd left join listingCE on commande.idCE=listingCE.idCE where commande.corbeille=0 and id_commande LIKE ? and commande.idCE LIKE ? and client LIKE ? and date<= (?) and referente LIKE ? and client.mail LIKE ? and total LIKE ? order by id_commande DESC LIMIT 1000",('%'+idCmd+'%','%'+idCE+'%','%'+client+'%',dateMax,'%'+ref1+'%','%'+mail+'%','%'+montant+'%')]
                Lclients=lecture_BDD(req)
        elif sansDateMax:
            req=["SELECT DISTINCT(id_commande),commande.idCE,client,total,etatCmd,date from client join commande on idclient=idclientCmd left join listingCE on commande.idCE=listingCE.idCE where commande.corbeille=0 and id_commande LIKE ? and commande.idCE LIKE ? and client LIKE ? and date>= (?) and referente LIKE ? and client.mail LIKE ? and total LIKE ? order by id_commande DESC LIMIT 1000",('%'+idCmd+'%','%'+idCE+'%','%'+client+'%',dateMin,'%'+ref1+'%','%'+mail+'%','%'+montant+'%')]
            Lclients=lecture_BDD(req)
        else:
            req=["SELECT DISTINCT(id_commande),commande.idCE,client,total,etatCmd,date from client join commande on idclient=idclientCmd left join listingCE on commande.idCE=listingCE.idCE where commande.corbeille=0 and id_commande LIKE ? and commande.idCE LIKE ? and client LIKE ? and date >= (?) and date <= (?) and referente LIKE ? and client.mail LIKE ? and total LIKE ? order by id_commande DESC LIMIT 1000",('%'+idCmd+'%','%'+idCE+'%','%'+client+'%',dateMin,dateMax,'%'+ref1+'%','%'+mail+'%')]
            Lclients=lecture_BDD(req)
    listeRef,listeAll=getListRef()
    write_log(str(session['user']['id']),"/searchSuivi - Filtre avec les valeurs suivantes DateMax : "+str(session['user']['filtreDateMin'])+" // dateMin : "+str(session['user']['filtreDateMin'])+" // id : "+str(session['user']['filtreID'])+" // ce : "+str(session['user']['filtreCE'])+" // Nom : "+str(session['user']['filtreNom'])+"// Etat : "+str(session['user']['filtreEtat'])+"// Mail :"+str(session['user']['filtreMail'])+"// Montant :"+str(session['user']['filtreMontant']))
    return render_template('suivi_general.html',user=user,Lclients=Lclients,dateMin=dateMin,dateMax=dateMax,idCmd=idCmd,idCE=idCE,client=client,etat=etat,ref=ref,mail=mail,listeRef=listeRef,listeAll=listeAll,montant=montant)
    
@app.route('/suprCmd', methods=['GET', 'POST'])
def suprCmd():
    checkUser()
    user=session['user']['id']
    idCmd=getValeurFormulaire('idCmd')
    req=["UPDATE commande set corbeille=1,deletedBy=? where id_commande=?",(user,idCmd)]
    ecriture_BDD(req)
    req=["UPDATE facturation set etatMin=99,etatMax=99 where idCmd=?",(idCmd)]
    ecriture_BDD(req)
    write_log(str(session['user']['id']),"/suprCmd - Suppression de la commande n°"+str(idCmd))
    return jsonify()

@app.route('/annuleCmd', methods=['GET', 'POST'])
def annuleCmd():
    checkUser()
    user=session['user']['id']
    idCmd=getValeurFormulaire('idCmd')
    answer=getValeurFormulaire('answer')
    req=["UPDATE commande set justification=?,deletedBy=?,etatCmd=99 where id_commande=?",(answer,user,idCmd)]
    ecriture_BDD(req)
    #annuler tous les produits
    req=["SELECT * FROM facturation WHERE idCmd=?",(idCmd,)]
    listePdt=lecture_BDD(req)
    for produit in listePdt:
        try:
            qte=int(produit['qte'])
        except:
            qte==1
        idProd=produit['idProd']
        if qte==0 or qte==1:
            texte="4"
        else:
            texte=(qte-1)*"4;"+"4"
        req=["UPDATE facturation SET etatProd=?,etatMin=4, etatMax=4 where idProd=?",(texte,idProd)]
        ecriture_BDD(req)
    req=["UPDATE facturation set etatMin=4,etatMax=7 where idCmd=?",(idCmd)]
    ecriture_BDD(req)
    #annule les paiements associés
    req=["UPDATE paiement SET etat=2 where idCd=?",(idCmd,)]
    ecriture_BDD(req)
    write_log(str(session['user']['id']),"/annuleCmd - Annulation de la commande n°"+str(idCmd)+" pour la raison suivante "+str(answer))
    return '', 204

# Details #
@app.route('/detailsCmd/<user>', methods=['GET', 'POST'])
def detailsCmd(user):
    checkUser()
    idDetailCmd=session['user']['idDetailCmd']
    try:
        idDetailCmd=int(getValeurFormulaire('idCmd'))
        session['user']['idDetailCmd']=idDetailCmd
    except:
        pass
    paiementLien=hist_paiement('lien',idDetailCmd)
    paiementRib=hist_paiement('rib',idDetailCmd)
    paiementEspece=hist_paiement('espece',idDetailCmd)
    paiementChequeR=hist_paiement('chequeR',idDetailCmd)
    paiementChequeAV=hist_paiement('chequeAV',idDetailCmd)
    paiementChequeAP=hist_paiement('chequeAP',idDetailCmd)
    paiementAutre=hist_paiement('autre',idDetailCmd)
    previousPage=getValeurFormulaire("previousPage")
    if previousPage==None:
        previousPage="suivi"
    req=["SELECT * from client join commande on idclient=idclientCmd left join livraison on livraison.idlivraison=commande.idlivraison where id_commande=?",(idDetailCmd,)]
    client=lecture_BDD(req)
    LidUser=[client[0]['extractedBy'],client[0]['createdBy'],client[0]['modifiedBy'],client[0]['preparedBy'],client[0]['facturedBy'],client[0]['deliveredBy']]
    Luser=[]
    for x in LidUser:
        if x==None:
            Luser.append('null')
        else:
            req=["SELECT prenom FROM utilisateur WHERE id=?",(str(x),)]
            try :
                prenom=lecture_BDD(req)[0]['prenom']
                Luser.append(prenom)
            except:
                Luser.append('null')
    Ltitle=["Extrait par","Créé par","Modifié par","Préparé par","Facturé par","Livré par"]
    req=["SELECT * from facturation where idCmd=? and (etatProd like '%0%' or etatProd LIKE '%1%' or etatProd LIKE '%2%' or etatProd LIKE '%3%' or etatProd LIKE '%5%')",(idDetailCmd,)]
    Lcmd=lecture_BDD(req)
    req=["SELECT * from facturation where idCmd=? and etatProd like '%4%'",(idDetailCmd,)]
    LcmdAnnule=lecture_BDD(req)
    req=["SELECT prenom from commande join listingCE on listingCE.idCE=commande.idCE join utilisateur ON utilisateur.id=listingCE.referente where id_commande=?",(idDetailCmd,)]
    ref=lecture_BDD(req)
    if client[0]['idclientHW']==1:
        write_log(str(session['user']['id']),"/detailsCmd - Visualisation HW de la commande n°"+str(idDetailCmd))
        template="suivi_detailsHW.html"
    else:
        write_log(str(session['user']['id']),"/detailsCmd - Visualisation de la commande n°"+str(idDetailCmd))
        template="suivi_details.html"
    listeLien=["Lien CB",paiementLien,"Lien"]
    listeRIB=["RIB",paiementRib,"Rib"]
    listeChequeR=["Cheque reçu",paiementChequeR,"ChequeR"]
    listeChequeAV=["Cheque avant envoi",paiementChequeAV,"ChequeAV"]
    listeChequeAP=["Cheque apres reception",paiementChequeAP,"ChequeAP"]
    listeEspece=["Especes",paiementEspece,"Espece"]
    listeAutre=["Autres",paiementAutre,"Autre"]
    typePaiement=[listeLien,listeRIB,listeChequeR,listeChequeAV,listeChequeAP,listeEspece,listeAutre]
    #Liste des factures
    listePDF=[]
    nomPDF=[]
    qte=0
    for facture in os.listdir(app.config['FACTURE_FOLDER']) :
        if facture.startswith(str(idDetailCmd)+"-"):
            qte+=1
            splitFact=facture.split("-")
            year=splitFact[1]
            month=splitFact[2]
            day=splitFact[3]
            time=splitFact[4].split("_")
            h=time[0]
            min=time[1]
            sec=time[2].split(".")[0]
            nomPDF.append("Facture du "+day+"/"+month+"/"+year+" à "+h+":"+min+":"+sec)
            listePDF.append(app.config['FACTURE_FOLDER']+"/"+facture)
    return render_template(template,user=user,client=client,Lcmd=Lcmd,previousPage=previousPage,LcmdAnnule=LcmdAnnule,typePaiement=typePaiement,Luser=Luser,Ltitle=Ltitle,idDetailCmd=idDetailCmd,nomPDF=nomPDF,qte=qte,ref=ref)


@app.route('/actionFromDetails/<user>', methods=['GET', 'POST'])
def actionFromDetails(user):
    checkUser()
    action=getValeurFormulaire("action")
    idCmd=getValeurFormulaire("idCmd")
    idCE=getValeurFormulaire("idCE")
    total=getValeurFormulaire("total")
    date1=datetime.today().strftime('%Y-%m-%d_%H:%M:%S')
    date=date1.split('_')[0]
    heure=date1.split('_')[1]
    sendMail=False
    if action=="0":
        #Voir PDF
        for image in os.listdir(targetFile):
            if image.startswith(idCmd):
                return send_file(targetFile+"/"+image, as_attachment=True) 
        write_log(str(session['user']['id']),"/actionFromDetails - Visualisation du bon de commande n°"+str(idCmd))

    elif action=="1":
        #Exporter colissimo   
        req=["SELECT * from client where idclient in (SELECT idclientCmd from commande where id_commande=?)",(idCmd,)]
        client=lecture_BDD(req)[0]
        nom_prenom=majusca(client["client"])
        nom=nom_prenom.split(" ")[0]
        prenom=nom_prenom.replace(nom,"")
        mail=client["mail"].lower()
        tel=client["tel"]
        adresse=client["adresse"]
        Lnombre,Llettre,_,_=listeA(adresse)
        LcodePossible=CodePossible(Lnombre)
        Lville,LCP=codepostal(LcodePossible)
        ville,CP=getVille(Lville,Llettre,LCP)
        rue1=adresse.replace(ville,"")
        rue=majusca(rue1.replace(CP,""))
        if len(tel)>0:
            fixe,mobile=fixoumobile(tel)
        else:
            fixe=""
            mobile=""
        write_log(str(session['user']['id']),"/actionFromDetails - Export colissimo de la commande n°"+str(idCmd))
        return render_template("suivi_details_colissimo.html",user=user,ville=ville,CP=CP,rue=rue,nom=nom,prenom=prenom,mail=mail,fixe=fixe,mobile=mobile)
    
    elif action=="2":
        #Enregistrer les modifications
        societe=getValeurFormulaire("societe")
        client=majusca(getValeurFormulaire("client"))
        mail=getValeurFormulaire("mail").lower()
        tel=getValeurFormulaire("tel")
        adresse=majusca(getValeurFormulaire("adresse"))
        commentaire=getValeurFormulaire("commentaire")
        req=["UPDATE client set idCEclient=?,societe=?,client=?,mail=?,tel=?,adresse=?,commentaire=? where idclient=(SELECT idclientCmd from commande where id_commande=?)",(idCE,societe,client,mail,tel,adresse,commentaire,idCmd)]
        ecriture_BDD(req)

        req=["UPDATE commande set idCE=?,total=?,modifiedBy=? where id_commande=?",(idCE,total,user,idCmd)]
        ecriture_BDD(req)

        code=getListeForm("code")
        ean=getListeForm("ean")
        libW=getListeForm("libW")
        lib=getListeForm("lib")
        prix=getListeForm("prix")
        qte=getListeForm("qte")
        ato=getListeForm("ato")
        LidProd=getListeForm("idProd")

        for i in range(len(code)):
            if qte[i]!="":
                etatProd="0;"*(int(qte[i])-1)+"0"
            else:
                etatProd="0"
            if LidProd[i] in ato:
                if LidProd[i][0]=="n":
                    req=["insert into facturation (idCmd,code,ean,libW,lib,prix,qte,ato,errone,idHW,etatProd,etatMin,etatMax) values(?,?,?,?,?,?,?,?,?,?,?,?,?)",(idCmd,code[i],ean[i],libW[i],libW[i],prix[i],qte[i],"oui",0,-1,etatProd,0,0)]
                else:
                    req=["UPDATE facturation set code=?,lib=?,prix=?,qte=?,ato='oui',ean=?,libW=?,etatProd=? where idProd=?",(code[i],lib[i],prix[i],qte[i],ean[i],libW[i],etatProd,LidProd[i])]
            else:
                if LidProd[i][0]=="n":
                    req=["insert into facturation (idCmd,code,ean,libW,lib,prix,qte,ato,errone,idHW,etatProd,etatMin,etatMax) values(?,?,?,?,?,?,?,?,?,?,?,?,?)",(idCmd,code[i],ean[i],libW[i],lib[i],prix[i],qte[i],"non",0,-1,etatProd,0,0)]
                else:
                    req=["UPDATE facturation set code=?,lib=?,prix=?,qte=?,ato='non',ean=?,libW=?,etatProd=? where idProd=?",(code[i],lib[i],prix[i],qte[i],ean[i],libW[i],etatProd,LidProd[i])]  
            ecriture_BDD(req)
        write_log(str(session['user']['id']),"/actionFromDetails - Enregistrement des modifications de la commande n°"+str(idCmd))
    elif action=="3":
        #Afficher les factures
        listePDF=[]
        qte=0
        for facture in os.listdir(app.config['FACTURE_FOLDER']) :
            if facture.startswith(idCmd+"-"):
                qte+=1
                listePDF.append(app.config['FACTURE_FOLDER']+"/"+facture)
        if qte>0:
            return send_file(fusionnerPDF(listePDF,idCmd), as_attachment=True)
        #cas aucun facture
        write_log(str(session['user']['id']),"/actionFromDetails - Visualisation des factures de commande la n°"+str(idCmd))
    elif action=="4":
        #duplique la commande
        req=["SELECT idclientCmd FROM commande WHERE id_commande=?",(idCmd,)]
        idClient=lecture_BDD(req)[0]["idclientCmd"]
        req=["SELECT UPPER(idCEclient),UPPER(societe),UPPER(client),UPPER(mail),UPPER(tel),UPPER(adresse) FROM client WHERE idclient=?",(idClient,)]
        client=lecture_BDD(req)[0]
        req=["SELECT * FROM facturation WHERE idCmd=?",(idCmd,)]
        Lcode=lecture_BDD(req)
        #duplique le client
        req=["INSERT INTO client (idCEclient,societe,client,mail,tel,adresse) values (?,?,?,?,?,?)",(client["UPPER(idCEclient)"],client["UPPER(societe)"],client["UPPER(client)"],client["UPPER(mail)"],client["UPPER(tel)"],client["UPPER(adresse)"])]
        ecriture_BDD(req)
        #recupère id client
        req=["SELECT MAX(idclient) FROM client WHERE upper(idCEclient)=? AND upper(societe)=? AND upper(client)=? AND upper(mail)=? AND upper(tel)=? AND upper(adresse)=?",(client["UPPER(idCEclient)"],client["UPPER(societe)"],client["UPPER(client)"],client["UPPER(mail)"],client["UPPER(tel)"],client["UPPER(adresse)"])]
        idClient=lecture_BDD(req)[0]["MAX(idclient)"]
        #création de la commande avec l'id client
        req=["insert into commande (idclientCmd,idCE,total,idclientHW,etatCmd,date,corbeille,createdBy) values(?,?,?,?,?,?,0,?)",(idClient,idCE,total,-1,0,date,user)]
        ecriture_BDD(req)
        req=["SELECT MAX(id_commande) FROM commande",()]
        newIdCmd=lecture_BDD(req)[0]["MAX(id_commande)"]
        #ajout des produits dans le tableau facturation
        for i in range(len(Lcode)):
            req=["insert into facturation (idCmd,code,ean,libW,lib,prix,qte,ato,errone,idHW,etatProd,etatMin,etatMax) values(?,?,?,?,?,?,?,?,?,?,?,?,?)",(newIdCmd,Lcode[i]["code"],Lcode[i]["ean"],Lcode[i]["libW"],Lcode[i]["lib"],Lcode[i]["prix"],Lcode[i]["qte"],Lcode[i]["ato"],0,-1,0,0,0)]
            ecriture_BDD(req)
        req=["INSERT INTO stats  (date,idUser,action,cde,pdt,lot) VALUES (?,?,?,?,?,?)",(date,user,'ajouter',1,len(Lcode),newIdCmd)]
        ecriture_BDD(req)
        session['user']['idDetailCmd']=newIdCmd
        write_log(str(session['user']['id']),"/actionFromDetails - Duplication de la commande n°"+str(idCmd))
        return (suiviCmd(user))
    elif action=="5":
        #Voir infos CE
        write_log(str(session['user']['id']),"/actionFromDetails - Visualisation des infos CE de la commande n°"+str(idCmd))
        session['user']['page']="detailCommande"
        return facturationInfo(user)

    elif action=="factures":  
        #Partage de nouvelles factures
        date=datetime.today().strftime('%Y-%m-%d-%H_%M_%S')      
        req=["SELECT id_commande,mail,client,idCE from commande join client on idclientcmd=idclient WHERE id_commande=?",(idCmd,)]
        cmd=lecture_BDD(req)
        Linfo=[cmd[0]["mail"],cmd[0]["client"],str(cmd[0]["id_commande"]),99]
        Lfiles=request.files.getlist("file")
        i=0
        LidFact=[]
        for file in Lfiles:
            if file.filename!='':
                ext=file.filename.split(".")[1]
                file.save(os.path.join(app.config['FACTURE_FOLDER'],str(cmd[i]["id_commande"])+"-"+date+"."+ext))
                LidFact.append(cmd[0]["id_commande"])
            i=i+1
        Lfact=[]
        if cmd[0]["id_commande"] in LidFact:
            for facture in os.listdir(app.config['FACTURE_FOLDER']) :
                if facture.startswith(str(cmd[0]['id_commande'])+"-"):
                    Lfact.append(app.config['FACTURE_FOLDER']+"/"+facture)
        send_email(Linfo,Lfact,[])
        return (detailsCmd(user))
        
    elif "relance" in action:
        Particule=action.split('relance')[1]
        particule=f_particule(Particule)
        
        idPaiement=getValeurFormulaire("idPaiement"+Particule)
        relance=getValeurFormulaire("idRelance"+Particule)
        montant=getValeurFormulaire("idMontant"+Particule)
        idUnique=getValeurFormulaire("idUnique"+Particule)
        #Montant avec 2 décimales
        montant='%.2f'%float(montant)
        req=["SELECT mail FROM facturation JOIN commande ON id_commande=idCmd JOIN client ON idclientCmd=idclient WHERE idCmd=?",(idCmd,)]
        mail=lecture_BDD(req)[0]["mail"]
        if mail=="" or mail is None:
            sendMail=False
        else:
            #Annuler les paiements précédents et enlever le lastOne
            req=["UPDATE paiement SET etat=2,lastOne=0 WHERE idUnique=?",(idUnique,)]
            ecriture_BDD(req)
            #Créer la nouvelle demande de paiement et du lastOne
            relance=int(relance)+1
            req=["INSERT INTO paiement (idCd,type,date,heure,etat,montant,relance,idPaiement,lastOne) VALUES (?,?,?,?,?,?,?,?,?)",(idCmd,particule,date,heure,0,montant,relance,idPaiement,1)]
            ecriture_BDD(req)
            action2=particule
            sendMail=True
            write_log(str(session['user']['id']),"/actionFromDetails - Relance de paiement "+str(particule)+" de la commande n°"+str(idCmd))



    elif "annule" in action:
        Particule=action.split('annule')[1]
        particule=f_particule(Particule)
        idPaiement=getValeurFormulaire("idPaiement"+Particule)
        relance=getValeurFormulaire("idRelance"+Particule)
        montant=getValeurFormulaire("idMontant"+Particule)
        idUnique=getValeurFormulaire("idUnique"+Particule)
        #Annule la demande de paiement
        req=["UPDATE paiement SET etat=2 WHERE idUnique=?",(idUnique,)]
        ecriture_BDD(req)
        write_log(str(session['user']['id']),"/actionFromDetails - Annulation du paiement "+str(particule)+" de la commande n°"+str(idCmd))

        return (detailsCmd(user))
    elif action=="livrer":
        livrer_commande(idCmd,user)
        return (detailsCmd(user))

    else:
        montant1=getValeurFormulaire("montant")
        if montant1=="" or montant1=="0":
            return '', 204
        else:
            montant1.replace(",",".")
            montant=str("%.2f" % float(montant1))
            
            etat="0"
            relance=0
            action2=action
            req=["SELECT MAX(idPaiement) FROM paiement WHERE idCd=? and type=?",(idCmd,action)]
            idP=lecture_BDD(req)[0]['MAX(idPaiement)']
            if idP!=None:
                idPaiement=int(idP)+1
            else:
                idPaiement=1
            req=["SELECT mail FROM facturation JOIN commande ON id_commande=idCmd JOIN client ON idclientCmd=idclient WHERE idCmd=?",(idCmd,)]
            mail=lecture_BDD(req)[0]["mail"]
            if mail=="" or mail is None:
                sendMail=False
            else:
                req=["INSERT INTO paiement (idCd,type,date,heure,etat,montant,relance,idPaiement,lastOne) VALUES (?,?,?,?,?,?,?,?,?)",(idCmd,action,date,heure,etat,montant,relance,idPaiement,1)]
                ecriture_BDD(req)
                sendMail=True
                write_log(str(session['user']['id']),"/actionFromDetails - Demande de paiement de la commande n°"+str(idCmd))


    if sendMail:
        req=["SELECT SUM(qte),idclientCmd,commande.idCE,client.adresse,client.mail,client,referente FROM facturation JOIN commande ON id_commande=idCmd JOIN client ON idclientCmd=idclient JOIN listingCE ON listingCE.idCE=commande.idCE where idCmd=?",(idCmd,)]
        liste=lecture_BDD(req)
        nbrPdt=liste[0]["SUM(qte)"]
        idClient=liste[0]["idclientCmd"]
        idCE=liste[0]["idCE"]
        adresse=str(liste[0]["adresse"])
        mail=liste[0]["mail"]
        client=liste[0]["client"]
        idRef=liste[0]["referente"]
        #todo jeanne 18/06
        if mail!="" or mail!=None:
            idCdMail=str(idCmd)+'-'+str(idPaiement)+'-'+str(relance)
            send_email([str(mail),str(client),str(idCmd),action2,montant,str(nbrPdt),adresse,idCdMail,str(idClient),str(idCE),str(idRef)],[],[])
        return (detailsCmd(user))
    else:
        return '',204
    

@app.route('/extractColissimo/<user>', methods=['GET','POST'])
def extractColissimo(user):
    checkUser()
    bouton=getValeurFormulaire("bouton")
    if bouton=="0":
        car_interdit=False
        Lcar=[]
        Linfo=[getValeurFormulaire("nom"),getValeurFormulaire("prenom"),getValeurFormulaire("fixe"),getValeurFormulaire("mobile"),getValeurFormulaire("mail"),getValeurFormulaire("rue"),getValeurFormulaire("CP"),getValeurFormulaire("ville"),getValeurFormulaire("res"),getValeurFormulaire("couls"),getValeurFormulaire("lieu_dit"),getValeurFormulaire("instructions")]
        nom=Linfo[0]
        prenom=Linfo[1]
        fixe=Linfo[2]
        mobile=Linfo[3]
        mail=Linfo[4]
        rue=Linfo[5]
        CP=Linfo[6]
        ville=Linfo[7]
        res=Linfo[8]
        couls=Linfo[9]
        lieu_dit=Linfo[10]
        instructions=Linfo[11]
        for texte in Linfo:
            Lcar.append(check_caracteres(texte))
        if True in Lcar:
            car_interdit=True
        if car_interdit==False:
            with open(exportFold+"/"+nom+prenom+"_extractor.csv","w") as csvfile:
                csvfile.write('Référence;;Raison sociale;Service;Prénom;Nom;Etage couloir escalier;Entrée bâtiment;N° et voie;Lieu dit;Code postal;Commune;Code ISO du pays;Téléphone fixe;Téléphone portable;Email;Code porte1;Code porte2;Interphone;Instructions de livraison;Nom commercial chargeur\n')
                csvfile.write(';;;;'+prenom+';'+nom+';'+couls+';'+res+';'+rue+';'+lieu_dit+';'+CP+';'+ville+';FR;'+fixe+';'+mobile+';'+mail+';;;;;'+instructions+';')
            write_log(str(session['user']['id']),"/extractColissimo -Extraction colissimo réussie")
            return detailsCmd(user)
        else:
            write_log(str(session['user']['id']),"/extractColissimo -Extraction colissimo échouée")
            return render_template("suivi_details_colissimo.html",user=user,ville=ville,CP=CP,rue=rue,nom=nom,prenom=prenom,mail=mail,fixe=fixe,mobile=mobile,couls=couls,res=res,instructions=instructions,lieu_dit=lieu_dit)
    return detailsCmd(user)      

@app.route('/annuler', methods=['GET', 'POST'])
def annuler():
    checkUser()
    idcmd=getValeurFormulaire("id")
    req=["UPDATE facturation set etatProd=4,etatMin=4,etatMax=4 where idProd=?",(idcmd,)]
    ecriture_BDD(req)
    write_log(str(session['user']['id']),"/annuler - Annulation d'un produit de la commande n°"+str(idcmd))
    return jsonify()
    
@app.route('/addCmd/<user>', methods=['GET', 'POST'])
def addCmd(user):
    checkUser()
    req=["SELECT idclient,client,idCEclient,date from client join commande on idclientCmd=idclient order by date desc",()]
    Lclients=lecture_BDD(req)
    req=["SELECT idCE from listingCE where corbeille=0 order by idCE",()]
    LCE=lecture_BDD(req)
    Lcode=getLcode()
    write_log(str(session['user']['id']),"/addCmd - Ajout d'une commande")
    return render_template('suivi_addCmd.html',user=user,Lclients=Lclients,LCE=LCE,Lcode=Lcode)
    

@app.route('/addProd', methods=['GET', 'POST'])
def addProd():
    checkUser()
    code=getValeurFormulaire("code")
    ato=getValeurFormulaire("ato")
    errone,code,ean,lib=checkCode(code)
    prix=0
    date=""
    if errone==0:
        prix=getPrix(code)
        dateLim=datetime.today()+timedelta(delaiRupt)
        req=["SELECT date from rupture where rupt_code=? and date>?",(code,dateLim)]
        l=lecture_BDD(req)
        if len(l)>0:
            date=l[0]["date"]
            errone=-1
    write_log(str(session['user']['id']),"/addProd - Ajout du produit : "+str(code))
    return jsonify(lib=lib,prix=prix,ato=ato,ean=ean,errone=errone,date=date)
    

@app.route('/valinuler/<user>', methods=['GET', 'POST'])
def valinuler(user):
    checkUser()
    mode=getValeurFormulaire("mode")
    if mode!="0":
        idCE=getValeurFormulaire("idCE")
        societe=getValeurFormulaire("societe")
        client=majusca(getValeurFormulaire("client"))
        mail=getValeurFormulaire("mail").lower()
        tel=getValeurFormulaire("tel")
        adresse=majusca(getValeurFormulaire("adresse"))
        total=getValeurFormulaire("total")
        commentaire=getValeurFormulaire("commentaire")
        date=datetime.today().strftime('%Y-%m-%d')

        req=["insert into client (idCEclient,societe,client,mail,tel,adresse,commentaire) values(?,?,?,?,?,?,?)",(idCE,societe,client,mail,tel,adresse,commentaire)]
        ecriture_BDD(req)
        req=["SELECT max(idclient) from client",()]
        idclient=lecture_BDD(req)[0]["max(idclient)"]
        req=["insert into commande (idclientCmd,idCE,total,idclientHW,etatCmd,date,corbeille,createdBy) values(?,?,?,?,?,?,0,?)",(idclient,idCE,total,-1,0,date,user)]
        ecriture_BDD(req)

        req=["SELECT max(id_commande) from commande",()]
        idCmd=lecture_BDD(req)[0]['max(id_commande)']

        #Récupération des produits
        Lcode=getListeForm("code")
        Llib=getListeForm("lib")
        Lprix=getListeForm("prix")
        Lqte=getListeForm("qte")
        Lato=getListeForm("ato")
        Lean=getListeForm("ean")

        for i in range(len(Lcode)):
            req=["insert into facturation (idCmd,code,ean,libW,lib,prix,qte,ato,errone,idHW,etatProd,etatMin,etatMax) values(?,?,?,?,?,?,?,?,?,?,?,?,?)",(idCmd,Lcode[i],Lean[i],Llib[i],Llib[i],Lprix[i],Lqte[i],Lato[i],0,-1,0,0,0)]
            ecriture_BDD(req)
        req=["INSERT INTO stats  (date,idUser,action,cde,pdt,lot) VALUES (?,?,?,?,?,?)",(date,user,'ajouter',1,len(Lcode),idCmd)]
        ecriture_BDD(req)
        if mode=="1":
            write_log(str(session['user']['id']),"/valinuler - Création de la commande n°"+str(idCmd)+" et ajout d'une nouvelle")
            return addCmd(user)
        else:
            write_log(str(session['user']['id']),"/valinuler - Création de la commande n°"+str(idCmd)+" et retour au suivi des commandes")
            return suiviCmd(user)
    return suiviCmd(user)
    

@app.route('/searchClient', methods=['GET', 'POST'])
def searchClient():
    checkUser()
    client=getValeurFormulaire("client")
    try:
        idclient=client.split("]")[0].split("[")[1]
        req=["SELECT * from client where idclient=?",(idclient,)]
        reqInfos=lecture_BDD(req)
        Linfo=[reqInfos[0]['idCEclient'],reqInfos[0]['societe'],reqInfos[0]['client'],reqInfos[0]['mail'],reqInfos[0]['tel'],reqInfos[0]['adresse'],reqInfos[0]['commentaire']]
        taille=len(Linfo)
    except :
        taille=0
        Linfo=[]
    write_log(str(session['user']['id']),"/searchClient - Recherche d'un client")
    return jsonify(Linfo=Linfo,taille=taille)
    

@app.route('/getSociete', methods=['GET', 'POST'])
def getSociete(): 
    checkUser()
    idCE=getValeurFormulaire('idCE')
    req=["SELECT entreprise from listingCE where idCE=? and corbeille=0",(idCE,)]
    societe=lecture_BDD(req)[0]["entreprise"]
    return jsonify(societe=societe)

#endregion

####################### 0-Monde Traitement des données - OngletTraitement ###############
#region
@app.route('/start/<user>')
def start(user):
    checkUser()
    idPC=-1
    req=["SELECT idCE from listingCE where corbeille=0",()]
    LidCE=lecture_BDD(req)
    req=["SELECT id,numPC from postes ORDER BY numPC",()]
    Lpc=lecture_BDD(req)
    # if session['user']['idPC']!="-1" or session['user']['idPC'] in Lpc:
    #     idPC=session['user']['idPC'] 
    # else:
    #     idPC=Lpc[0]
    #Commandes à préparer/facturer
    req=["SELECT count(id_commande) FROM commande WHERE etatCmd=1 and corbeille=0",()]
    encours=lecture_BDD(req)[0]["count(id_commande)"]
    req=["SELECT count(idReliquat),reliquats.code,reliquats.qte,reliquats.lot,ean,libW,commande.idCE,dateLot,utilisateur.prenom from reliquats join facturation on reliquats.code=facturation.code join commande on id_commande=facturation.idCmd  join listingCE on listingCE.idCE=commande.idCE JOIN utilisateur ON listingCE.referente=utilisateur.id where commande.lot=reliquats.lot and etatMin<2 and commande.corbeille=0 order by reliquats.code",()]
    reliquats=lecture_BDD(req)[0]["count(idReliquat)"]
    req=["SELECT count(id_commande) FROM commande WHERE etatCmd=2 and corbeille=0",()]
    livres=lecture_BDD(req)[0]["count(id_commande)"]
    Ldate=[]
    for i in range (0,8,1):
        Lenfant=[]
        date=(datetime.today()-timedelta(i)).strftime('%Y-%m-%d')
        Lenfant.append(date)
        #Commandes créées
        req=["SELECT count(id_commande) FROM commande WHERE date=?",(date,)]
        Lenfant.append(lecture_BDD(req)[0]["count(id_commande)"])
        #Commandes facturées
        req=["SELECT count(id_commande) FROM commande WHERE dateFact=?",(date,)]
        Lenfant.append(lecture_BDD(req)[0]["count(id_commande)"])
        Ldate.append(Lenfant)
    write_log(str(session['user']['id']),"/start - Page initiale pour extraire")
    return render_template('traitementDonnees_synthetiser.html',LidCE=LidCE,user=user,Lpc=Lpc,Ldate=Ldate,encours=encours,reliquats=reliquats,livres=livres,idPC=idPC)

@app.route('/extractGeneral',methods=['GET', 'POST'])
def extractGeneral():
    try :
        session['user']
        user=session['user']
    except:
        return(index())
    action=getValeurFormulaire("action")
    if action=="1":
        export_CSV1()
        write_log(str(session['user']['id']),"/extractGeneral - Exportation du listing CSV 1.csv")
    elif action=="2":
        export_CSV2()
        write_log(str(session['user']['id']),"/extractGeneral - Exportation du listing CSV 2.csv")
    elif action=="3":
        export_CSV3()
        write_log(str(session['user']['id']),"/extractGeneral - Exportation du listing CSV 3.csv")
    elif action=="4":
        export_CSV4()
        write_log(str(session['user']['id']),"/extractGeneral - Exportation du listing CSV 4.csv")
    elif action=="5":
        export_CSV5()
        write_log(str(session['user']['id']),"/extractGeneral - Exportation du listing CSV 5.csv")
    elif action=="5":
        export_CSV6()
        write_log(str(session['user']['id']),"/extractGeneral - Exportation du listing CSV 5.csv")
    elif action=="7":
        export_CSV7()
        write_log(str(session['user']['id']),"/extractGeneral - Exportation du listing CSV 5.csv")
    return start(user) 
@app.route('/changePC', methods=['GET', 'POST'])
def changePC():
    checkUser()
    idPC=getValeurFormulaire("idPC")
    session['user']['idPC']=idPC
    write_log(str(session['user']['id']),"/start - Page initiale pour extraire")
    return '',204

@app.route('/generer/<user>', methods=['GET', 'POST'])
def generer(user):
    checkUser()
    nCE=getValeurFormulaire('nCE')
    if nCE!="":
        nCE=int(nCE)
    description=getValeurFormulaire('description')
    createur=getValeurFormulaire('createur')
    date=datetime.today().strftime('%Y-%m-%d')
    req=["INSERT INTO extractions (idCE,description,date,createur) VALUES(?,?,?,?)",(nCE,description,date,createur)]
    ecriture_BDD(req)
    req=["SELECT max(idExtraction) FROM extractions",()]
    idExtraction=lecture_BDD(req)[0]['max(idExtraction)']
    session['user']['idExtraction']=str(idExtraction)
    idPoste=getValeurFormulaire('idPoste')
    req=["SELECT dossierExtract,dossierErreur FROM postes WHERE id=?",(idPoste,)]
    repertoire=lecture_BDD(req)[0]['dossierExtract']
    erreur=lecture_BDD(req)[0]['dossierErreur']
    nbError,nbFichier=initTraitement(nCE,user,repertoire,erreur)
    #STATS-EXTRACTION
    req=["SELECT count(qte) FROM facturation JOIN commande ON idCmd=id_commande WHERE idExtractionCmd=?",(idExtraction,)]
    nbProduits=lecture_BDD(req)[0]['count(qte)']
    req=["INSERT INTO stats (date,idUser,action,cde,pdt,lot) VALUES (?,?,?,?,?,?)",(date,user,'extraire',nbFichier,nbProduits,idExtraction)]
    ecriture_BDD(req)
    if nbFichier>=nbError:
        write_log(str(session['user']['id']),"/generer -Extraction avec succès n°"+str(idExtraction))
        return assoClientCE(user,nbError)
    else:
        write_log(str(session['user']['id']),"/generer -Extraction en échec n°"+str(idExtraction))
        req=['DELETE FROM extractions where idExtraction=?',(idExtraction,)]
        ecriture_BDD(req)
        return '',204


@app.route('/assoClientCE/<user>',methods=['GET', 'POST'])
def assoClientCE(user,nbError=0):
    checkUser()
    idExtraction=int(session['user']['idExtraction'])
    req=["SELECT * from client join commande on idclient=idclientCmd where idExtraction=? and idclientHW=-1 and etatCmd=0 and commande.corbeille=0 order by societe",(idExtraction,)]
    Lclients=lecture_BDD(req)

    req=["SELECT idCE from listingCE where corbeille=0",()]
    LidCE=lecture_BDD(req)

    req=["SELECT * from client join commande on idclient=idclientCmd where idExtraction=? and idclientHW<>-1 and etatCmd=0 and commande.corbeille=0 order by idclientHW",(idExtraction,)]
    LclientsHW=lecture_BDD(req)

    nCE=""
    date=""
    description=""
    createur=""
    try:
        req=["SELECT idCE,description,createur,date from extractions where idExtraction=?",(idExtraction,)]
        Linfo=lecture_BDD(req)[0]
        nCE=Linfo["idCE"]
        date=Linfo["date"]
        description=Linfo["description"]
        createur=Linfo["createur"]
    except:
        pass
    write_log(str(session['user']['id']),"/assoClientCE - Modification de l'extraction n°"+str(idExtraction))
    return render_template('traitementDonnees_associationClientCE.html',Lclients=Lclients,LclientsHW=LclientsHW,LidCE=LidCE,nCE=nCE,date=date,description=description,createur=createur,nbError=nbError,user=user)
    

@app.route('/applicModif', methods=['GET', 'POST'])
def applicModif(): 
    checkUser()

    user=session['user']['id']
    nouvidCE=getValeurFormulaire('nouvidCE')
    idClient=getValeurFormulaire('idClient')
    req=["SELECT idCE from listingCE where idCE=? and corbeille=0",(nouvidCE,)]
    ListIdCE=lecture_BDD(req)
    result=0
    if len(ListIdCE)>0:
        result=1
        req=["UPDATE client set idCEclient=? where idclient=?",(nouvidCE,idClient)]
        ecriture_BDD(req)
        req=["UPDATE commande set idCE=?,modifiedBy=? where idclientCmd=?",(nouvidCE,user,idClient)]
        ecriture_BDD(req)
    write_log(str(session['user']['id']),"/applicModif - Modification de la commande du client n°"+str(idClient))
    return jsonify(result=result)


@app.route('/applicModifHW', methods=['GET', 'POST'])
def applicModifHW(): 
    checkUser()
    idCE=getValeurFormulaire('nouvidCE')
    idClient=getValeurFormulaire('idClient')
    societe=getValeurFormulaire('societe')
    client=majusca(getValeurFormulaire('client'))
    mail=getValeurFormulaire('mail').lower()
    tel=getValeurFormulaire('tel')
    adresse=majusca(getValeurFormulaire('adresse'))
    total=getValeurFormulaire('total')
    user=session['user']['id']

    req=["SELECT idCE from listingCE where idCE=? and corbeille=0",(idCE,)]
    ListIdCE=lecture_BDD(req)
    if len(ListIdCE)>0:
        req=["UPDATE client set idCEclient=?,societe=?,client=?,mail=?,tel=?,adresse=? where idclient=?",(idCE,societe,client,mail,tel,adresse,idClient)]
        req2=["UPDATE commande set idCE=?,total=?,modifiedBy=? where idclientCmd=?",(idCE,total,user,idClient)]
        result=1
    else:
        req=["UPDATE client set societe=?,client=?,mail=?,tel=?,adresse=? where idclient=?",(societe,client,mail,tel,adresse,idClient)]
        req2=["UPDATE commande set total=?,modifiedBy=? where idclientCmd=?",(total,user,idClient)]
        result=0
    ecriture_BDD(req)
    ecriture_BDD(req2)
    write_log(str(session['user']['id']),"/applicModiHW - Modification de la commande HW du client n°"+str(idClient))
    return jsonify(result=result)


@app.route('/historique/<user>',methods=['GET', 'POST'])
def hist(user): 
    checkUser()    
    idExtraction=session['user']['idExtraction']
    req=["SELECT * from extractions where idExtraction in (SELECT distinct idExtractionCmd from commande where etatCmd=0 and corbeille=0) order by date desc LIMIT 100",()]
    listExtract=lecture_BDD(req)
    write_log(str(session['user']['id']),"/historique - Visualisation généréale de l'historique")
    return render_template('traitementDonnees_hist.html',listExtract=listExtract,idExtraction=idExtraction,user=user)
    

@app.route('/selectExtract/<user>', methods=['GET', 'POST'])
def selectExtract(user):
    checkUser()
    id=getValeurFormulaire('id')
    session['user']['idExtraction']=int(id)
    write_log(str(session['user']['id']),"/selectExtract - Séléection de l'extraction n°"+str(id))
    return assoClientCE(user)
    

@app.route('/suprExtract', methods=['GET', 'POST'])
def suprExtract():
    checkUser()
    idExtraction=getValeurFormulaire('id')
    req=["UPDATE commande set corbeille=1 where idExtractionCmd=?",(idExtraction,)]
    write_log(str(session['user']['id']),"/suprExtract - Suppresion de l'extraction n°"+str(id))
    ecriture_BDD(req)
    return jsonify()
    

#endregion

####################### 1-Monde préparer - OngletPréparer ###############################
#region
@app.route('/choixCE/<user>', methods=['GET', 'POST'])
def choixCE(user):
    checkUser()
    idCE=session['user']['idCE']

    ref=getValeurFormulaire("ref")
    if ref!=None:
        write_log(str(session['user']['id']),"/choixCE - Filtre référente n°"+str(ref))
        req=["SELECT distinct commande.idCE,utilisateur.prenom,entreprise from commande inner join listingCE on commande.idCE=listingCE.idCE JOIN utilisateur ON listingCE.referente=utilisateur.id where etatCmd=0 and commande.corbeille=0 and listingCE.referente=? and listingCE.corbeille=0",(ref,)]
        ref=int(ref)
    else:
        write_log(str(session['user']['id']),"/choixCE - Filtre sur aucune référente")
        req=["SELECT distinct commande.idCE,utilisateur.prenom,entreprise from commande inner join listingCE on commande.idCE=listingCE.idCE JOIN utilisateur ON listingCE.referente=utilisateur.id where etatCmd=0 and commande.corbeille=0 and listingCE.corbeille=0",()]
    listCE=lecture_BDD(req)
    nbClient=[]
    minDate=[]
    for i in range(len(listCE)):
        req=["SELECT count(*),MIN(date) from commande where idCE=? and corbeille=0 and etatCmd=0",(listCE[i]["idCE"],)]
        ligne=lecture_BDD(req)[0]
        nbClient.append(ligne["count(*)"])
        minDate.append(ligne["min(date)"])
    listeRef,listeAll=getListRef()
    dateLim=(datetime.today()-timedelta(days=15)).strftime('%Y-%m-%d')
    return render_template('preparation_selectCE.html',listCE=listCE,nbClient=nbClient,idCE=idCE,minDate=minDate,user=user,ref=ref,listeRef=listeRef,listeAll=listeAll,dateLim=dateLim)


@app.route('/selectCE/<user>', methods=['GET', 'POST'])
def selectCE(user):
    checkUser()
    idCE=getValeurFormulaire('idCE')
    session['user']['idCE']=idCE
    write_log(str(session['user']['id']),"/selectCE - Sélection du CE n°"+str(idCE))
    return editErreurs(user)
    

@app.route('/erreurs/<user>',methods=['GET', 'POST'])
def editErreurs(user):
    checkUser()
    idCE=session['user']['idCE']
    LprixSuggest=[]
    req=["SELECT idProd,idCmd,client,mail,tel,code,lib,prix,qte,ato from facturation join commande on idCmd=id_commande join client on idclient=idclientCmd where errone=1 and idCE=? and etatCmd=0 and etatProd<>4 and idHW=-1 and commande.corbeille=0",(idCE,)]
    codeErreur=lecture_BDD(req)
    req=["SELECT idProd,idCmd,client,mail,tel,code,lib,prix,qte,ato from facturation join commande on idCmd=id_commande join client on idclient=idclientCmd where errone=2 and idCE=? and etatCmd=0 and etatProd<>4 and idHW=-1 and commande.corbeille=0",(idCE,)]
    prixErreur=lecture_BDD(req)
    for Lcode in prixErreur:
        code=Lcode["code"]
        LprixSuggest.append(getPrix(code))
    req=["SELECT idProd,idCmd,client,mail,tel,code,lib,prix,qte,ato from facturation join commande on idCmd=id_commande join client on idclient=idclientCmd where errone=3 and idCE=? and etatCmd=0 and etatProd<>4 and idHW=-1 and commande.corbeille=0",(idCE,)]
    qteErreur=lecture_BDD(req)
    req=["SELECT idProd,idCmd,client,mail,tel,code,prix,qte,ato,idHW from facturation join commande on idCmd=id_commande join client on idclient=idclientCmd where errone=1 and idCE=? and etatCmd=0 and etatProd<>4 and idHW<>-1 and commande.corbeille=0",(idCE,)]
    codeErreurHW=lecture_BDD(req)
    req=["SELECT idProd,idCmd,client,mail,tel,code,prix,qte,ato,idHW from facturation join commande on idCmd=id_commande join client on idclient=idclientCmd where errone=2 and idCE=? and etatCmd=0 and etatProd<>4 and idHW<>-1 and commande.corbeille=0",(idCE,)]
    prixErreurHW=lecture_BDD(req)
    for Lcode in prixErreurHW:
        code=Lcode["code"]
        LprixSuggest.append(getPrix(code))
    req=["SELECT idProd,idCmd,client,mail,tel,code,prix,qte,ato,idHW from facturation join commande on idCmd=id_commande join client on idclient=idclientCmd where errone=3 and idCE=? and etatCmd=0 and idHW<>-1 and commande.corbeille=0",(idCE,)]
    qteErreurHW=lecture_BDD(req)

    req=["SELECT entreprise,utilisateur.prenom from listingCE JOIN utilisateur ON listingCE.referente=utilisateur.id where idCE=? and corbeille=0 LIMIT 1",(idCE,)]
    try:
        liste=lecture_BDD(req)[0]
        nomCE=liste["entreprise"]
        referente=liste["prenom"]
    except:
        nomCE=""
        referente=""
    write_log(str(session['user']['id']),"/erreurs - Visualisation des commandes du CE n°"+str(idCE))
    return render_template('preparation_editErreurs.html',idCE=idCE,nomCE=nomCE,codeErreur=codeErreur,prixErreur=prixErreur,qteErreur=qteErreur,codeErreurHW=codeErreurHW,prixErreurHW=prixErreurHW,qteErreurHW=qteErreurHW,LprixSuggest=LprixSuggest,user=user,referente=referente)


@app.route('/validerModif/<user>', methods=['GET', 'POST'])
def validerModif(user):
    checkUser()
    HWouNum=getValeurFormulaire("HWouNum")
    idProd=getValeurFormulaire("idProd")
    if HWouNum=="Num":
        erreurType=getValeurFormulaire("erreurType")
        if erreurType=="code":
            code=getValeurFormulaire("code")
            req=["UPDATE facturation set code=? where idProd=?",(code,idProd)]
            ecriture_BDD(req)
            write_log(str(session['user']['id']),"/validerModif - Modification erreur Idprod/code : "+str(idProd)+"/"+str(code))
        elif erreurType=="prix":
            code=getValeurFormulaire("code")
            prix=getValeurFormulaire("prix")
            req=["UPDATE facturation set code=?,prix=? where idProd=?",(code,prix,idProd)]
            ecriture_BDD(req)
            write_log(str(session['user']['id']),"/validerModif - Modification erreur idprod/code/prix : "+str(idProd)+"/"+str(code)+"/"+str(prix))
        else:
            qte=getValeurFormulaire("qte")
            try:
                qte=int(qte)
                if qte<0:
                    message="La quantité doit être supérieure à 0 !"
                elif qte>30:
                    message="La quantité doit être inférieure à 30 !"
                else:
                    req=["UPDATE facturation set qte=? where idProd=?",(qte,idProd)]
                    write_log(str(session['user']['id']),"/validerModif - Modification erreur idprod/quantité : "+str(idProd)+"/"+str(qte))
                    ecriture_BDD(req)
            except:
                message="La quantité doit être un nombre !"        
    else:
        code=getValeurFormulaire("code")
        prix=getValeurFormulaire("prix")
        qte=getValeurFormulaire("qte")
        req=["UPDATE facturation set qte=?,code=?,prix=? where idProd=?",(qte,code,prix,idProd)]
        ecriture_BDD(req)
        write_log(str(session['user']['id']),"/validerModif - Modification HW erreur idprod/qte/prix/code : "+str(idProd)+"/"+str(qte)+"/"+str(prix)+"/"+str(code))

    req=["SELECT prix,qte,code from facturation where idProd=?",(idProd,)]
    cmd=lecture_BDD(req)[0]
    errone,strCode,ean,libW=checkCode(cmd["code"])
    if errone==0:
        errone=checkPrix(cmd['prix'],strCode)
        if errone==0:
            try:
                intQte=int(cmd["qte"])
                if intQte<1:
                    raise ValueError
            except ValueError:
                errone=3

    E=0
    req=["UPDATE facturation set errone=?,ean=?,libW=?,etatProd=?,etatMin=?,etatMax=? where idProd=?",(errone,ean,libW,E,E,E,idProd)]
    ecriture_BDD(req)
    return editErreurs(user)


@app.route('/listeProduits/<user>',methods=['GET', 'POST'])
def listProd(user):
    checkUser()
    idCE=session['user']['idCE']
    req=["SELECT count(idProd) from facturation where errone>0 and etatProd<>4 and idCmd in (SELECT id_commande from commande where idCE=? and etatCmd=0 and corbeille=0)",(idCE,)]
    nbError=lecture_BDD(req)[0]["count(idProd)"]
    req=["SELECT * from facturation where errone=0 and etatProd<>4 and idCmd in (SELECT id_commande from commande where idCE=? and etatCmd=0 and corbeille=0) order by code",(idCE,)] 
    lignes=lecture_BDD(req)
    Lidclient,code,ean,lib,libCl,qte,oui,LidHW,Lstock=[],[],[],[],[],[],[],[],[]
    for l in lignes:
        ato=l['ato']
        strCode=l['code']
        intQte=int(l['qte'])
        txtlib=l['lib']
        idHW=l['idHW']
        idcmd=l['idProd']
        idCmd=l['idCmd']
        try :
            index=code.index(strCode)
            LidHW[index].append(idHW)
            qte[index]=qte[index]+intQte
            if ato=="oui":
                oui[index]+=intQte
            Lidclient[index].append(idCmd)
            if idHW==-1:
                libCl[index].append(txtlib)
            else:
                libCl[index].append(idcmd)

        except ValueError:
            Lstock.append(getStockSorgues(strCode))
            code.append(strCode)
            qte.append(intQte)
            LidHW.append([idHW])
            lib.append(l['libW'])
            ean.append(l['ean'])
            Lidclient.append([idCmd])
            if ato=="oui":
                oui.append(intQte)
            else:
                oui.append(0)
            if idHW==-1:
                libCl.append([txtlib])
            else:
                libCl.append([idcmd])

    
    req=["SELECT entreprise,utilisateur.prenom from listingCE JOIN utilisateur ON listingCE.referente=utilisateur.id where idCE=? and corbeille=0 LIMIT 1",(idCE,)]
    try:
        liste=lecture_BDD(req)[0]
        nomCE=liste["entreprise"]
        referente=liste["prenom"]
    except:
        nomCE=""
        referente=""
    date1=datetime.today().strftime('%Y-%m-%d_%H:%M:%S')
    date=date1.split('_')[0]
    heure=date1.split('_')[1]
    write_log(str(session['user']['id']),"/listeProduit - Visualisation du CE n° "+str(idCE))
    return render_template('preparation_bon.html',user=user,nbError=nbError,Lidclient=Lidclient,code=code,ean=ean,lib=lib,libCl=libCl,quantite=qte,atom=oui,nProd=len(code),idCE=idCE,nomCE=nomCE,LidHW=LidHW,Lstock=Lstock,referente=referente,date=date,heure=heure)


@app.route('/lot/<user>', methods=['GET', 'POST'])
def creerlot(user):
    checkUser()
    idCE=session['user']['idCE']
    date=datetime.today().strftime('%Y-%m-%d')
    dateLim=datetime.today()+timedelta(delaiRupt)
    req=["SELECT max(lot) from commande",()]
    try:
        session['user']['lot']=lecture_BDD(req)[0]["max(lot)"]+1
    except TypeError:
        session['user']['lot']=0
    lot=session['user']['lot']
    req=["UPDATE commande set lot=?,etatCmd=1,dateLot=?,preparedBy=? where idCE=? and etatCmd=0 and corbeille=0",(lot,date,user,idCE)]
    ecriture_BDD(req)
    req=["SELECT qte,idProd,code from facturation where etatProd<>4 and idCmd in (SELECT id_commande from commande where lot=? and corbeille=0)",(lot,)]
    lignes=lecture_BDD(req)
    req=["SELECT SUM(qte),COUNT(idCmd) from facturation where etatProd<>4 and idCmd in (SELECT id_commande from commande where lot=? and corbeille=0)",(lot,)]
    pdt=lecture_BDD(req)[0]['SUM(qte)']
    cde=lecture_BDD(req)[0]['COUNT(idCmd)']
    #STATS-PREPARATION
    req=["INSERT INTO stats  (date,idUser,action,cde,pdt,lot) VALUES (?,?,?,?,?,?)",(date,user,'preparer',cde,pdt,lot)]
    ecriture_BDD(req)
    for l in lignes:
        req=["SELECT * from rupture where date>? and rupt_code=?",(dateLim,l["code"])]
        Lrupt=lecture_BDD(req)
        if len(Lrupt)>0:
            etat="3;"*(int(l['qte'])-1)+"3"
            minEtat=3
            maxEtat=3
        else:
            minEtat=0
            maxEtat=0
            etat="0;"*(int(l['qte'])-1)+"0"
        req=["UPDATE facturation set etatProd=?,etatMin=?,etatMax=? where idProd=?",(etat,minEtat,maxEtat,l['idProd'])]
        ecriture_BDD(req)
    
    req=["SELECT mail,client,id_commande,idCE from commande join client on idclientCmd=idclient where lot=? and corbeille=0",(lot,)]
    Lclient=lecture_BDD(req)
    req=["SELECT mail,mailCl,mailInterPrep from listingCE where idCE=? and corbeille=0",(Lclient[0]['idCE'],)]
    LmailCE=lecture_BDD(req)
    if len(LmailCE)>0:
        mailCl=LmailCE[0]['mailCl']
        mailInterPrep=LmailCE[0]['mailInterPrep']
        mail=LmailCE[0]['mail']
    else:
        mail=''
        mailCl=0
        mailInterPrep=0
    for client in Lclient:
        Linfo=[client["mail"],client["client"],str(client["id_commande"]),1]
        if mailCl==1:
            send_email(Linfo,[],[])
        if mailInterPrep==1:
            Linfo[0]=mail
            send_email(Linfo,[],[])
    write_log(str(session['user']['id']),"/lot - Formation du lot n° "+str(lot))
    return bonPrep(user)
    
#endregion   

####################### 2-Monde des reliquats - OngletReliquat ##########################
#region
@app.route('/reliquats/<user>', methods=['GET', 'POST'])
def reliquats(user):
    checkUser()
    lot=session['user']['lot']
    ref=getValeurFormulaire("ref")
    if ref!=None:
        write_log(str(session['user']['id']),"/reliquat - Filtre sur la référente "+str(ref))
        req=["SELECT distinct commande.idCE,utilisateur.prenom,entreprise,lot,dateLot from commande inner join listingCE on commande.idCE=listingCE.idCE JOIN utilisateur ON listingCE.referente=utilisateur.id where etatCmd=1 and commande.corbeille=0 and listingCE.referente=? and listingCE.corbeille=0 order by lot",(ref,)]
        ref=int(ref)
    else:
        write_log(str(session['user']['id']),"/suivi - Filtre sur toutes les référentes ")
        req=["SELECT distinct commande.idCE,lot,utilisateur.prenom,entreprise,lot,dateLot from commande inner join listingCE on commande.idCE=listingCE.idCE JOIN utilisateur ON listingCE.referente=utilisateur.id where etatCmd=1 and commande.corbeille=0 and listingCE.corbeille=0 order by lot",()]
    
    listLot=lecture_BDD(req)
    nbClient=[]
    listeRef,listeAll=getListRef()
    for client in listLot:
        req=["SELECT count(*),idCE from commande where lot=? and corbeille=0",(client["lot"],)]
        nbClient.append(lecture_BDD(req)[0]["count(*)"])
    dateLim=(datetime.today()-timedelta(days=15)).strftime('%Y-%m-%d')
    return render_template('reliquat_selectLot.html',user=user,listLot=listLot,lot=lot,nbClient=nbClient,ref=ref,listeRef=listeRef,listeAll=listeAll,dateLim=dateLim)
    

@app.route('/defReliquat/<user>',methods=['GET', 'POST'])
def defReliquat(user):
    checkUser()
    lot=session['user']['lot']
    req=["SELECT * from facturation where etatProd<>4 and idCmd in (SELECT id_commande from commande where lot=? and etatCmd=1 and corbeille=0) order by code",(lot,)]
    lignes=lecture_BDD(req)
    req=["SELECT distinct code from facturation where idCmd in (SELECT id_commande from commande where lot=? and etatCmd=1 and corbeille=0) order by code",(lot,)]
    Lcode=lecture_BDD(req)
    Lreliquats=[]
    Lstock=[]
    Lstockbis=[]
    for code in Lcode:
        req=["SELECT idReliquat,mag,qte from reliquats where lot=? and code=?",(lot,code['code'])]
        reliquats=lecture_BDD(req)
        Lreliquats.append(reliquats)
        Lstock.append(getStockAutres(code['code']))
        Lstockbis.append(getStockSorgues(code['code']))

    code,ean,lib,qte=[],[],[],[]
    for l in lignes:
        strCode=l['code']
        intQte=int(l['qte'])
        try :
            index=code.index(strCode)
            qte[index]=qte[index]+intQte

        except ValueError:
            code.append(strCode)
            qte.append(intQte)
            lib.append(l['libW'])
            ean.append(l['ean'])

    try:
        req=["SELECT idCE,dateLot from commande where lot=? LIMIT 1",(lot,)]
        liste=lecture_BDD(req)[0]
        idCE=liste["idCE"]
        dateLot=liste["dateLot"]
        req=["SELECT entreprise,utilisateur.prenom from listingCE JOIN utilisateur ON listingCE.referente=utilisateur.id where idCE=? and corbeille=0 LIMIT 1",(idCE,)]
        liste=lecture_BDD(req)[0]
        nomCE=liste["entreprise"]
        referente=liste["prenom"]
    except:
        referente=""
        idCE=""
        nomCE=""
    write_log(str(session['user']['id']),"/defReliquat - Sélection du lot n°"+str(lot))

    return render_template('reliquat_def.html',user=user,nomCE=nomCE,idCE=idCE,lot=lot,code=code,ean=ean,lib=lib,quantite=qte,nProd=len(code),Lreliquats=Lreliquats,Lmag=Lmag,Lstock=Lstock,Lstockbis=Lstockbis,referente=referente,dateLot=dateLot)


@app.route('/addReliquat', methods=['GET', 'POST'])
def addReliquat():
    checkUser()
    code=getValeurFormulaire("code")
    user=getValeurFormulaire("user")
    lot=session['user']['lot']
    req=["insert into reliquats (code,mag,qte,lot) values (?,?,?,?)",(code,"1-Sorgues",1,lot)]
    ecriture_BDD(req)
    req=["SELECT max(idReliquat) from reliquats where code=? and lot=?",(code,lot)]
    idReliquat=lecture_BDD(req)[0]['max(idReliquat)']
    write_log(str(session['user']['id']),"/addReliquat - Ajout de la demande reliquat n° "+str(idReliquat))
    return jsonify(idReliquat=idReliquat)


@app.route('/updateReliquat', methods=['GET', 'POST'])
def updateReliquat():
    checkUser()
    idReliquat=getValeurFormulaire("idReliquat")
    mag=getValeurFormulaire("mag")
    qte=getValeurFormulaire("qte")
    req=["UPDATE reliquats set mag=?, qte=? where idReliquat=?",(mag,qte,idReliquat)]
    ecriture_BDD(req)
    write_log(str(session['user']['id']),"/updateReliquat - Mise à jour de la demande reliquat n°"+str(idReliquat))
    return jsonify(result="success")
    

@app.route('/delReliquat', methods=['GET', 'POST'])
def delReliquat():
    checkUser()
    idReliquat=getValeurFormulaire("idReliquat")
    req=["delete from reliquats where idReliquat=?",(idReliquat,)]
    ecriture_BDD(req)
    write_log(str(session['user']['id']),"/delReliquat - Suppression du reliquat n° "+str(idReliquat))
    return jsonify(result="success")
           

@app.route('/bonPrep/<user>',methods=['GET', 'POST'])
def bonPrep(user):
    checkUser()
    lot=session['user']['lot']
    req=["SELECT * from facturation where errone=0 and etatProd<>4 and idCmd in (SELECT id_commande from commande where lot=? and etatCmd=1 and corbeille=0) order by code",(lot,)]
    lignes=lecture_BDD(req)
    code,ean,lib,libCl,qte,oui,LidHW,Lstock=[],[],[],[],[],[],[],[]
    for l in lignes:
        ato=l['ato']
        strCode=l['code']
        intQte=int(l['qte'])
        txtlib=l['lib']
        idHW=l['idHW']
        idcmd=l['idProd']
        
        try :
            index=code.index(strCode)
            LidHW[index].append(idHW)
            qte[index]=qte[index]+intQte
            if ato=="oui":
                oui[index]+=intQte
            if idHW==-1:
                libCl[index].append(txtlib)
            else:
                libCl[index].append(idcmd)

        except ValueError:
            Lstock.append(getStockSorgues(strCode))
            code.append(strCode)
            qte.append(intQte)
            LidHW.append([idHW])
            lib.append(l['libW'])
            ean.append(l['ean'])
            if ato=="oui":
                oui.append(intQte)
            else:
                oui.append(0)
            if idHW==-1:
                libCl.append([txtlib])
            else:
                libCl.append([idcmd])
    
    
    try:
        req=["SELECT idCE,dateLot from commande where lot=? LIMIT 1",(lot,)]
        liste=lecture_BDD(req)[0]
        idCE=liste["idCE"]
        dateLot=liste["dateLot"]
        req=["SELECT * from listingCE JOIN utilisateur ON listingCE.referente=utilisateur.id where idCE=? and corbeille=0 LIMIT 1",(idCE,)]
        Linfo=lecture_BDD(req)[0]
        nomCE=Linfo["entreprise"]
        referente=Linfo["prenom"]
    except:
        idCE=""
        nomCE=""
        referente=""
    write_log(str(session['user']['id']),"/bonPrep -Visualisation du bon de préparation du lot n°"+str(lot))
    return render_template('reliquat_bonPrep.html',user=user,code=code,ean=ean,lib=lib,libCl=libCl,quantite=qte,atom=oui,nProd=len(code),idCE=idCE,nomCE=nomCE,lot=lot,LidHW=LidHW,Lstock=Lstock,referente=referente,dateLot=dateLot,Linfo=Linfo)


@app.route('/visuReliquat/<user>',methods=['GET', 'POST'])
def visuReliquat(user,tout=0):
    checkUser()
    date1=datetime.today().strftime('%d-%m-%Y_%H:%M:%S')
    date=date1.split('_')[0]
    heure=date1.split('_')[1]
    req=["SELECT id from lastRelik",()]
    idReliquat=lecture_BDD(req)[0]["id"] 
    req=["SELECT idCE from listingCE where corbeille=0",()]
    LidCE=lecture_BDD(req)
    if int(tout)==0:
        idFiltre=idReliquat
    else:
        idFiltre=0
    Lrelik=[]
    for mag in Lmag:
        if(mag==Lmag[-1]):
            req=["SELECT distinct idReliquat,reliquats.code,reliquats.qte,reliquats.lot,ean,libW,commande.idCE,dateLot,qteDonnee,utilisateur.id,utilisateur.prenom from reliquats join facturation on reliquats.code=facturation.code join commande on id_commande=facturation.idCmd join listingCE on listingCE.idCE=commande.idCE JOIN utilisateur ON listingCE.referente=utilisateur.id where commande.lot=reliquats.lot and etatMin<2 and mag=? and idReliquat>? and commande.corbeille=0 order by reliquats.code",(mag,idFiltre)]
        else:
            req=["SELECT distinct idReliquat,reliquats.code,reliquats.qte,reliquats.lot,ean,libW,commande.idCE,dateLot,utilisateur.prenom from reliquats join facturation on reliquats.code=facturation.code join commande on id_commande=facturation.idCmd  join listingCE on listingCE.idCE=commande.idCE JOIN utilisateur ON listingCE.referente=utilisateur.id where commande.lot=reliquats.lot and etatMin<2 and mag=? and idReliquat>?  and commande.corbeille=0 order by reliquats.code",(mag,idFiltre)]
        Lrelikmag=lecture_BDD(req)
        Lrelik.append(Lrelikmag)
    req=["SELECT max(idReliquat) from reliquats",()]
    l=lecture_BDD(req)
    if len(l)>0:
        maxRelik=l[0]['max(idReliquat)']
    else:
        maxRelik=0
    write_log(str(session['user']['id']),"/visuReliquat - Visualisation reliquat avec l'idMax n° "+str(maxRelik))
    return render_template('reliquat_general.html',user=user,Lrelik=Lrelik,Lmag=Lmag,idReliquat=idReliquat,maxRelik=maxRelik,LidCE=LidCE,date=date,heure=heure)
    

@app.route('/changeQteDonnee', methods=['GET', 'POST'])
def changeQteDonnee():
    checkUser()
    idRelik=getValeurFormulaire("idRelik")
    qteDonnee=getValeurFormulaire("qteDonnee")
    req=["UPDATE reliquats set qteDonnee=? where idReliquat=?",(qteDonnee,idRelik)]
    ecriture_BDD(req)
    write_log(str(session['user']['id']),"/changeQteDonnee - Ajout de la quantité pour l'idReliquat n°"+str(idRelik)+" avec une quantité de "+str(qteDonnee))
    return jsonify()
    

@app.route('/filtreReliquat/<user>', methods=['GET', 'POST'])
def filtreReliquat(user):
    checkUser()
    idReliquat=getValeurFormulaire("idReliquat")
    tout=getValeurFormulaire("tout")

    if idReliquat!="":
        req=["UPDATE lastRelik set id=?",(idReliquat,)]
        ecriture_BDD(req)
    write_log(str(session['user']['id']),"/filtreReliquat - Filtre sur la idReliquat "+str(idReliquat))
    return visuReliquat(user,tout)
    

@app.route('/filtreReliquatCE/<user>', methods=['GET', 'POST'])
def filtreReliquatCE(user):
    checkUser()
    idCE=getValeurFormulaire("idCE")
    Lrelik=[]
    req=["SELECT idCE from listingCE where corbeille=0",()]
    LidCE=lecture_BDD(req)
    if idCE!="":
        for mag in Lmag:
            if(mag==Lmag[-1]):
                req=["SELECT distinct idReliquat,reliquats.code,reliquats.qte,reliquats.lot,ean,libW,commande.idCE,dateLot,qteDonnee,utilisateur.id from reliquats join facturation on reliquats.code=facturation.code join commande on id_commande=facturation.idCmd join listingCE on listingCE.idCE=commande.idCE JOIN utilisateur ON listingCE.referente=utilisateur.id where commande.lot=reliquats.lot and etatMin<2 and mag=? and commande.idCE=? and commande.corbeille=0 order by reliquats.code",(mag,idCE)]
            else:
                req=["SELECT distinct idReliquat,reliquats.code,reliquats.qte,reliquats.lot,ean,libW,commande.idCE,dateLot,utilisateur.id from reliquats join facturation on reliquats.code=facturation.code join commande on id_commande=facturation.idCmd  join listingCE on listingCE.idCE=commande.idCE JOIN utilisateur ON listingCE.referente=utilisateur.id where commande.lot=reliquats.lot and etatMin<2 and mag=? AND commande.idCE=? and commande.corbeille=0 order by reliquats.code",(mag,idCE)]
            Lrelikmag=lecture_BDD(req)
            Lrelik.append(Lrelikmag)
        req=["SELECT id from lastRelik",()]
        idReliquat=lecture_BDD(req)[0]["id"] 
        req=["SELECT max(idReliquat) from reliquats",()]
        l=lecture_BDD(req)
        if len(l)>0:
            maxRelik=l[0]['max(idReliquat)']
        else:
            maxRelik=0
        write_log(str(session['user']['id']),"/filtreReliquarCE - Filtre sur le reliquat "+str(idReliquat))
        return render_template('reliquat_general.html',user=user,Lrelik=Lrelik,Lmag=Lmag,idCE=idCE,idReliquat=idReliquat,maxRelik=maxRelik,LidCE=LidCE)
    else: 
        tout=0
        write_log(str(session['user']['id']),"/filtreReliquatCE - Filtre tout les reliquats ")
        return(visuReliquat(user,tout))
    

@app.route('/rupture/<user>',methods=['GET', 'POST'])
def rupture(user):
    checkUser()
    date=datetime.today().strftime('%Y-%m-%d')
    req=["SELECT distinct idReliquat,reliquats.code,reliquats.qte,reliquats.lot,ean,libW,idCE,rupture.date from reliquats join facturation on reliquats.code=facturation.code join commande on id_commande=facturation.idCmd left join rupture on rupt_code=reliquats.code where commande.lot=reliquats.lot and etatMin<2 and mag=? and corbeille=0 and reliquats.code not in (SELECT rupt_code from rupture where date>?) order by mag,idReliquat",(Lmag[4],date)]
    Lrelik=lecture_BDD(req)
    write_log(str(session['user']['id']),"/rupture - Visualisation des ruptures")
    return render_template('reliquat_rupture.html',Lrelik=Lrelik,user=user)
    

@app.route('/planning/<user>',methods=['GET', 'POST'])
def planning(user):
    checkUser()
    date=datetime.today().strftime('%Y-%m-%d')
    req=["SELECT * from rupture where date>? order by date",(date,)]
    Lrupt=lecture_BDD(req)
    L0=[]
    L1=[]
    L2=[]
    for rupt in Lrupt:
        date=rupt["date"]
        Y=date.split("-")[0]
        M=date.split("-")[1]
        D=date.split("-")[2]
        date=datetime(int(Y),int(M),int(D)).strftime('%Y-%B-%d')
        Y=date.split("-")[0]
        M=date.split("-")[1]
        D=date.split("-")[2]
        if M+" "+Y not in L0:
            L0.append(M+" "+Y)
            L1.append([D])
            L2.append([[[rupt["rupt_code"],rupt["lib"]]]])
        elif D not in L1[-1]:
            L1[-1].append(D)
            L2[-1].append([[rupt["rupt_code"],rupt["lib"]]])
        else:
            L2[-1][-1].append([rupt["rupt_code"],rupt["lib"]])
    write_log(str(session['user']['id']),"/planning - Visualisation du planning")
    return render_template("reliquat_michael_planning.html",L0=L0,L1=L1,L2=L2,user=user)
    

@app.route('/suprRupt', methods=['GET', 'POST'])
def suprRupt():
    checkUser()
    idRupt=getValeurFormulaire('idRupt')
    req=["SELECT etatProd,idProd from facturation join commande on idCmd=id_commande where code=? and etatCmd=1 and corbeille=0",(idRupt,)]
    Lprod=lecture_BDD(req)
    for prod in Lprod:
        idProd=prod["idProd"]
        etatProd=prod["etatProd"]
        etatProd=etatProd.replace("3","1")
        LetatProd=etatProd.split(";")
        etatMin=min(LetatProd)
        etatMax=max(LetatProd)
        req=["UPDATE facturation set etatProd=?,etatMin=?,etatMax=? where idProd=?",(etatProd,etatMin,etatMax,idProd)]
        ecriture_BDD(req)
    req=["delete from rupture where rupt_code=?",(idRupt,)]
    ecriture_BDD(req)
    write_log(str(session['user']['id']),"/suprRupt - Suppression de l'id rupture n°"+str(idRupt))
    return jsonify()
    


@app.route('/validRupt/<user>', methods=['GET', 'POST'])
def validRupt(user):
    checkUser()
    Lcode=getListeForm("code")
    Ldate=getListeForm("date")
    Llib=getListeForm("lib")
    date=datetime.today().strftime('%Y-%m-%d')
    for i in range(len(Lcode)):
        if Ldate[i]!="" and Ldate[i]>date:
            req=["insert into rupture (date,rupt_code,lib) values (?,?,?)",(Ldate[i],Lcode[i],Llib[i])]
            ecriture_BDD(req)
            req=["SELECT etatProd,idProd,dateLot from facturation join commande on idCmd=id_commande where code=? and etatCmd=1",(Lcode[i],)]
            Letat=lecture_BDD(req)
            for etatID in Letat:
                delta=datetime.strptime(Ldate[i], '%Y-%m-%d')-datetime.strptime(etatID["dateLot"], '%Y-%m-%d')
                if delta.days>delaiRupt:
                    etat=etatID["etatProd"]
                    ID=etatID["idProd"]
                    etat=etat.replace("0","3")
                    etat=etat.replace("1","3")
                    L=etat.split(";")
                    minEtat=min(L)
                    maxEtat=max(L)
                    req=["UPDATE facturation set etatProd=?,etatMin=?,etatMax=? where idProd=?",(etat,minEtat,maxEtat,ID)]
                    ecriture_BDD(req)
            write_log(str(session['user']['id']),"/validRupt - Validation de la rupture du code "+str(Lcode[i]))
    return rupture(user)
    

@app.route('/michael/<user>')
def michael(user):
    checkUser()
    req=["SELECT code,libW,sum(qte) from facturation where etatProd<>4 and idCmd in (SELECT id_commande from commande where etatCmd=1 and corbeille=0) group by code order by sum(qte) DESC",()] 
    lignes=lecture_BDD(req)
    Lstock=[]
    for l in lignes:
        code=l["code"]
        req=["SELECT date from prevision where code=?",(code,)]
        Ldate=lecture_BDD(req)
        if len(Ldate)>0:
            date=Ldate[0]["date"]
        else:
            date=datetime.today().strftime('%d-%m-%Y')
        stockSorgues=getStockSorgues(code)
        stockRes=stockSorgues[0]
        stockTot=int(stockSorgues[1])+int(stockSorgues[0])
        stockAutre=getStockAutres(code)
        for s in stockAutre:
            stockTot+=int(s)
        stockPrev=stockTot-l["sum(qte)"]
        Lstock.append([stockRes,stockTot,stockPrev,date])
    write_log(str(session['user']['id']),"/michael - Visualisation")
    return render_template("reliquat_michael.html",user=user,lignes=lignes,Lstock=Lstock)
    

@app.route('/changeDatePrev', methods=['GET', 'POST'])
def changeDatePrev():
    checkUser()
    date=getValeurFormulaire("date")
    code=getValeurFormulaire("code")
    req=["SELECT code from prevision where code=?",(code,)]
    l=lecture_BDD(req)
    if len(l)>0:
        req=["UPDATE prevision set date=? where code=?",(date,code)]
        ecriture_BDD(req)
    else:
        req=["INSERT into prevision (date,code) values (?,?)",(date,code)]
        ecriture_BDD(req)
    write_log(str(session['user']['id']),"/changeDatePrev - Modification de la date de rupture"+str(date)+" pour le code " +str(code))
    return jsonify()
    
#endregion

####################### 3-Monde facturer - OngletFacturer ###############################
#region
@app.route('/choixLot/<user>', methods=['GET', 'POST'])
def choixLot(user):
    checkUser()
    lot=session['user']['lot']
    ref=getValeurFormulaire("ref")
    if ref!=None:
        write_log(str(session['user']['id']),"/choixLot - Visualisation sur la référente "+str(ref))
        req=["SELECT distinct commande.idCE,utilisateur.prenom,entreprise,lot,dateLot from commande inner join listingCE on commande.idCE=listingCE.idCE JOIN utilisateur ON listingCE.referente=utilisateur.id where etatCmd=1 and commande.corbeille=0 and listingCE.referente=? and listingCE.corbeille=0 order by lot",(ref,)]
        ref=int(ref)
    else:
        write_log(str(session['user']['id']),"/choixLot - Visualisation sur toutes les référentes")
        req=["SELECT distinct commande.idCE,utilisateur.prenom,entreprise,lot,dateLot from commande inner join listingCE on commande.idCE=listingCE.idCE JOIN utilisateur ON listingCE.referente=utilisateur.id where etatCmd=1 and commande.corbeille=0 and listingCE.corbeille=0 order by lot",()]
    
    listLot=lecture_BDD(req)
    nbClient=[]
    for client in listLot:
        req=["SELECT count(*),idCE from commande where lot=? and etatCmd=1 and corbeille=0",(client["lot"],)]
        nbClient.append(lecture_BDD(req)[0]["count(*)"])
    listeRef,listeAll=getListRef()
    dateLim=(datetime.today()-timedelta(days=15)).strftime('%Y-%m-%d')
    return render_template('facturation_selectLot.html',user=user,listLot=listLot,lot=lot,nbClient=nbClient,ref=ref,listeRef=listeRef,listeAll=listeAll,dateLim=dateLim)
    

@app.route('/selectLot/<user>', methods=['GET', 'POST'])
def selectLot(user):
    checkUser()
    lot=int(getValeurFormulaire('lot'))
    session['user']['lot']=lot
    mode=getValeurFormulaire('mode')
    if mode=="1":
        return defReliquat(user)
    write_log(str(session['user']['id']),"/selectLot - Sélection du lot n°"+str(lot))
    return fact(user)
    

@app.route('/suprLot/<user>', methods=['GET', 'POST'])
def suprLot(user):
    checkUser()
    lot=int(getValeurFormulaire('lot'))
    session['user']['lot']=lot
    lot=session['user']['lot']
    req=["UPDATE facturation set etatProd=0,etatMin=0,etatMax=0 where idCmd in (SELECT id_commande from commande where lot=? and corbeille=0)",(lot,)]
    ecriture_BDD(req)
    req=["UPDATE commande set lot=NULL,etatCmd=0,dateLot=NULL where lot=? and etatCmd=1 and corbeille=0",(lot,)]
    ecriture_BDD(req)
    write_log(str(session['user']['id']),"/suprLot - Suppression du lot n°"+str(lot))
    return reliquats(user)
    

@app.route('/facturation/<user>',methods=['GET', 'POST'])
def fact(user): 
    checkUser()
    lot=session['user']['lot']
    req=["SELECT * from client join commande on idclient=idclientCmd where lot=? and etatCmd=1 and commande.corbeille=0 order by client",(lot,)]
    Lclients=lecture_BDD(req)
    Lbonstot=[]
    LEtatTot=[]
    Lsomme=[]
    for client in Lclients:
        idCmd=client["id_commande"]
        req=["SELECT idProd,code,lib,libW,prix,qte,ato,etatProd,idHW,etatMin from facturation where idCmd=? and etatProd<>4",(idCmd,)]
        bons=lecture_BDD(req)
        req=["SELECT sum(qte) from facturation where idCmd=? and etatProd<>4",(idCmd,)]
        somme=lecture_BDD(req)
        Lsomme.append(somme[0]["sum(qte)"])
        sousLEtat=[]
        for cmd in bons:
            Letat=cmd['etatProd']
            Letat=Letat.split(";")
            sousLEtat.append(Letat)
        LEtatTot.append(sousLEtat)
        Lbonstot.append(bons)
    try:
        req=["SELECT idCE from commande where lot=? LIMIT 1",(lot,)]
        idCE=lecture_BDD(req)[0]["idCE"]
        req=["SELECT entreprise from listingCE where idCE=? and corbeille=0 LIMIT 1",(idCE,)]
        nomCE=lecture_BDD(req)[0]["entreprise"]
        req=["SELECT utilisateur.prenom from listingCE JOIN utilisateur ON listingCE.referente=utilisateur.id where idCE=? and corbeille=0 LIMIT 1",(idCE,)]
        referente=lecture_BDD(req)[0]["prenom"]
    except :
        idCE=""
        nomCE=""
        referente=""
    write_log(str(session['user']['id']),"/facturation - Visualisation du lot n°"+str(lot))
    return render_template('facturation_general.html',user=user,nomCE=nomCE,Lclients=Lclients,Lbons=Lbonstot,idCE=idCE,lot=lot,LEtatTot=LEtatTot,Lsomme=Lsomme,referente=referente)
    

@app.route('/changeEtat', methods=['GET', 'POST'])
def changeEtat():
    checkUser()
    name=getValeurFormulaire("name")
    idCmd=name.split("-")[1]
    idQte=name.split("-")[0]
    etatCmd=getValeurFormulaire("etatCmd")
    req=["SELECT etatProd from facturation where idProd=?",(idCmd,)]
    Letat=lecture_BDD(req)[0]['etatProd']
    Letat=Letat.split(";")
    Letat[int(idQte)]=etatCmd
    minEtat=min(Letat)
    maxEtat=max(Letat)
    strEtatCmd = ";".join(Letat)
    req=["UPDATE facturation set etatProd=?,etatMin=?,etatMax=? where idProd=?",(strEtatCmd,minEtat,maxEtat,idCmd)]
    ecriture_BDD(req)
    write_log(str(session['user']['id']),"/changeEtat - Modification de l'état de la commande n°"+str(idCmd))
    return '', 204
    

@app.route('/nextStep/<user>', methods=['GET', 'POST'])
def nextStep(user):
    checkUser()
    action=getValeurFormulaire("action")
    lot=session['user']['lot']
    if action=="valider":
        lot=session['user']['lot']
        date=datetime.today().strftime('%Y-%m-%d-%H_%M_%S')
        req=["SELECT id_commande,mail,client,idCE from commande join client on idclientcmd=idclient where lot=? and etatCmd=1 and corbeille=0 order by client",(lot,)]
        commandes=lecture_BDD(req)
        req=["SELECT mail,mailCl,mailInterFact,mailInterRelFact,mailInterRel,mailInterRupt from listingCE where idCE=? and corbeille=0",(commandes[0]['idCE'],)]
        LmailCE=lecture_BDD(req)
        nbrPdt=getValeurFormulaire("nbrePdt")
        if len(LmailCE)>0:
            mailCl=LmailCE[0]['mailCl']
            mailInterFact=LmailCE[0]['mailInterFact']
            mailInterRelFact=LmailCE[0]['mailInterRelFact']
            mailInterRel=LmailCE[0]['mailInterRel']
            mailInterRupt=LmailCE[0]['mailInterRupt']
            mail=LmailCE[0]['mail']
        else:
            mail=''
            mailCl=1
            mailInterFact=0
            mailInterRelFact=0
            mailInterRel=0
            mailInterRupt=0
        Lfiles=request.files.getlist("file")
        i=0
        LidFact=[]
        qteFact=0
        for file in Lfiles:
            if file.filename!='':
                ext=file.filename.split(".")[1]
                file.save(os.path.join(app.config['FACTURE_FOLDER'], str(commandes[i]["id_commande"]) + "-"+date+"."+ext))
                LidFact.append(commandes[i]["id_commande"])
            i+=1
        date=datetime.today().strftime('%Y-%m-%d')
        for cmd in commandes:
            emailCE=mail
            emailClient=cmd["mail"]
            Lrupt=[]
            Lrel=[]
            req=["SELECT etatMin,mailRupt,mailRel,code,libW,etatProd,idProd from facturation where idCmd=?",(cmd["id_commande"],)]
            LetatProd=lecture_BDD(req)
            mini=5
            for etat in LetatProd:
                L=etat["etatProd"].split(";")
                if etat["etatMin"]<mini:
                    mini=etat["etatMin"]
                if etat["mailRupt"]!=1 and "3" in L:
                    req=["UPDATE facturation set mailRupt=1 where idProd=?",(etat["idProd"],)]
                    ecriture_BDD(req)
                    Lrupt.append([etat["code"],etat["libW"]])
                if etat["mailRel"]!=1 and "1" in L:
                    req=["UPDATE facturation set mailRel=1 where idProd=?",(etat["idProd"],)]
                    Lrel.append([etat["code"],etat["libW"]])
                    ecriture_BDD(req)
            Linfo=[cmd["mail"],cmd["client"],str(cmd["id_commande"]),0]
            #Il y a des ruptures        
            if len(Lrupt)>0:
                Linfo[3]=4
                if mailCl==1:
                    Linfo[0]=emailClient
                    send_email(Linfo,[],Lrupt)
                if mailInterRupt==1:
                    Linfo[0]=emailCE
                    send_email(Linfo,[],Lrupt)
            #Il y a des reliquats
            if len(Lrel)>0:
                Linfo[3]=3.5
                if mailCl==1:
                    Linfo[0]=emailClient
                    send_email(Linfo,[],Lrel)
                if mailInterRel==1:
                    Linfo[0]=emailCE
                    send_email(Linfo,[],Lrel)

            Lfact=[]
            if cmd["id_commande"] in LidFact:
                for facture in os.listdir(app.config['FACTURE_FOLDER']) :
                    if facture.startswith(str(cmd['id_commande'])+"-"):
                        Lfact.append(app.config['FACTURE_FOLDER']+"/"+facture)
            #Il y a des facturés 
            if len(Lfact)>0:
                #Liste des produits en reliquat ou non traités
                req=["SELECT idProd from facturation where etatMin<2 and idCmd=?",(cmd["id_commande"],)]
                l=lecture_BDD(req)
                #Liste des produits facturés
                req=["SELECT idProd from facturation where etatProd LIKE '%2%' and idCmd=?",(cmd["id_commande"],)]
                l2=lecture_BDD(req)
                #il y a des reliquats ou produits en prép
                if len(l2)>0:
                    if (len(l)>0):
                        Linfo[3]=3
                        if mailInterRelFact==1:
                            Linfo[0]=emailCE
                            send_email(Linfo,Lfact,[])
                        if mailCl==1:
                            Linfo[0]=emailClient
                            send_email(Linfo,Lfact,[])
                    else:
                        Linfo[3]=2
                        if mailInterFact==1:
                            Linfo[0]=emailCE
                            send_email(Linfo,Lfact,[])
                        if mailCl==1:
                            Linfo[0]=emailClient
                            send_email(Linfo,Lfact,[])
                 
            else:
                print("pas de facture")
            if mini<2:
                b=1
            elif mini==2:
                b=2
                qteFact+=1
                req=["UPDATE commande set dateFact=?,facturedBy=? where id_commande=?",(date,user,cmd["id_commande"],)]
                ecriture_BDD(req)
            elif mini>2:
                #On livre direct la commande
                b=5
                req=["UPDATE commande set dateFact=?,facturedBy=?,deliveredBy=? where id_commande=?",(date,user,user,cmd["id_commande"],)]
                ecriture_BDD(req)
            req=["UPDATE commande set etatCmd=?,facturedBy=? where id_commande=?",(b,user,cmd["id_commande"],)]
            ecriture_BDD(req)
        #STATS-FACTURATION
        qtePdt=getValeurFormulaire('qtePdt')
        req=["INSERT INTO stats  (date,idUser,action,cde,pdt,lot) VALUES (?,?,?,?,?,?)",(date,user,'facturer',qteFact,qtePdt,lot)]
        ecriture_BDD(req)
        write_log(str(session['user']['id']),"/nextStep - Validation des données facturées pour le lot n°"+str(lot))

    elif action=="validerSansMail":
        lot=session['user']['lot']
        date=datetime.today().strftime('%Y-%m-%d-%H_%M_%S')
        req=["SELECT id_commande,mail,client,idCE from commande join client on idclientcmd=idclient where lot=? and etatCmd=1 and corbeille=0 order by client",(lot,)]
        commandes=lecture_BDD(req)
        req=["SELECT mail from listingCE where idCE=? and corbeille=0",(commandes[0]['idCE'],)]
        LmailCE=lecture_BDD(req)
        nbrPdt=getValeurFormulaire("nbrePdt")
        Lfiles=request.files.getlist("file")
        i=0
        LidFact=[]
        qteFact=0
        for file in Lfiles:
            if file.filename!='':
                ext=file.filename.split(".")[1]
                file.save(os.path.join(app.config['FACTURE_FOLDER'], str(commandes[i]["id_commande"]) + "-"+date+"."+ext))
                LidFact.append(commandes[i]["id_commande"])
            i+=1
        date=datetime.today().strftime('%Y-%m-%d')
        for cmd in commandes:
            Lrupt=[]
            req=["SELECT etatMin,mailRupt,code,libW,etatProd,idProd from facturation where idCmd=?",(cmd["id_commande"],)]
            LetatProd=lecture_BDD(req)
            mini=5
            for etat in LetatProd:
                L=etat["etatProd"].split(";")
                if etat["etatMin"]<mini:
                    mini=etat["etatMin"]
                if etat["mailRupt"]!=1 and "3" in L:
                    req=["UPDATE facturation set mailRupt=1 where idProd=?",(etat["idProd"],)]
                    ecriture_BDD(req)
                    Lrupt.append([etat["code"],etat["libW"]])

            Lfact=[]
            if cmd["id_commande"] in LidFact:
                for facture in os.listdir(app.config['FACTURE_FOLDER']) :
                    if facture.startswith(str(cmd['id_commande'])+"-"):
                        Lfact.append(app.config['FACTURE_FOLDER']+"/"+facture)

            if len(Lfact)>0:
                req=["SELECT idProd from facturation where etatMin<2 and idCmd=?",(cmd["id_commande"],)]
                l=lecture_BDD(req)
                req=["SELECT idProd from facturation where etatMin=2 and idCmd=?",(cmd["id_commande"],)]
                l2=lecture_BDD(req)
                Linfo=[cmd["mail"],cmd["client"],str(cmd["id_commande"])]
                #il y a des reliquats ou produits en prép
                if (len(l)>0) and (len(l2)>0):
                    Linfo.append(3)
                elif len(l)>0:
                    Linfo.append(3.5)
            else:

                req=["SELECT idProd from facturation where etatMin<2 and idCmd=?",(cmd["id_commande"],)]
                l=lecture_BDD(req)
                req=["SELECT idProd from facturation where etatMin=2 and idCmd=?",(cmd["id_commande"],)]
                l2=lecture_BDD(req)
                Linfo=[cmd["mail"],cmd["client"],str(cmd["id_commande"])]
                #il y a des reliquats ou produits en prép
                if (len(l)>0) and (len(l2)>0):
                    Linfo.append(3)
                elif len(l)>0:
                    Linfo.append(3.5)
                else:
                    Linfo.append(2)
            if mini<2:
                b=1
            elif mini==2:
                b=2
                qteFact+=1
                req=["UPDATE commande set dateFact=?,facturedBy=? where id_commande=?",(date,user,cmd["id_commande"],)]
                ecriture_BDD(req)
            else:
                b=3
                req=["UPDATE commande set dateFact=?,facturedBy=? where id_commande=?",(date,user,cmd["id_commande"],)]
                ecriture_BDD(req)
            req=["UPDATE commande set etatCmd=?,facturedBy=? where id_commande=?",(b,user,cmd["id_commande"],)]
            ecriture_BDD(req)
        #STATS-FACTURATION
        qtePdt=getValeurFormulaire('qtePdt')
        req=["INSERT INTO stats  (date,idUser,action,cde,pdt,lot) VALUES (?,?,?,?,?,?)",(date,user,'facturer',qteFact,qtePdt,lot)]
        ecriture_BDD(req)
        write_log(str(session['user']['id']),"/nextStep - validation des données facturées pour le lot n° (sans mail)"+str(lot))

    elif action=="info":
        write_log(str(session['user']['id']),"/nextStep - Visualisation synthèse des infos CE du lot n°"+str(lot))
        session['user']['page']="facturation"
        return facturationInfo(user)
    else:
        idCmd=action.split('-')[1]
        action=action.split('-')[0]
        montant1=getValeurFormulaire("montant-"+idCmd)
        numFact=getValeurFormulaire("numFact")
        if montant1=="" or montant1=="0":
            return '', 204
        else:
            montant1.replace(",",".")
            montant=str("%.2f" % float(montant1))
            date1=datetime.today().strftime('%Y-%m-%d_%H:%M:%S')
            date=date1.split('_')[0]
            heure=date1.split('_')[1]
            etat="0"
            #ici
            req=["SELECT MAX(idPaiement) FROM paiement WHERE idCd=? and type=?",(idCmd,action)]
            idPaiement=lecture_BDD(req)[0]['MAX(idPaiement)']
            if idPaiement==None:
                idPaiement=1
            else:
                idPaiement=int(idPaiement)+1

            req=["INSERT INTO paiement (idCd,type,date,heure,etat,montant,relance,idPaiement,lastOne) VALUES (?,?,?,?,?,?,?,?,?)",(idCmd,action,date,heure,etat,montant,1,idPaiement,1)]
            ecriture_BDD(req)
            req=["SELECT SUM(qte),idclientCmd,commande.idCE,client.adresse,client.mail,client,referente FROM facturation JOIN commande ON id_commande=idCmd JOIN client ON idclientCmd=idclient JOIN listingCE ON listingCE.idCE=commande.idCE where idCmd=?",(idCmd,)]
            liste=lecture_BDD(req)
            nbrPdt=liste[0]["SUM(qte)"]
            idClient=liste[0]["idclientCmd"]
            idCE=liste[0]["idCE"]
            adresse=str(liste[0]["adresse"])
            mail=liste[0]["mail"]
            client=liste[0]["client"]
            idRef=liste[0]["referente"]
            send_email([str(mail),str(client),str(idCmd),action,montant,str(nbrPdt),adresse,idCmd,str(idClient),str(idCE),str(idRef)],[],[])
            write_log(str(session['user']['id']),"/nextStep - Demande de paiement pour la commande n°"+str(idCmd))
            return '', 204    
    return fact(user)

    

@app.route('/facturationInfo/<user>', methods=['GET', 'POST'])
def facturationInfo(user):
    checkUser()
    if session['user']['page']=="facturation":
        lot=session['user']['lot']
        action=getValeurFormulaire("action")
        req=["SELECT idCE from commande where lot=? LIMIT 1",(lot,)]
        idCE=lecture_BDD(req)[0]["idCE"]
    else:
        idCde=session['user']['idDetailCmd']
        action=getValeurFormulaire("action")
        req=["SELECT idCE,lot from commande where id_commande=? LIMIT 1",(idCde,)]
        idCE=lecture_BDD(req)[0]["idCE"]
        lot=lecture_BDD(req)[0]["lot"]
    if action=="0":
        adresse=getValeurFormulaire("adresse")
        qteFact=getValeurFormulaire("qteFact")
        sac=getValeurFormulaire("sac")
        retraitMag=getValeurFormulaire("retraitMag")
        colisIndiv=getValeurFormulaire("colisIndiv")
        colisCol=getValeurFormulaire("colisCol")
        colisExpe=getValeurFormulaire("colisExpe")
        catalogue=getValeurFormulaire("catalogue")
        commentaires=getValeurFormulaire("commentaires")
        mailClient=getValeurFormulaire("mailClient")
        mailInterPrep=getValeurFormulaire("mailInterPrep")
        mailInterFact=getValeurFormulaire("mailInterFact")
        mailInterRelFact=getValeurFormulaire("mailInterRelFact")
        mailInterRel=getValeurFormulaire("mailInterRel")
        mailInterRupt=getValeurFormulaire("mailInterRupt")
        mCl=0
        minterPrep=0
        minterFact=0
        minterRelFact=0
        minterRel=0
        minterRupt=0
        if mailClient=="on":
            mCl=1
        if mailInterPrep=="on":
            minterPrep=1
        if mailInterFact=="on":
            minterFact=1
        if mailInterRelFact=="on":
            minterRelFact=1
        if mailInterRel=="on":
            minterRel=1    
        if mailInterRupt=="on":
            minterRupt=1 
        req=["UPDATE listingCE SET qteFact=?,sac=?,retraitMag=?,colisIndiv=?,colisCol=?,colisExpe=?,catalogue=?,commentaires=?,adresse=?,mailCl=?,mailInterPrep=?, mailInterFact=?,mailInterRelFact=?,mailInterRel=?,mailInterRupt=? WHERE idCE=?",(qteFact,sac,retraitMag,colisIndiv,colisCol,colisExpe,catalogue,commentaires,adresse,mCl,minterPrep,minterFact,minterRelFact,minterRel,minterRupt,idCE)]
        ecriture_BDD(req)
        write_log(str(session['user']['id']),"/facturationInfo - Modification du CE n°"+str(idCE))

    if action=="1":
        if session['user']['page']=="facturation":
            return (fact(user))
        else:
            return (detailsCmd(user))
    try:  
        req=["SELECT entreprise from listingCE where idCE=? and corbeille=0 LIMIT 1",(idCE,)]
        nomCE=lecture_BDD(req)[0]["entreprise"]
        req=["SELECT utilisateur.prenom from listingCE JOIN utilisateur ON listingCE.referente=utilisateur.id where idCE=? and corbeille=0 LIMIT 1",(idCE,)]
        referente=lecture_BDD(req)[0]["prenom"]
        req=["SELECT qteFact,sac,retraitMag,colisIndiv,colisCol,colisExpe,catalogue,commentaires,adresse,mailCl,mailInterPrep,mailInterFact,mailInterRelFact,mailInterRel,mailInterRupt FROM listingCE WHERE idCE=?",(idCE,)]
        listeInfo=lecture_BDD(req)
        qteFact=listeInfo[0]['qteFact']
        sac=listeInfo[0]['sac']
        retraitMag=listeInfo[0]['retraitMag']
        colisIndiv=listeInfo[0]['colisIndiv']
        colisCol=listeInfo[0]['colisCol']
        colisExpe=listeInfo[0]['colisExpe']
        commentaires=listeInfo[0]['commentaires']
        adresse=listeInfo[0]['adresse']
        catalogue=listeInfo[0]['catalogue']
        mailClient=listeInfo[0]['mailCl']
        mailInterPrep=listeInfo[0]['mailInterPrep']
        mailInterFact=listeInfo[0]['mailInterFact']
        mailInterRelFact=listeInfo[0]['mailInterRelFact']
        mailInterRel=listeInfo[0]['mailInterRel']
        mailInterRupt=listeInfo[0]['mailInterRupt']
    except :
        idCE=""
        nomCE=""
        referente=""
        listeInfo=""
    return render_template('facturation_info.html',user=user,adresse=adresse,nomCE=nomCE,idCE=idCE,lot=lot,referente=referente,qteFact=qteFact,sac=sac,retraitMag=retraitMag,colisIndiv=colisIndiv,colisCol=colisCol,colisExpe=colisExpe,catalogue=catalogue,commentaires=commentaires,mailClient=mailClient,mailInterPrep=mailInterPrep,mailInterFact=mailInterFact,mailInterRelFact=mailInterRelFact,mailInterRel=mailInterRel,mailInterRupt=mailInterRupt)


@app.route('/recap/<user>',methods=['GET', 'POST'])
def recap(user):
    checkUser()
    lot=session['user']['lot']
    req=["SELECT * from facturation where etatProd<>4 and idCmd in (SELECT id_commande from commande where lot=? and corbeille=0) order by code",(lot,)]
    lignes=lecture_BDD(req)
    req=["SELECT distinct code from facturation where idCmd in (SELECT id_commande from commande where lot=? and corbeille=0) order by code",(lot,)]
    Lcode=lecture_BDD(req)
    Lreliquats=[]
    for code in Lcode:
        req=["SELECT idReliquat,mag,qte from reliquats where lot=? and code=?",(lot,code['code'])]
        reliquats=lecture_BDD(req)
        Lreliquats.append(reliquats)

    code,ean,lib,qte,Letat=[],[],[],[],[]
    for l in lignes:
        strCode=l['code']
        intQte=int(l['qte'])
        etat=l['etatProd'].split(";")

        try :
            index=code.index(strCode)
            qte[index]=qte[index]+intQte
            Letat[index]+=etat

        except ValueError:
            code.append(strCode)
            qte.append(intQte)
            lib.append(l['libW'])
            ean.append(l['ean'])
            Letat.append(etat)

    try:
        req=["SELECT idCE from commande where lot=? LIMIT 1",(lot,)]
        idCE=lecture_BDD(req)[0]["idCE"]
        req=["SELECT entreprise from listingCE where idCE=? and corbeille=0 LIMIT 1",(idCE,)]
        nomCE=lecture_BDD(req)[0]["entreprise"]
    except:
        idCE=""
        nomCE=""
    write_log(str(session['user']['id']),"/recap - Visualisation du lot n°"+str(lot))
    return render_template('facturation_recap.html',user=user,nomCE=nomCE,idCE=idCE,lot=lot,code=code,ean=ean,lib=lib,quantite=qte,Letat=Letat,nProd=len(code),Lreliquats=Lreliquats)

    
    
@app.route('/clientRupt/<user>', methods=['GET', 'POST'])
def clientRupt(user):
    checkUser()
    ref=getValeurFormulaire("ref")
    if ref!=None:
        write_log(str(session['user']['id']),"/clientRupt - Visualisation avec filtre sur la référente°"+str(ref))
        req=["SELECT distinct client,commande.idCE,client.tel,client.mail,lot,date,id_commande,entreprise,utilisateur.id FROM client join commande on idclient=idclientCmd join listingCE on commande.idCE=listingCE.idCE JOIN utilisateur ON listingCE.referente=utilisateur.id where clientRupt is null and listingCE.referente=? and listingCE.corbeille=0 and id_commande in (SELECT id_commande from commande join facturation on idCmd=id_commande where etatProd LIKE '%3%')",(ref,)]
        ref=int(ref)
    else:
        write_log(str(session['user']['id']),"/clientRupt - Visualisation sans filtre référente")
        req=["SELECT distinct client,commande.idCE,client.tel,client.mail,lot,date,id_commande,entreprise,utilisateur.id FROM client join commande on idclient=idclientCmd join listingCE on commande.idCE=listingCE.idCE JOIN utilisateur ON listingCE.referente=utilisateur.id where clientRupt is null and listingCE.corbeille=0 and id_commande in (SELECT id_commande from commande join facturation on idCmd=id_commande where etatProd LIKE '%3%')",()]
    
    Lclient=lecture_BDD(req)
    Lprod=[]
    listeRef,listeAll=getListRef()
    for client in Lclient:
        req=["SELECT code,libW,prix,qte from facturation where idCmd=? and etatMax=3",(client["id_commande"],)]
        prod=lecture_BDD(req)
        Lprod.append(prod)
    write_log(str(session['user']['id']),"/clientRupt - Visualisation")
    return render_template('facturation_clientRupt.html',user=user,Lclient=Lclient,Lprod=Lprod,listeRef=listeRef,listeAll=listeAll)

    
@app.route('/modifClientRupt',methods=["POST","GET"])
def modifClientRupt():
    checkUser()
    idCmd=getValeurFormulaire("idCmd")
    check=getValeurFormulaire("check")
    if check=="1":
        req=["UPDATE commande set clientRupt=1 where id_commande=?",(idCmd,)]
    else:
        req=["UPDATE commande set clientRupt=NULL where id_commande=?",(idCmd,)]
    ecriture_BDD(req)
    write_log(str(session['user']['id']),"/modifClientRupt - Modification de la commande n°"+str(idCmd))

    return jsonify()
    
#endregion

####################### 4-Monde des paiements - OngletPaiements #########################
#region

@app.route('/paiements/<user>',methods=['GET', 'POST'])
def paiements(user):
    checkUser()
    action=getValeurFormulaire('filtre')
    #réactulisation du filtre 
    if action=='filtre':
        session['user']['paiementDateMin']="-1"
        session['user']['paiementDateMax']="-1"
        session['user']['paiementID']="-1"
        session['user']['paiementLot']="-1"
        session['user']['paiementCE']="-1"
        session['user']['paiementNom']="-1"
        session['user']['paiementType']="-1"
        session['user']['paiementMontant']="-1"
    #vérification de la sauvegarde des filtres
    if (session['user']['paiementDateMin']!='-1' or session['user']['paiementDateMax']!='-1' or session['user']['paiementID']!='-1' or session['user']['paiementLot']!='-1' or session['user']['paiementCE']!='-1' or session['user']['paiementNom']!='-1' or session['user']['paiementMontant']!='-1' or session['user']['paiementType']!='-1'):
        return(searchImpaye(user))
    ref=getValeurFormulaire("ref")
    if ref!=None:
        write_log(str(session['user']['id']),"/paiements - Visualisation avec la réferente n°"+str(ref))
        req=["SELECT DISTINCT idUnique,idCd,paiement.date,heure,type,montant,idCE,lot,client,relance,idPaiement FROM paiement join commande ON id_commande=idCd JOIN client on idclientCmd=idclient and idCE in (SELECT idCE from listingCE where listingCE.referente=? and corbeille=0) AND etat=0 order by paiement.date ASC, heure ASC  LIMIT 200",(ref,)]
        ref=int(ref)
    else:
        write_log(str(session['user']['id']),"/paiements - Visualisation sans filtre de référente")
        req=["SELECT DISTINCT idUnique,idCd,paiement.date,heure,type,montant,idCE,lot,client,relance,idPaiement FROM paiement join commande ON id_commande=idCd JOIN client ON idclientCmd=idclient where commande.corbeille=0 AND etat=0 order by paiement.date ASC, heure ASC LIMIT 200",()]
    Lclients=lecture_BDD(req)
    listeRef,listeAll=getListRef()
    return render_template('paiement_impaye.html',Lclients=Lclients,user=user,ref=ref,listeRef=listeRef,listeAll=listeAll)

@app.route('/searchImpaye/<user>',methods=['GET', 'POST'])
def searchImpaye(user):
    checkUser()
    dateMin=str(getValeurFormulaire("dateMin"))
    dateMax=str(getValeurFormulaire("dateMax"))
    idCmd=str(getValeurFormulaire("idCmd"))
    idCE=str(getValeurFormulaire("idCE"))
    lot=str(getValeurFormulaire("lot"))
    client=str(getValeurFormulaire("client"))
    type=str(getValeurFormulaire("type"))
    montant=str(getValeurFormulaire("montant"))
    ref=getValeurFormulaire("ref")
    sansDateMini=False
    sansDateMax=False
    #Clés du filtre par session
    if session['user']['paiementDateMin']!='-1':
        if dateMin=="" or dateMin==None or dateMin=="None":
            dateMin=session['user']['paiementDateMin']
        else:
            session['user']['paiementDateMin']=dateMin
    else:
        if dateMin=="" or dateMin==None  or dateMin=="None":
            session['user']['paiementDateMin']='-1'
            sansDateMini=True
            dateMin=""
        else:
            session['user']['paiementDateMin']=dateMin

    if session['user']['paiementDateMax']!='-1':
        if dateMax=="" or dateMax==None  or dateMax=="None":
            dateMax=session['user']['paiementDateMax']
        else:
            session['user']['paiementDateMax']=dateMax
    else:
        if dateMax=="" or dateMax==None  or dateMax=="None":
            session['user']['paiementdateMax']='-1'
            sansDateMax=True
            dateMax=""
        else:
            session['user']['paiementDateMax']=dateMax

    if session['user']['paiementID']!='-1' :
        if idCmd=="" or idCmd=="None" :
            idCmd=session['user']['paiementID']
        else:
            session['user']['paiementID']=idCmd
    else:
        if idCmd=="" or idCmd=="None":
            session['user']['paiementID']='-1'
            idCmd=""
        else:
            session['user']['paiementID']=idCmd

    if session['user']['paiementCE']!='-1':
        if idCE=="" or idCE=="None":
            idCE=session['user']['paiementCE']
        else:
            session['user']['paiementCE']=idCE
    else:
        if idCE=="" or idCE=="None":
            session['user']['paiementCE']='-1'
            idCE=""
        else:
            session['user']['paiementCE']=idCE

    if session['user']['paiementNom']!='-1':
        if client=="" or client=="None" or client==None:
            client=session['user']['paiementNom']
        else:
            session['user']['paiementNom']=client  
    else:
        if client=="" or client=="None" or client==None:
            session['user']['paiementNom']='-1'
            client=""
        else:
            session['user']['paiementNom']=client

    if session['user']['paiementType']!='-1':
        if type==None or type=="None":
            type=session['user']['paiementType']
        else:
            session['user']['paiementType']=type
    else:
        if type==None or type=='None':
            type=""
        session['user']['paiementType']=type

    if session['user']['paiementMontant']!='-1':
        if montant==None or montant=="None":
            montant=session['user']['paiementMontant']
        else:
            session['user']['paiementMontant']=montant
    else:
        if montant==None or montant=='None':
            montant=""
        session['user']['paiementMontant']=montant

    if session['user']['paiementLot']!='-1':
        if lot==None or lot=="None":
            lot=session['user']['paiementLot']
        else:
            session['user']['paiementLot']=lot
    else:
        if lot==None or lot=='None':
            lot=""
        session['user']['paiementLot']=lot

    
    if ref=="None" or ref is None:
        ref1=""
    else:
        ref1=ref
        ref=int(ref)
    if sansDateMini:
        if sansDateMax:
            #ici
            req=["SELECT DISTINCT idUnique,idCd,relance,idPaiement,paiement.date,heure,type,montant,commande.idCE,lot,client FROM paiement join commande ON id_commande=idCd JOIN client on idclientCmd=idclient left join listingCE on commande.idCE=listingCE.idCE WHERE commande.corbeille=0 and idCd LIKE ? and type LIKE ? and montant LIKE ? and commande.idCE LIKE ? and lot LIKE ? and client LIKE ? and referente LIKE ? AND etat=0 order by paiement.date ASC, heure ASC  LIMIT 200",('%'+idCmd+'%','%'+type+'%','%'+montant+'%','%'+idCE+'%','%'+lot+'%','%'+client+'%','%'+ref1+'%')]
            Lclients=lecture_BDD(req)
        else:
            #ici
            req=["SELECT DISTINCT idUnique,idCd,relance,idPaiement,paiement.date,heure,type,montant,commande.idCE,lot,client FROM paiement join commande ON id_commande=idCd JOIN client on idclientCmd=idclient left join listingCE on commande.idCE=listingCE.idCE WHERE commande.corbeille=0 and idCd LIKE ? and type LIKE ? and montant LIKE ? and commande.idCE LIKE ? and lot LIKE ? and client LIKE ? and referente LIKE ? AND etat=0 and paiement.date<= (?) order by paiement.date ASC, heure ASC  LIMIT 200",('%'+idCmd+'%','%'+type+'%','%'+montant+'%','%'+idCE+'%','%'+lot+'%','%'+client+'%','%'+ref1+'%',dateMax)]
            Lclients=lecture_BDD(req)
    elif sansDateMax:
            #ici
        req=["SELECT DISTINCT idUnique,idCd,relance,idPaiement,paiement.date,heure,type,montant,commande.idCE,lot,client FROM paiement join commande ON id_commande=idCd JOIN client on idclientCmd=idclient left join listingCE on commande.idCE=listingCE.idCE WHERE commande.corbeille=0 and idCd LIKE ? and type LIKE ? and montant LIKE ? and commande.idCE LIKE ? and lot LIKE ? and client LIKE ? and referente LIKE ? AND etat=0 and paiement.date>= (?) order by paiement.date ASC, heure ASC  LIMIT 200",('%'+idCmd+'%','%'+type+'%','%'+montant+'%','%'+idCE+'%','%'+lot+'%','%'+client+'%','%'+ref1+'%',dateMin)]
        Lclients=lecture_BDD(req)
    else:
            #ici
        req=["SELECT DISTINCT idUnique,idCd,relance,idPaiement,paiement.date,heure,type,montant,commande.idCE,lot,client FROM paiement join commande ON id_commande=idCd JOIN client on idclientCmd=idclient left join listingCE on commande.idCE=listingCE.idCE WHERE commande.corbeille=0 and idCd LIKE ? and type LIKE ? and montant LIKE ? and commande.idCE LIKE ? and lot LIKE ? and client LIKE ? and referente LIKE ? AND etat=0 and paiement.date>= (?) and paiement.date<= (?) order by paiement.date ASC, heure ASC  LIMIT 200",('%'+idCmd+'%','%'+type+'%','%'+montant+'%','%'+idCE+'%','%'+lot+'%','%'+client+'%','%'+ref1+'%',dateMin,dateMax)]
        Lclients=lecture_BDD(req)
    
    listeRef,listeAll=getListRef()
    write_log(str(session['user']['id']),"/searchImpayes - Visualisation")
    return render_template('paiement_impaye.html',user=user,Lclients=Lclients,dateMin=dateMin,dateMax=dateMax,montant=montant,idCmd=idCmd,idCE=idCE,client=client,lot=lot,type=type,ref=ref,listeRef=listeRef,listeAll=listeAll)


@app.route('/relancePaiement',methods=['GET', 'POST'])
def relance():
    checkUser()
    date1=datetime.today().strftime('%Y-%m-%d_%H:%M:%S')
    date=date1.split('_')[0]
    heure=date1.split('_')[1]
    id=getValeurFormulaire('id')
    idCmd=id.split('-')[0]
    idPaiement=id.split('-')[1]
    idRelance=id.split('-')[2]
    montant=id.split('-')[3]
    montant='%.2f'%float(montant)
    type=id.split('-')[4]
    #Annuler les paiements précédents et enlever le lastOne
    req=["UPDATE paiement SET etat=2,lastOne=0 WHERE idCd=? AND type=? AND idPaiement=? ",(idCmd,type,idPaiement)]
    ecriture_BDD(req)
    #Créer la nouvelle demande de paiement et du lastOne
    relance=int(idRelance)+1  
    req=["INSERT INTO paiement (idCd,type,date,heure,etat,montant,relance,idPaiement,lastOne) VALUES (?,?,?,?,?,?,?,?,?)",(idCmd,type,date,heure,0,montant,relance,idPaiement,1)]
    ecriture_BDD(req)
    req=["SELECT SUM(qte),idclientCmd,commande.idCE,client.adresse,client.mail,client,lot,referente FROM facturation JOIN commande ON id_commande=idCmd JOIN client ON idclientCmd=idclient JOIN listingCE ON listingCE.idCE=commande.idCE WHERE idCmd=?",(idCmd,)]
    liste=lecture_BDD(req)
    nbrPdt=liste[0]["SUM(qte)"]
    idClient=liste[0]["idclientCmd"]
    idCE=liste[0]["idCE"]
    adresse=str(liste[0]["adresse"])
    mail=liste[0]["mail"]
    client=liste[0]["client"]
    lot=liste[0]["lot"]
    idRef=liste[0]["referente"]
    idCdMail=str(idCmd)+'-'+str(idPaiement)+'-'+str(relance)
    L=[date,heure,idCmd,idCE,lot,client,type,montant,relance,idPaiement]
    try:
        send_email([str(mail),str(client),str(idCmd),type,montant,str(nbrPdt),adresse,idCdMail,str(idClient),str(idCE),str(idRef)],[],[])
        message="Mail envoyé au client"
    except:
        message="Erreur lors de l'envoi du mail"
    write_log(str(session['user']['id']),"/relancePaiement - Relance du paiments de la commande n°"+str(idCmd))
    return jsonify(message=message,L=L)
   
@app.route('/validePaiement',methods=['GET', 'POST'])
def valide():
    try :
        session['user']
        user=session['user']
    except:
        return(index())
    date1=datetime.today().strftime('%Y-%m-%d_%H:%M:%S')
    date=date1.split('_')[0]
    heure=date1.split('_')[1]
    id=getValeurFormulaire('id')
    idCmd=id.split('-')[0]
    idPaiement=id.split('-')[1]
    idRelance=id.split('-')[2]
    montant=id.split('-')[3]
    type=id.split('-')[4]
    req=["UPDATE paiement SET etat=1 where idCd=? AND idPaiement=? AND relance=? AND type=?",(idCmd,idPaiement,idRelance,type)]
    ecriture_BDD(req)
    #ici
    req=["INSERT INTO stats  (date,idUser,action,cde,pdt,lot) VALUES (?,?,?,?,?,?)",(date,user,'paiement',1,montant,idCmd)]
    ecriture_BDD(req)
    message="Demande de paiement validée"
    write_log(str(session['user']['id']),"/validePaiement - Validation du paiement de la commande n°"+str(idCmd))
    return jsonify(message=message)

@app.route('/annulePaiement',methods=['GET', 'POST'])
def annule():
    try :
        session['user']
        user=session['user']
    except:
        return(index())
    date1=datetime.today().strftime('%Y-%m-%d_%H:%M:%S')
    date=date1.split('_')[0]
    heure=date1.split('_')[1]
    id=getValeurFormulaire('id')
    idCmd=id.split('-')[0]
    idPaiement=id.split('-')[1]
    idRelance=id.split('-')[2]
    montant=id.split('-')[3]
    type=id.split('-')[4]
    req=["UPDATE paiement SET etat=2 where idCd=? AND idPaiement=? AND relance=? AND type=? AND montant=?",(idCmd,idPaiement,idRelance,type,montant)]
    ecriture_BDD(req)
    message="Demande de paiement annulée"
    write_log(str(session['user']['id']),"/annulePaiement - Annulation du paiement de la commande n°"+str(idCmd))
    return jsonify(message=message)

@app.route('/extractImpayes',methods=['GET', 'POST'])
def extractImpayes():
    try :
        session['user']
        user=session['user']
    except:
        return(index())
    action=getValeurFormulaire("action")
    if action=="0":
        export_Impayes()
        write_log(str(session['user']['id']),"/extractImpayes - Exportation du listing des impayés.csv")
    elif action=="1":
        export_Impayes_Synthese_CE()
        write_log(str(session['user']['id']),"/extractImpayes - Exportation du listing des impayésCE.csv")
    elif action=="2":
        export_Impayes_Synthese_Referente()
        write_log(str(session['user']['id']),"/extractImpayes - Exportation du listing des impayésRef.csv")
    return paiements(user) 

  
@app.route('/relanceGroupe/<user>',methods=['GET', 'POST'])
def relanceGroupe(user):
    checkUser()
    listeRelance=[]
    req=["SELECT idCd,paiement.date,heure,type,montant,idCE,lot,client,relance,idPaiement FROM paiement join commande ON id_commande=idCd JOIN client ON idclientCmd=idclient where commande.corbeille=0 AND etat=0 order by paiement.date ASC, heure ASC LIMIT 1000",()]
    LPaiement=lecture_BDD(req)
    action=getValeurFormulaire('action')
    btEnlever=session['user']['paiement2BtEnlever']
    
    if action=="annuleAll":
        for element in session['user']['listeRelance']:
            idCd=element[0]
            idPaiement=element[1]
            relance=element[2]
            type=element[3]
            #Annuler la demande de paiement
            req=["UPDATE paiement SET etat=2 where idCd=? AND idPaiement=? AND relance=? AND type=?",(idCd,idPaiement,relance,type)]
            ecriture_BDD(req)
        session['user']['listeRelance']=[]
        write_log(str(session['user']['id']),"/relanceGroupe - Annulation des paiements en masse")
        return render_template('paiement_relanceGroupe.html',LPaiement=LPaiement,user=user,listeRelance=listeRelance,btEnlever=btEnlever)

    elif action=="relanceAll":
        for element in session['user']['listeRelance']:
            date1=datetime.today().strftime('%Y-%m-%d_%H:%M:%S')
            date=date1.split('_')[0]
            heure=date1.split('_')[1]
            idCd=element[0]
            idPaiement=element[1]
            relance=element[2]
            type=element[3]
            #Récuperer données manquantes
            req=["SELECT montant FROM paiement WHERE idCd=? AND idPaiement=? AND relance=? AND type=?",(idCd,idPaiement,relance,type)]
            montant=lecture_BDD(req)[0]['montant']
            montant='%.2f'%float(montant)
            #Annuler les paiements précédents et enlever le lastOne
            req=["UPDATE paiement SET etat=2,lastOne=0 WHERE idCd=? AND type=? AND idPaiement=? ",(idCd,type,idPaiement)]
            ecriture_BDD(req)
            #Créer la nouvelle demande de paiement et du lastOne
            relance=int(relance)+1  
            req=["INSERT INTO paiement (idCd,type,date,heure,etat,montant,relance,idPaiement,lastOne) VALUES (?,?,?,?,?,?,?,?,?)",(idCd,type,date,heure,0,montant,relance,idPaiement,1)]
            ecriture_BDD(req)
            req=["SELECT SUM(qte),idclientCmd,commande.idCE,client.adresse,client. mail,client,referente FROM facturation JOIN commande ON id_commande=idCmd JOIN client ON idclientCmd=idclient JOIN listingCE ON listingCE.idCE=commande.idCE WHERE idCmd=?",(idCd,)]
            liste=lecture_BDD(req)
            nbrPdt=liste[0]["SUM(qte)"]
            idClient=liste[0]["idclientCmd"]
            idCE=liste[0]["idCE"]
            adresse=str(liste[0]["adresse"])
            mail=liste[0]["mail"]
            client=liste[0]["client"]
            idCdMail=str(idCd)+'-'+str(idPaiement)+'-'+str(relance)
            idRef=liste[0]["referente"]
            send_email([str(mail),str(client),str(idCd),type,str(montant),str(nbrPdt),adresse,idCdMail,str(idClient),str(idCE),str(idRef)],[],[])
        session['user']['listeRelance']=[]
        write_log(str(session['user']['id']),"/relanceGroupe - Relance des paiements en masse")
        return render_template('paiement_relanceGroupe.html',LPaiement=LPaiement,user=user,listeRelance=listeRelance,btEnlever=btEnlever)
        
    elif action=="valideAll":
        for element in session['user']['listeRelance']:
            date1=datetime.today().strftime('%Y-%m-%d_%H:%M:%S')
            date=date1.split('_')[0]
            heure=date1.split('_')[1]
            idCd=element[0]
            idPaiement=element[1]
            relance=element[2]
            type=element[3]
            #Récuperer données manquantes
            req=["SELECT montant FROM paiement WHERE idCd=? AND idPaiement=? AND relance=? AND type=?",(idCd,idPaiement,relance,type)]
            montant=lecture_BDD(req)[0]['montant']
            #Valide le paiement
            req=["UPDATE paiement SET etat=1 where idCd=? AND idPaiement=? AND relance=? AND type=?",(idCd,idPaiement,relance,type)]
            ecriture_BDD(req)
            #ici STATS
            req=["INSERT INTO stats  (date,idUser,action,cde,pdt,lot) VALUES (?,?,?,?,?,?)",(date,user,'paiement',1,montant,idCd)]
            ecriture_BDD(req)
        session['user']['listeRelance']=[]
        write_log(str(session['user']['id']),"/relanceGroupe - Validation des paiements en masse")
        return render_template('paiement_relanceGroupe.html',LPaiement=LPaiement,user=user,listeRelance=listeRelance,btEnlever=btEnlever)

    elif action=="enleverUn":
        session['user']['paiement2BtEnlever']='oui'
        btEnlever=session['user']['paiement2BtEnlever']
        for client in session['user']['listeRelance']:
                idCommande=client[0]
                idPaiement=client[1]
                idRelance=client[2]
                type=client[3]
                req=["SELECT idCd,paiement.date,heure,type,montant,idCE,lot,client,relance,idPaiement FROM paiement join commande ON id_commande=idCd JOIN client ON idclientCmd=idclient WHERE commande.corbeille=0 AND paiement.idCd=? AND idPaiement=? AND relance=? AND type=?",(idCommande,idPaiement,idRelance,type)]
                clientSelec=lecture_BDD(req)[0]

                if clientSelec not in listeRelance:
                    listeRelance.append(clientSelec)
        write_log(str(session['user']['id']),"/relanceGroupe - Enlever un élementn de la liste des paiements en masse")
        return render_template('paiement_relanceGroupe.html',LPaiement=LPaiement,user=user,listeRelance=listeRelance,btEnlever=btEnlever)

    else:
        if len(session['user']['listeRelance'])!=0:
            if action!=None:
                idCd=action.split('--')[0]
                idPaiement=action.split('--')[1]
                relance=action.split('--')[2]
                type=action.split('--')[3]
                liste=[idCd,idPaiement,relance,type]
                if liste in session['user']['listeRelance']:
                    session['user']['listeRelance'].remove(liste)
                    session['user']['paiement2BtEnlever']='non'
            for client in session['user']['listeRelance']:
                idCommande=client[0]
                idPaiement=client[1]
                idRelance=client[2]
                type=client[3]
                req=["SELECT idCd,paiement.date,heure,type,montant,idCE,lot,client,relance,idPaiement FROM paiement join commande ON id_commande=idCd JOIN client ON idclientCmd=idclient WHERE commande.corbeille=0 AND paiement.idCd=? AND idPaiement=? AND relance=? AND type=?",(idCommande,idPaiement,idRelance,type)]
                clientSelec=lecture_BDD(req)[0]

                if clientSelec not in listeRelance:
                    listeRelance.append(clientSelec)
        write_log(str(session['user']['id']),"/relanceGroupe - Visualisation des paiements en masse")
        
        return render_template('paiement_relanceGroupe.html',LPaiement=LPaiement,user=user,listeRelance=listeRelance,btEnlever=btEnlever)

@app.route('/ajoutImpayeGroupe', methods=['GET', 'POST'])
def ajoutImpayeGroupe():
    checkUser()
    listeRecherche=getValeurFormulaire("listeRecherche")
    idCd=listeRecherche.split(' - ')[0]
    idPaiement=listeRecherche.split(' - ')[7]
    relance=listeRecherche.split(' - ')[8]
    type=listeRecherche.split(' - ')[2]
    Linfo=[idCd,idPaiement,relance,type]
    if Linfo not in session['user']['listeRelance']:
        session['user']['listeRelance'].append(Linfo)
        taille=len(session['user']['listeRelance'])
        req=["SELECT paiement.date,heure,idCE,lot,client,type,montant FROM paiement JOIN commande ON id_commande=idCd JOIN client ON idclientCmd=idclient WHERE idCd=? AND idPaiement=? AND relance=? AND type=?",(idCd,idPaiement,relance,type)]
        liste=lecture_BDD(req)[0]
        date=liste['date']
        heure=liste['heure']
        idCE=liste['idCE']
        lot=liste['lot']
        client=liste['client']
        montant=liste['montant']
        message=""
        action=getValeurFormulaire('action')
        if action!=None:
            idCd=action.split('--')[0]
            idPaiement=action.split('--')[1]
            relance=action.split('--')[2]
            type=action.split('--')[3]
            liste=[idCd,idPaiement,relance,type]
            if liste in session['user']['listeRelance']:
                session['user']['listeRelance'].remove(liste)
            else:
                print("not in session")
        
        write_log(str(session['user']['id']),"/ajoutImpayesGroupe - Ajout d'un élement à la liste des paiements en masse")
        return jsonify(date=date,heure=heure,idCd=idCd,idCE=idCE,lot=lot,client=client,type=type,montant=montant,idPaiement=idPaiement,relance=relance,message=message)
    else:
        message="Ce paiement est déjà sélectionné dans la liste."
        return jsonify(message=message)

@app.route('/paiementsPaye/<user>',methods=['GET', 'POST'])
def paiementsPaye(user):
    checkUser()
    action=getValeurFormulaire('filtre')
    #réactulisation du filtre 
    if action=='filtre':
        session['user']['paiement2DateMin']="-1"
        session['user']['paiement2DateMax']="-1"
        session['user']['paiement2ID']="-1"
        session['user']['paiement2Lot']="-1"
        session['user']['paiement2CE']="-1"
        session['user']['paiement2Nom']="-1"
        session['user']['paiement2Type']="-1"
        session['user']['paiement2Montant']="-1"
    #vérification de la sauvegarde des filtres
    if (session['user']['paiement2DateMin']!='-1' or session['user']['paiement2DateMax']!='-1' or session['user']['paiement2ID']!='-1' or session['user']['paiement2Lot']!='-1' or session['user']['paiement2CE']!='-1' or session['user']['paiement2Nom']!='-1' or session['user']['paiement2Montant']!='-1' or session['user']['paiement2Type']!='-1'):
        return(searchPaye(user))
    ref=getValeurFormulaire("ref")
    if ref!=None:
        write_log(str(session['user']['id']),"/paiementsPaye - Filtre sur la référente "+str(ref))
        req=["SELECT DISTINCT idCd,paiement.date,heure,type,montant,idCE,lot,client,relance,idPaiement FROM paiement join commande ON id_commande=idCd JOIN client on idclientCmd=idclient and idCE in (SELECT idCE from listingCE where listingCE.referente=? and corbeille=0) AND etat=1 order by paiement.date DESC, heure DESC  LIMIT 1000",(ref,)]
        ref=int(ref)
    else:
        write_log(str(session['user']['id']),"/paiementsPaye - Filtre sur toutes les référentes")
        req=["SELECT DISTINCT idCd,paiement.date,heure,type,montant,idCE,lot,client,relance,idPaiement,idUnique FROM paiement join commande ON id_commande=idCd JOIN client ON idclientCmd=idclient where commande.corbeille=0 AND etat=1 order by paiement.date DESC, heure DESC LIMIT 1000",()]
    Lclients=lecture_BDD(req)
    listeRef,listeAll=getListRef()
    return render_template('paiement_paye.html',Lclients=Lclients,user=user,ref=ref,listeRef=listeRef,listeAll=listeAll)

@app.route('/searchPaye/<user>',methods=['GET', 'POST'])
def searchPaye(user):
    checkUser()
    dateMin=str(getValeurFormulaire("dateMin"))
    dateMax=str(getValeurFormulaire("dateMax"))
    idCmd=str(getValeurFormulaire("idCmd"))
    idCE=str(getValeurFormulaire("idCE"))
    lot=str(getValeurFormulaire("lot"))
    client=str(getValeurFormulaire("client"))
    montant=str(getValeurFormulaire("montant"))
    ref=getValeurFormulaire("ref")
    type1=str(getValeurFormulaire("type"))
    sansDateMini=False
    sansDateMax=False
    #Clés du filtre par session
    if session['user']['paiement2DateMin']!='-1':
        if dateMin=="" or dateMin==None or dateMin=="None":
            dateMin=session['user']['paiement2DateMin']
        else:
            session['user']['paiement2DateMin']=dateMin
    else:
        if dateMin=="" or dateMin==None  or dateMin=="None":
            session['user']['paiement2DateMin']='-1'
            sansDateMini=True
            dateMin=""
        else:
            session['user']['paiement2DateMin']=dateMin

    if session['user']['paiement2DateMax']!='-1':
        if dateMax=="" or dateMax==None  or dateMax=="None":
            dateMax=session['user']['paiement2DateMax']
        else:
            session['user']['paiement2DateMax']=dateMax
    else:
        if dateMax=="" or dateMax==None  or dateMax=="None":
            session['user']['paiement2dateMax']='-1'
            sansDateMax=True
            dateMax=""
        else:
            session['user']['paiement2DateMax']=dateMax

    if session['user']['paiement2ID']!='-1' :
        if idCmd=="" or idCmd=="None" :
            idCmd=session['user']['paiement2ID']
        else:
            session['user']['paiement2ID']=idCmd
    else:
        if idCmd=="" or idCmd=="None":
            session['user']['paiement2ID']='-1'
            idCmd=""
        else:
            session['user']['paiement2ID']=idCmd

    if session['user']['paiement2CE']!='-1':
        if idCE=="" or idCE=="None":
            idCE=session['user']['paiement2CE']
        else:
            session['user']['paiement2CE']=idCE
    else:
        if idCE=="" or idCE=="None":
            session['user']['paiement2CE']='-1'
            idCE=""
        else:
            session['user']['paiement2CE']=idCE

    if session['user']['paiement2Nom']!='-1':
        if client=="" or client=="None" or client==None:
            client=session['user']['paiement2Nom']
        else:
            session['user']['paiement2Nom']=client  
    else:
        if client=="" or client=="None" or client==None:
            session['user']['paiement2Nom']='-1'
            client=""
        else:
            session['user']['paiement2Nom']=client

    if session['user']['paiement2Type']!='-1':
        if type1==None or type1=="None":
            type1=session['user']['paiement2Type']
        else:
            session['user']['paiement2Type']=type1
    else:
        if type1==None or type1=='None':
            type1=""
        session['user']['paiement2Type']=type1

    if session['user']['paiement2Montant']!='-1':
        if montant==None or montant=="None":
            montant=session['user']['paiement2Montant']
        else:
            session['user']['paiement2Montant']=montant
    else:
        if montant==None or montant=='None':
            montant=""
        session['user']['paiement2Montant']=montant

    if session['user']['paiement2Lot']!='-1':
        if lot==None or lot=="None":
            lot=session['user']['paiement2Lot']
        else:
            session['user']['paiement2Lot']=lot
    else:
        if lot==None or lot=='None':
            lot=""
        session['user']['paiement2Lot']=lot
    
    if ref=="None" or ref==None:
        ref1=""
    else:
        ref1=ref
        ref=int(ref)
    if sansDateMini:
        if sansDateMax:
            #ici
            req=["SELECT DISTINCT idCd,relance,idPaiement,paiement.date,heure,type,montant,commande.idCE,lot,client,idUnique FROM paiement join commande ON id_commande=idCd JOIN client on idclientCmd=idclient left join listingCE on commande.idCE=listingCE.idCE WHERE commande.corbeille=0 and idCd LIKE ? and type LIKE ? and montant LIKE ? and commande.idCE LIKE ? and lot LIKE ? and client LIKE ? and referente LIKE ? AND etat=1 order by paiement.date DESC, heure DESC  LIMIT 1000",('%'+idCmd+'%','%'+type1+'%','%'+montant+'%','%'+idCE+'%','%'+lot+'%','%'+client+'%','%'+ref1+'%')]
            Lclients=lecture_BDD(req)
        else:
            #ici
            req=["SELECT DISTINCT idCd,relance,idPaiement,paiement.date,heure,type,montant,commande.idCE,lot,client,idUnique FROM paiement join commande ON id_commande=idCd JOIN client on idclientCmd=idclient left join listingCE on commande.idCE=listingCE.idCE WHERE commande.corbeille=0 and idCd LIKE ? and type LIKE ? and montant LIKE ? and commande.idCE LIKE ? and lot LIKE ? and client LIKE ? and referente LIKE ? AND etat=1 and paiement.date<= (?) order by paiement.date DESC, heure DESC  LIMIT 1000",('%'+idCmd+'%','%'+type1+'%','%'+montant+'%','%'+idCE+'%','%'+lot+'%','%'+client+'%','%'+ref1+'%',dateMax)]
            Lclients=lecture_BDD(req)
    elif sansDateMax:
            #ici
        req=["SELECT DISTINCT idCd,relance,idPaiement,paiement.date,heure,type,montant,commande.idCE,lot,client,idUnique FROM paiement join commande ON id_commande=idCd JOIN client on idclientCmd=idclient left join listingCE on commande.idCE=listingCE.idCE WHERE commande.corbeille=0 and idCd LIKE ? and type LIKE ? and montant LIKE ? and commande.idCE LIKE ? and lot LIKE ? and client LIKE ? and referente LIKE ? AND etat=1 and paiement.date>= (?) order by paiement.date DESC, heure DESC  LIMIT 1000",('%'+idCmd+'%','%'+type1+'%','%'+montant+'%','%'+idCE+'%','%'+lot+'%','%'+client+'%','%'+ref1+'%',dateMin)]
        Lclients=lecture_BDD(req)
    else:
            #ici
        req=["SELECT DISTINCT idCd,relance,idPaiement,paiement.date,heure,type,montant,commande.idCE,lot,client,idUnique FROM paiement join commande ON id_commande=idCd JOIN client on idclientCmd=idclient left join listingCE on commande.idCE=listingCE.idCE WHERE commande.corbeille=0 and idCd LIKE ? and type LIKE ? and montant LIKE ? and commande.idCE LIKE ? and lot LIKE ? and client LIKE ? and referente LIKE ? AND etat=1 and paiement.date>= (?) and paiement.date<= (?) order by paiement.date DESC, heure DESC  LIMIT 1000",('%'+idCmd+'%','%'+type1+'%','%'+montant+'%','%'+idCE+'%','%'+lot+'%','%'+client+'%','%'+ref1+'%',dateMin,dateMax)]
        Lclients=lecture_BDD(req)
    
    listeRef,listeAll=getListRef()
    write_log(str(session['user']['id']),"/searchPaye - Filtre")
    return render_template('paiement_paye.html',user=user,Lclients=Lclients,dateMin=dateMin,dateMax=dateMax,montant=montant,idCmd=idCmd,idCE=idCE,client=client,lot=lot,type=type1,ref=ref,listeRef=listeRef,listeAll=listeAll)
  
@app.route('/actionFromPaiementPaye/<user>', methods=['GET', 'POST'])
def actionFromPaiementPaye(user):
    checkUser()
    date1=datetime.today().strftime('%Y-%m-%d_%H:%M:%S')
    date=date1.split('_')[0]
    heure=date1.split('_')[1]
    Action=getValeurFormulaire("action")
    action=Action.split('-')[0]
    idUnique=Action.split('-')[1]
    idCmd=getValeurFormulaire('idCmd')
    idPaiement=getValeurFormulaire('idPaiement')
    idRelance=getValeurFormulaire('idRelance')
    type=getValeurFormulaire('type')
    montant=getValeurFormulaire('montant')
    if action=='annuler':
        req=["UPDATE paiement SET etat=2 where idUnique=?",(idUnique,)]
        ecriture_BDD(req)
        write_log(str(session['user']['id']),"/actionFromPaiementPaye - Annulation du paiement de la commande"+str(idCmd))
    return paiementsPaye(user)
#endregion

####################### 5-Monde des livraisons- OngletLivraison #########################
#region
@app.route('/livraison/<user>', methods=['GET', 'POST'])
def choixCELivre(user):
    checkUser()
    idCELivraison=session['user']['idCELivraison']
    ref=getValeurFormulaire("ref")
    if ref!=None:
        write_log(str(session['user']['id']),"/livraison - Filtre sur la référente "+str(ref))
        req=["SELECT distinct commande.idCE,utilisateur.prenom,entreprise from commande join listingCE on commande.idCE=listingCE.idCE JOIN utilisateur ON listingCE.referente=utilisateur.id where etatCmd>0 and etatCmd<3 and commande.corbeille=0 and listingCE.referente=? and listingCE.corbeille=0 and id_commande in (SELECT distinct idCmd from facturation where etatProd like '%2%') order by commande.idCE",(ref,)]
        ref=int(ref)
    else:
        write_log(str(session['user']['id']),"/livraison - Filtre sur toutes les référentes")
        req=["SELECT distinct commande.idCE,utilisateur.prenom,entreprise from commande join listingCE on commande.idCE=listingCE.idCE JOIN utilisateur ON listingCE.referente=utilisateur.id where etatCmd>0 and etatCmd<3 and commande.corbeille=0 and listingCE.corbeille=0 and id_commande in (SELECT distinct idCmd from facturation where etatProd like '%2%') order by commande.idCE",()]
    
    listCE=lecture_BDD(req)
    nbClientAtion=[]
    nbClientRe=[]
    minDate=[]
    for i in range(len(listCE)):
        req=["SELECT count(*) from commande where idCE=? and etatCmd=1 and corbeille=0",(listCE[i]["idCE"],)]
        nbAtion=lecture_BDD(req)[0]["count(*)"]
        req=["SELECT count(*) from commande where idCE=? and etatCmd=2 and corbeille=0",(listCE[i]["idCE"],)]
        nbRe=lecture_BDD(req)[0]["count(*)"]
        req=["SELECT MIN(date) from commande where idCE=? and etatCmd<3 and etatCmd>0 and corbeille=0",(listCE[i]["idCE"],)]
        date=lecture_BDD(req)[0]["min(date)"]

        nbClientAtion.append(nbAtion)
        nbClientRe.append(nbRe)
        minDate.append(date)
    listeRef,listeAll=getListRef()
    dateLim=(datetime.today()-timedelta(days=15)).strftime('%Y-%m-%d')
    return render_template('livraison_selectCE.html',user=user,listCE=listCE,nbClientAtion=nbClientAtion,nbClientRe=nbClientRe,idCE=idCELivraison,minDate=minDate,ref=ref,listeRef=listeRef,listeAll=listeAll,dateLim=dateLim)
    


@app.route('/selectLivraison/<user>', methods=['GET', 'POST'])
def selectLivraison(user):
    checkUser()
    session['user']['idCELivraison']=int(getValeurFormulaire('idCE'))
    write_log(str(session['user']['id']),"/selectLivraison - Selection du CE n° "+str(session['user']['idCELivraison']))
    return visuLivraison(user)
    

@app.route('/visuLivraison/<user>',methods=['GET', 'POST'])
def visuLivraison(user):
    checkUser()
    idCELivraison=session['user']['idCELivraison']
    req=["SELECT * from commande join client on idclientCmd=idclient where idCE=? and etatCmd>0 and etatCmd<3 and commande.corbeille=0 and id_commande in (SELECT distinct idCmd from facturation where etatProd like '%2%')",(idCELivraison,)]
    Lcmd=lecture_BDD(req)
    req=["SELECT entreprise from listingCE where idCE=? and corbeille=0 LIMIT 1",(idCELivraison,)]
    try:
        nomCE=lecture_BDD(req)[0]["entreprise"]
    except:
        nomCE=""
        
    write_log(str(session['user']['id']),"/visuLivraison - Visualisation du CE n° "+str(idCELivraison))
    return render_template('livraison_general.html',user=user,idCE=idCELivraison,nomCE=nomCE,Lcmd=Lcmd)


@app.route('/livrer/<user>', methods=['GET', 'POST'])
def livrer(user):
    checkUser()
    idCE=getValeurFormulaire("idCE")
    LidCommande=getListeForm("check")
    if len(LidCommande)>0:
        date=datetime.today().strftime('%d/%m/%Y')
        req=["insert into livraison (dateLivraison,idCE,nbCmd) values(?,?,?)",(date,idCE,len(LidCommande))]
        ecriture_BDD(req)
    for idCmd in LidCommande:
        livrer_commande(idCmd,user)
        
        #Ne fonctionne pas totalement

        # req=["UPDATE commande set idlivraison=(SELECT max(idlivraison) from livraison),deliveredBy=? where id_commande=?",(user,idCmd)]
        # ecriture_BDD(req)
        # req=["SELECT etatProd,idProd from facturation where idCmd=?",(idCmd,)]
        # ligne=lecture_BDD(req)
        # for l in ligne:
        #     etatProd=l['etatProd'].split(";")

        #     for i in range(len(etatProd)):
        #         if etatProd[i]=="2":
        #             etatProd[i]="5"
            
        #     etatMin=int(min(etatProd))
        #     maxEtat=max(etatProd)
        #     stretatProd = ";".join(etatProd) 
        #     req=["UPDATE facturation set etatProd=?,etatMin=?,etatMax=? where idProd=?",(stretatProd,etatMin,maxEtat,l["idProd"])]
        #     ecriture_BDD(req)

        
        write_log(str(session['user']['id']),"/livrer - Livraison du CE n°"+str(idCE)+" sur "+str(len(LidCommande))+" commandes")
    return choixCELivre(user)
    

@app.route('/histLivraison/<user>',methods=['GET', 'POST'])
def histLivraison(user): 
    checkUser()
    req=["SELECT * from livraison order by dateLivraison desc LIMIT 30",()]
    listLivraison=lecture_BDD(req)
    write_log(str(session['user']['id']),"/histLivraison - Visualisation de l'histotirque de livraison")
    return render_template('livraison_hist.html',user=user,listLivraison=listLivraison)
#endregion    

####################### Monde des CE - OngletCE #########################################
#region
@app.route('/ajoutCE/<user>', methods=['GET', 'POST'])
def ajoutCE(user):
    checkUser()
    req=["SELECT max(idCE) FROM listingCE WHERE idCE<900900 and corbeille=0",()]
    idCE=int(lecture_BDD(req)[0]['max(idCE)'])+1
    if idCE==900900:
        req=["SELECT max(idCE) FROM listingCE WHERE idCE<999000 and corbeille=0",()]
        idCE=int(lecture_BDD(req)[0]['max(idCE)'])+1
    CE={"prenom":"","idCE":idCE,"entreprise":"","intermediaire":"","mail":"","tel":"","mailCl":"0","mailInterPrep":"0","mailInterFact":"0","mailInterRelFact":"0","mailInterRel":"0","mailInterRupt":"0","qteFact":"1","sac":"Papier","retraitMag":"NON","colisIndiv":"NON","colisCol":"NON","colisExpe":"Aucun","catalogue":"1","promotion":"1","commentaires":"","adresse":""}
    req=["SELECT listingCE.id,utilisateur.prenom,idCE,entreprise,intermediaire,listingCE.mail,tel,mailCl,mailInterPrep,mailInterFact,mailInterRelFact,mailInterRel,mailInterRupt,qteFact,sac,retraitMag,colisIndiv,colisCol,colisExpe,catalogue,promotion,commentaires,adresse from listingCE  JOIN utilisateur ON listingCE.referente=utilisateur.id where corbeille=0",()]
    LCE=lecture_BDD(req)
    listeRef,listeAll=getListRef()
    return render_template('CE_ajout.html',CE=CE,user=user,LCE=LCE,listeRef=listeRef,listeAll=listeAll)

@app.route('/addCE', methods=['GET', 'POST'])
def addCE():
    checkUser()
    idCE=getValeurFormulaire("idCE")
    entreprise=getValeurFormulaire("entreprise")
    referente=getValeurFormulaire("referente")
    intermediaire=getValeurFormulaire("intermediaire")
    mail=getValeurFormulaire("mail").lower()
    tel=getValeurFormulaire("tel")
    mailCl=getValeurFormulaire("mailCl")
    mailInterPrep=getValeurFormulaire("mailInterPrep")
    mailInterFact=getValeurFormulaire("mailInterFact")
    mailInterRelFact=getValeurFormulaire("mailInterRelFact")
    mailInterRel=getValeurFormulaire("mailInterRel")
    mailInterRupt=getValeurFormulaire("mailInterRupt")
    mcl=0
    minterPrep=0
    minterFact=0
    minterRelFact=0
    minterRel=0
    minterRupt=0
    if mailCl=="true":
        mcl=1
    if mailInterPrep=="true":
        minterPrep=1
    if mailInterFact=="true":
        minterFact=1
    if mailInterRelFact=="true":
        minterRelFact=1
    if mailInterRel=="true":
        minterRel=1    
    if mailInterRupt=="true":
        minterRupt=1 
    qteFact=getValeurFormulaire("qteFact")
    sac=getValeurFormulaire("sac")
    retraitMag=getValeurFormulaire("retraitMag")
    colisIndiv=getValeurFormulaire("colisIndiv")
    colisCol=getValeurFormulaire("colisCol")
    colisExpe=getValeurFormulaire("colisExpe")
    catalogue=getValeurFormulaire("catalogue")
    promotion=getValeurFormulaire("promotion")
    commentaires=getValeurFormulaire("commentaires")
    adresse=getValeurFormulaire("adresse")
    CE={"prenom":"","idCE":idCE,"entreprise":"","intermediaire":"","mail":"","tel":"","mailCl":"0","mailInterPrep":"0","mailInterFact":"0","mailInterRelFact":"0","mailInterRel":"0","mailInterRupt":"0","qteFact":"1","sac":"Papier","retraitMag":"NON","colisIndiv":"NON","colisCol":"NON","colisExpe":"Aucun","catalogue":"1","promotion":"1","commentaires":"","adresse":""}
    req=["SELECT listingCE.id,utilisateur.prenom,idCE,entreprise,intermediaire,listingCE.mail,tel,mailCl,mailInterPrep,mailInterFact,mailInterRelFact,mailInterRel,mailInterRupt,qteFact,sac,retraitMag,colisIndiv,colisCol,colisExpe,catalogue,promotion,commentaires,adresse from listingCE  JOIN utilisateur ON listingCE.referente=utilisateur.id where corbeille=0",()]
    LCE=lecture_BDD(req)
    listeRef,listeAll=getListRef()

    req=["INSERT INTO listingCE (referente,idCE,entreprise,intermediaire,mail,tel,corbeille,mailCl,mailInterPrep,mailInterFact,mailInterRelFact,mailInterRel,mailInterRupt,qteFact,sac,retraitMag,colisIndiv,colisCol,colisExpe,catalogue,promotion,commentaires,adresse) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(referente,idCE,entreprise,intermediaire,mail,tel,0,mcl,minterPrep,minterFact,minterRelFact,minterRel,minterRupt,qteFact,sac,retraitMag,colisIndiv,colisCol,colisExpe,catalogue,promotion,commentaires,adresse)]
    ecriture_BDD(req)
    write_log(str(session['user']['id']),"/addCE - Ajout du CE n° "+str(idCE))
    return '',204

@app.route('/rechercheCE/<user>',methods=['GET', 'POST'])
def rechercheCE(user):
    checkUser()
    CEselectionne=getValeurFormulaire("CEselectionne")
    if CEselectionne=="" or CEselectionne is None:
        idCEselec=""
    else:
        idCEselec=int(CEselectionne.split(" - ")[0])
        
    write_log(str(session['user']['id']),"/rechercheCE - Filtre du CE n° "+str(idCEselec))
    req=["SELECT listingCE.id,utilisateur.prenom,idCE,entreprise,intermediaire,listingCE.mail,tel,mailCl,mailInterPrep,mailInterFact,mailInterRelFact,mailInterRel,mailInterRupt,qteFact,sac,retraitMag,colisIndiv,colisCol,colisExpe,catalogue,promotion,commentaires,adresse from listingCE  JOIN utilisateur ON listingCE.referente=utilisateur.id where corbeille=0",()]
    LCE=lecture_BDD(req)
    listeRef,listeAll=getListRef()
    if idCEselec is None or idCEselec=="":
        if session['user']['rechercheCE']=='-1':
            req=["SELECT listingCE.id,utilisateur.prenom,idCE,entreprise,intermediaire,listingCE.mail,tel,mailCl,mailInterPrep,mailInterFact,mailInterRelFact,mailInterRel,mailInterRupt,qteFact,sac,retraitMag,colisIndiv,colisCol,colisExpe,catalogue,promotion,commentaires,adresse from listingCE  JOIN utilisateur ON listingCE.referente=utilisateur.id where corbeille=0",()]
            CE=lecture_BDD(req)[0]
        else:
            try:
                req=["SELECT listingCE.id,utilisateur.prenom,idCE,entreprise,intermediaire,listingCE.mail,tel,mailCl,mailInterPrep,mailInterFact,mailInterRelFact,mailInterRel,mailInterRupt,qteFact,sac,retraitMag,colisIndiv,colisCol,colisExpe,catalogue,promotion,commentaires,adresse from listingCE  JOIN utilisateur ON listingCE.referente=utilisateur.id where corbeille=0 AND idCE=?",(session['user']['rechercheCE'],)]
                CE=lecture_BDD(req)[0]
            except:
                req=["SELECT listingCE.id,utilisateur.prenom,idCE,entreprise,intermediaire,listingCE.mail,tel,mailCl,mailInterPrep,mailInterFact,mailInterRelFact,mailInterRel,mailInterRupt,qteFact,sac,retraitMag,colisIndiv,colisCol,colisExpe,catalogue,promotion,commentaires,adresse from listingCE  JOIN utilisateur ON listingCE.referente=utilisateur.id where corbeille=0",()]
                CE=lecture_BDD(req)[0]

    else:
        session['user']['rechercheCE']=idCEselec
        req=["SELECT listingCE.id,utilisateur.prenom,idCE,entreprise,intermediaire,listingCE.mail,tel,mailCl,mailInterPrep,mailInterFact,mailInterRelFact,mailInterRel,mailInterRupt,qteFact,sac,retraitMag,colisIndiv,colisCol,colisExpe,catalogue,promotion,commentaires,adresse from listingCE  JOIN utilisateur ON listingCE.referente=utilisateur.id where corbeille=0 AND idCE=?",(idCEselec,)]
        CE=lecture_BDD(req)[0]
    return render_template('CE_recherche.html',CE=CE,user=user,LCE=LCE,CEselectionne=CEselectionne,listeRef=listeRef,listeAll=listeAll)

@app.route('/searchCE', methods=['GET', 'POST'])
def searchCE():
    checkUser()
    CEselectionne=getValeurFormulaire("CEselectionne")
    try:
        CE=CEselectionne.split(" - ")[0]
        req=["SELECT listingCE.id,referente,idCE,entreprise,intermediaire,listingCE.mail,tel,mailCl,mailInterPrep,mailInterFact,mailInterRelFact,mailInterRel,mailInterRupt,qteFact,sac,retraitMag,colisIndiv,colisCol,colisExpe,catalogue,promotion,commentaires,adresse from listingCE  JOIN utilisateur ON listingCE.referente=utilisateur.id where corbeille=0 AND idCE=?",(CE,)]
        L=lecture_BDD(req)[0]
        Linfo=[L["idCE"],L["entreprise"],L["referente"],L["intermediaire"],L["mail"],L["tel"],L["mailCl"],L["mailInterPrep"],L["mailInterFact"],L["mailInterRelFact"],L["mailInterRel"],L["mailInterRupt"],L["qteFact"],L["sac"],L["retraitMag"],L["colisIndiv"],L["colisCol"],L["colisExpe"],L["catalogue"],L["promotion"],L["commentaires"],L["adresse"],L["id"]]
        taille=len(Linfo)
        session['user']['rechercheCE']=CE
    except :
        taille=0
        Linfo=[]
        
    write_log(str(session['user']['id']),"/searchCE - Filtre du CE n° "+str(CE))
    return jsonify(Linfo=Linfo,taille=taille,CEselectionne=CEselectionne)

@app.route('/modifrechercheCE', methods=['GET', 'POST'])
def modifrechercheCE():
    checkUser()
    ide=getValeurFormulaire("ide")
    idCE=getValeurFormulaire("idCE")
    entreprise=getValeurFormulaire("entreprise")
    referente=getValeurFormulaire("referente")
    intermediaire=getValeurFormulaire("intermediaire")
    mail=getValeurFormulaire("mail")
    tel=getValeurFormulaire("tel")
    mailCl=getValeurFormulaire("mailCl")
    mailInterPrep=getValeurFormulaire("mailInterPrep")
    mailInterFact=getValeurFormulaire("mailInterFact")
    mailInterRelFact=getValeurFormulaire("mailInterRelFact")
    mailInterRel=getValeurFormulaire("mailInterRel")
    mailInterRupt=getValeurFormulaire("mailInterRupt")
    mcl=0
    minterPrep=0
    minterFact=0
    minterRelFact=0
    minterRel=0
    minterRupt=0
    if mailCl=="true":
        mcl=1
    if mailInterPrep=="true":
        minterPrep=1
    if mailInterFact=="true":
        minterFact=1
    if mailInterRelFact=="true":
        minterRelFact=1
    if mailInterRel=="true":
        minterRel=1    
    if mailInterRupt=="true":
        minterRupt=1 
    qteFact=getValeurFormulaire("qteFact")
    sac=getValeurFormulaire("sac")
    retraitMag=getValeurFormulaire("retraitMag")
    colisIndiv=getValeurFormulaire("colisIndiv")
    colisCol=getValeurFormulaire("colisCol")
    colisExpe=getValeurFormulaire("colisExpe")
    catalogue=getValeurFormulaire("catalogue")
    promotion=getValeurFormulaire("promotion")
    commentaires=getValeurFormulaire("commentaires")
    adresse=getValeurFormulaire("adresse")
    
    write_log(str(session['user']['id']),"/modifRechercheCE - Modification du CE n° "+str(ide))
    req=["UPDATE listingCE SET idCE=?,entreprise=?,referente=?,intermediaire=?,mail=?,tel=?,mailCl=?,mailInterPrep=?,mailInterFact=?,mailInterRelFact=?,mailInterRel=?,mailInterRupt=?,qteFact=?,sac=?,retraitMag=?,colisIndiv=?,colisCol=?,colisExpe=?,catalogue=?,promotion=?,commentaires=?,adresse=? where id=?",(idCE,entreprise,referente,intermediaire,mail,tel,mcl,minterPrep,minterFact,minterRelFact,minterRel,minterRupt,qteFact,sac,retraitMag,colisIndiv,colisCol,colisExpe,catalogue,promotion,commentaires,adresse,ide)]
    ecriture_BDD(req)
    return '',204

@app.route('/CE/<user>',methods=['GET', 'POST'])
def pageCE(user):
    checkUser()
    ref=getValeurFormulaire("ref")
    if ref!=None:
        write_log(str(session['user']['id']),"/CE - Filtre sur la référente "+str(ref))
        req=["SELECT listingCE.id,utilisateur.prenom,idCE,entreprise,intermediaire,listingCE.mail,tel,mailCl,mailInterPrep,mailInterFact,mailInterRelFact,mailInterRel,mailInterRupt from listingCE  JOIN utilisateur ON listingCE.referente=utilisateur.id where corbeille=0 and listingCE.referente=? order by idCE",(ref,)]
        ref=int(ref)
    else:
        write_log(str(session['user']['id']),"/CE - Filtre sur toutes les référentes")
        req=["SELECT listingCE.id,utilisateur.prenom,idCE,entreprise,intermediaire,listingCE.mail,tel,mailCl,mailInterPrep,mailInterFact,mailInterRelFact,mailInterRel,mailInterRupt from listingCE  JOIN utilisateur ON listingCE.referente=utilisateur.id where corbeille=0 order by idCE",()]

    LCE=lecture_BDD(req)
    listeRef,listeAll=getListRef()
    return render_template('CE_general.html',LCE=LCE,user=user,ref=ref,listeRef=listeRef,listeAll=listeAll)
    

@app.route('/modifCE', methods=['GET', 'POST'])
def modifCE():
    checkUser()
    ide=getValeurFormulaire("id")
    nouvIdCE=getValeurFormulaire("nouvidCE")
    entreprise=getValeurFormulaire("entreprise")
    ref=getValeurFormulaire("ref")
    inter=getValeurFormulaire("inter")
    mail=getValeurFormulaire("mail").lower()
    tel=getValeurFormulaire("tel")
    mailCl=getValeurFormulaire("mailCl")
    mailInterPrep=getValeurFormulaire("mailInterPrep")
    mailInterFact=getValeurFormulaire("mailInterFact")
    mailInterRelFact=getValeurFormulaire("mailInterRelFact")
    mailInterRel=getValeurFormulaire("mailInterRel")
    mailInterRupt=getValeurFormulaire("mailInterRupt")
    mcl=0
    minterPrep=0
    minterFact=0
    minterRelFact=0
    minterRel=0
    minterRupt=0
    if mailCl=="true":
        mcl=1
    if mailInterPrep=="true":
        minterPrep=1
    if mailInterFact=="true":
        minterFact=1
    if mailInterRelFact=="true":
        minterRelFact=1
    if mailInterRel=="true":
        minterRel=1    
    if mailInterRupt=="true":
        minterRupt=1 
    req=["UPDATE listingCE SET idCE=?,entreprise=?,referente=?,intermediaire=?,mail=?,tel=?,mailCl=?,mailInterPrep=?,mailInterFact=?,mailInterRelFact=?,mailInterRel=?,mailInterRupt=? where id=?",(nouvIdCE,entreprise,ref,inter,mail,tel,mcl,minterPrep,minterFact,minterRelFact,minterRel,minterRupt,ide)]
    ecriture_BDD(req)
    write_log(str(session['user']['id']),"/modifCE - Modification du CE n°"+str(nouvIdCE))
    return '',204
    

@app.route('/modifCEInfo', methods=['GET', 'POST'])
def modifCEInfo():
    checkUser()
    ide=getValeurFormulaire("id")
    qteFact=getValeurFormulaire("qteFact")
    sac=getValeurFormulaire("sac")
    retraitMag=getValeurFormulaire("retraitMag")
    colisIndiv=getValeurFormulaire("colisIndiv")
    colisCol=getValeurFormulaire("colisCol")
    colisExpe=getValeurFormulaire("colisExpe")
    catalogue=getValeurFormulaire("catalogue")
    promotion=getValeurFormulaire("promotion")
    commentaires=getValeurFormulaire("commentaires")
    req=["UPDATE listingCE SET qteFact=?,sac=?,retraitMag=?,colisIndiv=?,colisCol=?,colisExpe=?,catalogue=?,promotion=?,commentaires=? WHERE id=?",(qteFact,sac,retraitMag,colisIndiv,colisCol,colisExpe,catalogue,promotion,commentaires,ide)]
    ecriture_BDD(req)
    write_log(str(session['user']['id']),"/modifCEInfo - Modification ligne C n°"+str(ide))
    return '',204

@app.route('/modifCEAdresse', methods=['GET', 'POST'])
def modifCEAdresse():
    checkUser()
    ide=getValeurFormulaire("id")
    adresse=getValeurFormulaire("adresse")
    req=["UPDATE listingCE SET adresse=? WHERE id=?",(adresse,ide)]
    ecriture_BDD(req)
    write_log(str(session['user']['id']),"/modifCEAdresse - Modification ligne C n°"+str(ide))
    return '',204

@app.route('/suprCE', methods=['GET', 'POST'])
def suprCE():
    checkUser()
    ide=getValeurFormulaire("id")
    req=["UPDATE listingCE set corbeille=1 where id=?",(ide,)]
    ecriture_BDD(req)
    write_log(str(session['user']['id']),"suprCE - Suppression ligne C n°"+str(ide))
    return jsonify()

@app.route('/infoCE/<user>',methods=['GET', 'POST'])
def pageCEinfo(user): 
    checkUser()
    ref=getValeurFormulaire("ref")
    if ref==None or ref==0 or ref=='0':
        write_log(str(session['user']['id']),"/infoCE - Filtre sur la référente "+str(ref))
        req=["SELECT listingCE.id,utilisateur.prenom,idCE,entreprise,qteFact,sac,retraitMag,colisIndiv,colisCol,colisExpe,catalogue,promotion,commentaires from listingCE  JOIN utilisateur ON listingCE.referente=utilisateur.id where corbeille=0 order by idCE",()]
    else:
        write_log(str(session['user']['id']),"/infoCE - Filtre sur toutes les référentes")
        req=["SELECT listingCE.id,utilisateur.prenom,idCE,entreprise,qteFact,sac,retraitMag,colisIndiv,colisCol,colisExpe,catalogue,promotion,commentaires from listingCE  JOIN utilisateur ON listingCE.referente=utilisateur.id where corbeille=0 and listingCE.referente=? order by idCE",(ref,)]
        ref=int(ref)
    LCE=lecture_BDD(req)
    listeRef,listeAll=getListRef()
    return render_template('CE_infos.html',LCE=LCE,user=user,ref=ref,listeRef=listeRef,listeAll=listeAll)

@app.route('/adresseCE/<user>',methods=['GET', 'POST'])
def pageCEadresse(user): 
    checkUser()
    ref=getValeurFormulaire("ref")
    if ref==0 or ref==None or ref=='0':
        write_log(str(session['user']['id']),"/adresseCE - Filtre sur la référente "+str(ref))
        req=["SELECT listingCE.id,utilisateur.prenom,idCE,entreprise,adresse from listingCE  JOIN utilisateur ON listingCE.referente=utilisateur.id where corbeille=0 order by idCE",()]
        
    else:
        write_log(str(session['user']['id']),"/adresseCE - Filtre sur toutes les référentes")
        req=["SELECT listingCE.id,utilisateur.prenom,idCE,entreprise,adresse from listingCE  JOIN utilisateur ON listingCE.referente=utilisateur.id where corbeille=0 and listingCE.referente=? order by idCE",(ref,)]
        ref=int(ref)
    LCE=lecture_BDD(req)
    listeRef,listeAll=getListRef()
    return render_template('CE_adresses.html',LCE=LCE,user=user,ref=ref,listeRef=listeRef,listeAll=listeAll)
#endregion

####################### Dark World ######################################################
#region
@app.route('/connexion',methods=['GET', 'POST'])
def connexion():
    checkUser()
    write_log(str(session['user']['id']),"/connexion - Connexion")
    return render_template("dw_connexion.html")
    
@app.route('/utilisateurs',methods=['GET', 'POST'])
def utilisateurs():
    checkUser()
    req=["SELECT * FROM utilisateur WHERE etat='ACTIF' ORDER BY id",()]
    utilisateur=lecture_BDD(req)
    write_log(str(session['user']['id']),"/utilisateurs - Visualisation")
    return render_template("dw_utilisateurs.html",utilisateur=utilisateur)

@app.route('/ajoutUtilisateur',methods=['GET', 'POST'])
def ajoutUtilisateur():
    checkUser()
    req=["SELECT max(id) FROM utilisateur",()]
    id=lecture_BDD(req)[0]['max(id)']
    idUser=id+1
    nom="Nom - "+str(idUser)
    prenom="Prenom - "+str(idUser)
    mail="prenom"+str(idUser)+"@parfumeriempb.fr"
    mail=mail.lower()
    mdp=""
    niveau="NORMAL"
    etat='ACTIF'
    req=["INSERT INTO utilisateur (id,nom,prenom,mail,mdp,niveau,etat) VALUES(?,?,?,?,?,?,?)",(idUser,nom,prenom,mail,mdp,niveau,etat)]
    ecriture_BDD(req)
    write_log(str(session['user']['id']),"/ajoutUtilisateur - Ajout utilisateur id n°"+str(id))
    return utilisateurs()
    

@app.route('/supprUtilisateur',methods=['GET', 'POST'])
def supprUtilisateur():
    checkUser()
    id=getValeurFormulaire("id")
    req=["SELECT niveau FROM utilisateur WHERE id=?",(id,)]
    niveau=lecture_BDD(req)[0]['niveau']
    if niveau=="ADMIN":
        message="Impossible de supprimer un ADMINISTRATEUR"
    elif niveau=="REF":
        req=["SELECT referente FROM listingCE WHERE referente=?",(id,)]
        liste=lecture_BDD(req)
        if len(liste)==0:
            req=["UPDATE utilisateur SET etat='INACTIF' WHERE id=?",(id,)]
            ecriture_BDD(req)
            message="Changement(s) pris en compte"
            write_log(str(session['user']['id']),"/supprUtilisateur - Désactivation utilisateur id n°"+str(id))
        else:
            message="Veuillez attribuer les CE du référent n°"+id+" a d'autres référents avant de le supprimer"
        
    else:
        req=["UPDATE utilisateur SET etat='INACTIF' WHERE id=?",(id,)]
        ecriture_BDD(req)
        message="Changement(s) pris en compte"
        write_log(str(session['user']['id']),"/supputilisateur - Desactiviation utilisateur id n°"+str(id))
    return jsonify(message=message)


@app.route('/modifUtilisateur',methods=['GET', 'POST'])
def modifUtilisateur():
    checkUser()
    id=getValeurFormulaire("id")
    nom=getValeurFormulaire("nom")
    prenom=getValeurFormulaire("prenom")
    mail=getValeurFormulaire("mail").lower()
    niveau=getValeurFormulaire("niveau")
    req=["SELECT niveau FROM utilisateur WHERE id=?",(id,)]
    niveauAv=lecture_BDD(req)[0]['niveau']
    req=["UPDATE utilisateur SET nom=?,prenom=?,mail=?,niveau=?  WHERE id=?",(nom,prenom,mail,niveau,id)]
    ecriture_BDD(req)
    write_log(str(session['user']['id']),"/modifUtilisateur - Modification utilisateur id n°"+str(id))

    return '',204
    
@app.route('/initMDP',methods=['GET', 'POST'])
def initMDP():
    checkUser()
    id=getValeurFormulaire("idMDP")
    req=["SELECT id,nom,prenom,mail FROM utilisateur WHERE id=?",(id,)]
    user=lecture_BDD(req)[0]
    write_log(str(session['user']['id']),"/initMDP - Modification mdp utilisateur id n°"+str(id))
    return render_template("dw_utilisateurs_mdp.html",id=id,user=user)

@app.route('/validerMDP',methods=['GET', 'POST'])
def validerMDP():
    checkUser()
    id=getValeurFormulaire("idMDP")
    # MDP CRYPTER
    # mdp=getValeurFormulaire("mdp").encode()
    # mdpC=crypter(mdp)
    mdpC=getValeurFormulaire("mdp")
    req=["UPDATE utilisateur SET mdp=? WHERE id=?",(mdpC,id)]
    ecriture_BDD(req)
    write_log(str(session['user']['id']),"validMDP - Validation mdp utilisateur id n°"+str(id))
    return render_template("dw_utilisateurs_mdp_succes.html")

@app.route('/confirmerMDP',methods=['GET', 'POST'])
def confirmerMDP():
    checkUser()
    write_log(str(session['user']['id']),"/confirmerMDP - Confirmation modification mdp utilisateur id n°"+str(id))
    return render_template("dw_utilisateurs_mdp_succes.html")

@app.route('/postes',methods=['GET', 'POST'])
def postes():
    checkUser()
    req=["SELECT * FROM postes",()]
    Lpc=lecture_BDD(req)
    write_log(str(session['user']['id']),"/postes - Visualisation")
    return render_template("dw_utilisateurs_postes.html",Lpc=Lpc)

@app.route('/ajoutPoste',methods=['GET', 'POST'])
def ajoutPoste():
    checkUser()
    req=["SELECT max(id) FROM postes",()]
    id=lecture_BDD(req)[0]['max(id)']
    idPoste=id+1
    numPC="408-"+str(idPoste)
    dossierExtract="C:/exemple/pc/test/ - "+str(idPoste)
    dossierErreur="C:/exemple/pc/test/ - "+str(idPoste)
    req=["INSERT INTO postes VALUES(?,?,?,?)",(idPoste,numPC,dossierExtract,dossierErreur)]
    ecriture_BDD(req)
    write_log(str(session['user']['id']),"/ajoutPoste - Ajout poste numPC n°"+str(numPC))
    return postes()
    

@app.route('/supprPoste',methods=['GET', 'POST'])
def supprPoste():
    checkUser()
    id=getValeurFormulaire("id")
    req=["DELETE FROM postes WHERE id=?",(id,)]
    ecriture_BDD(req)
    message="Changement(s) pris en compte"
    write_log(str(session['user']['id']),"/supprPoste - Suppression du poste numPC n°"+str(id))
    return jsonify(message=message)


@app.route('/modifPoste',methods=['GET', 'POST'])
def modifPoste():
    checkUser()
    id=getValeurFormulaire("id")
    numPC=getValeurFormulaire("numPC")
    dossierExtract=str(getValeurFormulaire("dossierExtract"))
    dossierErreur=str(getValeurFormulaire("dossierErreur"))
    req=["UPDATE postes SET numPC=?,dossierExtract=?,dossierErreur=? WHERE id=?",(numPC,dossierExtract,dossierErreur,id)]
    ecriture_BDD(req)
    write_log(str(session['user']['id']),"/modidPoste - Modification poste numPC °"+str(numPC))
    return '',204

@app.route('/corbeille')
def corbeille():
    checkUser()
    req=["SELECT id_commande,client,societe,total from commande join client on idClient=idClientCmd where commande.corbeille=1 and idExtractionCmd is null",()]
    Lmanu=lecture_BDD(req)
    req=["SELECT distinct idExtraction,commande.date,createur from extractions join commande on idExtraction=idExtractionCmd where corbeille=1",()]
    Lextract=lecture_BDD(req)
    Lcmd=[]
    for extract in Lextract:
        req=["SELECT id_commande,client,societe,total from commande join client on idClient=idClientCmd where commande.corbeille=1 and commande.idExtractionCmd=?",(extract["idExtraction"],)]
        l=lecture_BDD(req)
        Lcmd.append(l)
    write_log(str(session['user']['id']),"/corbeille - Visualisation")
    return render_template("dw_corb_cde.html",Lcmd=Lcmd,Lextract=Lextract,Lmanu=Lmanu)
    

@app.route('/actionCorb',methods=['GET', 'POST'])
def actionCorb():
    checkUser()
    action=getValeurFormulaire("action")
    LidCmd=getListeForm("check")
    if action=="0":
        for idCmd in LidCmd:
            for image in os.listdir(repertoireImgClient) :
                if image.startswith(idCmd+"_"):
                    os.remove(repertoireImgClient+"/"+image)

            req=["SELECT idProd from facturation where idCmd=? and idHW<>-1",(idCmd,)]
            listIdHW=lecture_BDD(req)
            for idHW in listIdHW:
                for image in os.listdir(repertoireImgCmd) :
                    if image.startswith(str(idHW['idProd'])+"_"):
                        os.remove(repertoireImgCmd+"/"+image)
            req=["delete from commande where id_commande=?",(idCmd,)]
            ecriture_BDD(req)
            req=["delete from facturation where idCmd=?",(idCmd,)]
            ecriture_BDD(req)
        
        req=["delete from extractions where idExtraction not in (SELECT idExtractionCmd from commande where corbeille=0)",()]
        ecriture_BDD(req)
        write_log(str(session['user']['id']),"/actionCorb - Suppression des commandes")

    else:
        for cmd in LidCmd:
            req=["UPDATE commande set corbeille=0,deletedBy='' where id_commande=?",(cmd,)]
            ecriture_BDD(req)
        write_log(str(session['user']['id']),"/actionCorb - Ajout de la commande dans le monde normal")


    return corbeille()
    

@app.route('/corbCE')
def corbCE():
    checkUser()
    req=["SELECT id,idCE,entreprise,intermediaire from listingCE where corbeille=1",()]
    write_log(str(session['user']['id']),"/corbCE - Visualisation")
    Lce=lecture_BDD(req)
    return render_template("dw_corb_CE.html",Lce=Lce)
    

@app.route('/actionCorbCE',methods=['GET', 'POST'])
def actionCorbCE():
    checkUser()
    action=getValeurFormulaire("action")
    LidCE=getListeForm("check")
    if action=="0":
        for idCE in LidCE:
            req=["DELETE from listingCE where id=? and corbeille=1",(idCE,)]
            ecriture_BDD(req)
            write_log(str(session['user']['id']),"/actionCorbCE - Suppression du CE n°"+str(idCE))


    else:
        for idCE in LidCE:
            req=["UPDATE listingCE set corbeille=0 where id=?",(idCE,)]
            ecriture_BDD(req)
        write_log(str(session['user']['id']),"/actionCorbCE - Ajout dans le monde normal du CE n°"+str(idCE))

    return corbCE()

################EXPORT DE DONNEES######################

@app.route('/export_de_donnees',methods=['GET', 'POST'])
def export_de_donnees():
    checkUser()
    write_log(str(session['user']['id']),"/export_de_donnees - Visualisation")
    return render_template("dw_export_de_donnees.html")


@app.route('/action_export_de_donnees',methods=['GET', 'POST'])
def action_export_de_donnees():
    checkUser()
    action=getValeurFormulaire("action")
    if action!=None:
        dateMin=getValeurFormulaire("dateMin")
        dateMax=getValeurFormulaire("dateMax")
        if dateMax==None:
            dateMax=str(datetime.today().strptime('%Y-%m-%d'))
        if dateMin==None:  
            dateMin=str(datetime.date(2021,1,1).strptime('%Y-%m-%d'))
        maxD=dateMax
        minD=dateMin
    if action=="0" or action=="99":
        #suppression doublons
        req=["SELECT idclient,mail,client FROM client GROUP BY mail,client HAVING COUNT(*) > 1",()]
        Lmail=lecture_BDD(req)
        for mail in Lmail:
            if mail['mail']!='' or len(mail["mail"])>1:
                req=["SELECT id_commande from commande where idclientCmd in (SELECT idclient from client where mail=? and client=?)",(mail["mail"],mail["client"])]
                LidCmd=lecture_BDD(req)
                for idCmd in LidCmd:
                    req=["UPDATE commande set idclientCmd=? where id_commande=?",(mail["idclient"],idCmd["id_commande"])]
                    ecriture_BDD(req)
                req=["delete from client where idclient<>? and mail=? and client=?",(mail["idclient"],mail["mail"],mail["client"])]
                ecriture_BDD(req)
        write_log(str(session['user']['id']),"/action_export_de_donnees - Suppression des doublons")

    if action=="1" or action=="99":
        #Export des mails
        export_Mail_Clients()
        write_log(str(session['user']['id']),"/action_export_de_donnees - Exportation des mails clients")
    if action=="2" or action=="99":
        #Export des infos CE
        export_Infos_CE()
        write_log(str(session['user']['id']),"/action_export_de_donnees - Exportation des infos CE")
    if action=="3" or action=="99":
        #Export des commandes
        export_Commandes(maxD,minD)
        write_log(str(session['user']['id']),"/action_export_de_donnees - Exportation des commandes")
    if action=="4" or action=="99":
        #Export des paiements
        export_Paiements(maxD,minD)
        write_log(str(session['user']['id']),"/action_export_de_donnees - Exportation des paiements")
    if action=="5" or action=="99":
        #Export des impayés listing
        export_Impayes()
        write_log(str(session['user']['id']),"/action_export_de_donnees - Exportation des impayés")
    if action=="6" or action=="99":
        #Export des impayés par CE
        export_Impayes_Synthese_CE()
        write_log(str(session['user']['id']),"/action_export_de_donnees - Exportation des impayés par CE")
    if action=="7" or action=="99":
        #Export des impayés par référente
        export_Impayes_Synthese_Referente()
        write_log(str(session['user']['id']),"/action_export_de_donnees - Exportation des impayés par référente")
    if action=="8":
        extraction_auto()
        write_log(str(session['user']['id']),"/action_export_de_donnees - Exportation des impayés par référente")
    return '',204


################STAT######################
def deltaTime(date,dAnnee,dMois):
    liste=date.split('-')
    Nannee=int(liste[0])
    Nmois=int(liste[1])
    Njour=int(liste[2])
    if Nmois > dMois:
        Nmois-=dMois
    else:
        Nmois+=12-dMois
        Nannee-=1
    Nannee-=dAnnee
    newdate=datetime(Nannee, Nmois, Njour).strftime('%Y-%m-%d')
    return (newdate)

@app.route('/stat',methods=['GET', 'POST'])
def stat():
    checkUser()
    if session['user']['firstCo']=='-1':
        dateMin=deltaTime(datetime.today().strftime('%Y-%m-%d'),0,6)
        dateMax=datetime.today().strftime('%Y-%m-%d')
    else :
        #TODO ne se réactualise pas en fonction du choix de l'utilisateur
        dateMinForm=getValeurFormulaire("dateMin")
        dateMaxForm=getValeurFormulaire("dateMax")
        dateMin=session['user']['dwDateMin']
        dateMax=session['user']['dwDateMax']
        if dateMinForm!=dateMin:
            dateMin=dateMinForm
        if dateMaxForm!=dateMax:
            dateMax=dateMaxForm    
    session['user']['dwDateMin']=dateMin
    session['user']['dwDateMax']=dateMax
    if dateMax!="" and dateMax!=None:
        if dateMin!="" and dateMin!=None:
            phrase=" and date>='"+dateMin+"' and date<='"+dateMax+"'"
            
        else:
            phrase=" and date<='"+dateMax+"'"
            req=["SELECT min(date) from commande where corbeille=0",()]
            dateMin=lecture_BDD(req)[0]["min(date)"]
            
    elif dateMin!="" and dateMin!=None:
        phrase=" and date>='"+dateMin+"'"
        dateMax=datetime.today().strftime('%Y-%m-%d')
        
    else:
        phrase=""
        dateMax=datetime.today().strftime('%Y-%m-%d')
        req=["SELECT min(date) from commande where corbeille=0",()]
        dateMin=lecture_BDD(req)[0]["min(date)"]
        if dateMin==None:
            dateMin=dateMax
        
    req1=["SELECT count(id_commande) from commande where corbeille=0"+phrase,()]
    req2=["SELECT prix,etatProd from facturation join commande on idCmd=id_commande where etatCmd>0 and corbeille=0"+phrase,()]
    req3=["SELECT dateFact,date from commande where etatCmd>1 and corbeille=0"+phrase,()]
    req4=["SELECT distinct idCE from commande where corbeille=0 and etatCmd>0"+phrase,()]
    req5=["SELECT sum(qte),code,libW from facturation join commande on idCmd=id_commande where corbeille=0 and etatCmd>0"+phrase+" group by code order by sum(qte) desc",()]
    req6=["SELECT distinct code,libW from facturation join commande on idCmd=id_commande where corbeille=0 and etatCmd>0"+phrase,()]
    req7=["SELECT etatProd,prix from facturation join commande on idCmd=id_commande where corbeille=0 and etatCmd>0"+phrase,()]
    #nb de commande totales
    cmdTot=lecture_BDD(req1)[0]["count(id_commande)"]
    #calcul du CA
    l=lecture_BDD(req2)
    CA=0
    for prod in l:
        etat=prod["etatProd"]
        Letat=etat.split(";")
        for e in Letat:
            if int(e)==2 or int(e)==5:
                CA+=float(prod["prix"])
    CA=round(CA,2)
    #calcul temps moyen de traitement
    Ldate=lecture_BDD(req3)
    tpstot=timedelta(days=0)
    for d in Ldate:
        date=datetime.strptime(d["date"], '%Y-%m-%d')
        if d["dateFact"]!=None:
            dateFact=datetime.strptime(d["dateFact"], '%Y-%m-%d')
            tpstot+=dateFact-date 
    if len(Ldate)>0:
        tpstot=tpstot.days/len(Ldate)
        tpstot=round(tpstot,2)
    #meilleur CE
    CAmax=0
    idCEmax=0

    LCE=lecture_BDD(req4)
    for idCE in LCE:
        CACE=calculCACE(idCE["idCE"])
        if CACE>CAmax:
            CAmax=CACE
            idCEmax=idCE["idCE"]
    #calcul du meilleur produit en qte
    bestProd=lecture_BDD(req5)
    if len(bestProd)>0:
        bestP=bestProd[0]["libW"]
        nbProd=bestProd[0]["sum(qte)"]
    else:
        bestP="Aucun"
        nbProd=0
    #meilleur vente en €
    l=lecture_BDD(req6)
    CAProdmax=0
    libMax=0
    for prod in l:
        CAProd=calculCAProd(prod["code"])
        if CAProd>CAProdmax:
            CAProdmax=CAProd
            libMax=prod["libW"]
    #ruptures
    l=lecture_BDD(req7)
    coutRupt=0
    nbRupt=0
    for prod in l:
        etat=prod["etatProd"]
        Letat=etat.split(";")
        for e in Letat:
            if int(e)==3 :
                coutRupt+=float(prod["prix"])
                nbRupt+=1
    coutRupt=round(coutRupt,2)
    #boucle for datemin to dateMax
    maxD=datetime.strptime(dateMax, '%Y-%m-%d')
    minD=datetime.strptime(dateMin, '%Y-%m-%d')
    Ldate=[]
    for i in range((maxD - minD).days + 1):
        dateFormat=minD + timedelta(days=i)
        dateI=dateFormat.strftime('%Y-%m-%d')
        req=["SELECT count(id_commande) from commande where date<=? and (dateFact>? or dateFact isNull) and corbeille=0",(dateI,dateI)]
        nbCmd=int(lecture_BDD(req)[0]["count(id_commande)"])
        Ldate.append([dateI,nbCmd])
    jsondata=json.dumps({'Ldate':Ldate})
    write_log(str(session['user']['id']),"/stat - Visualisation")
    return render_template("dw_stat_general.html",CA=CA,cmdTot=cmdTot,tpstot=tpstot,bestP=bestP,nbProd=nbProd,idCEmax=idCEmax,CAmax=CAmax,CAProdMax=CAProdmax,libMax=libMax,coutRupt=coutRupt,nbRupt=nbRupt,dateMin=dateMin,dateMax=dateMax,jsondata=jsondata)


def calculCACE(idCE):
    checkUser()
    CA=0
    req=["SELECT prix,etatProd from facturation join commande on idCmd=id_commande where corbeille=0 and idCE=?",(idCE,)]
    l=lecture_BDD(req)
    for prod in l:
        etat=prod["etatProd"]
        Letat=etat.split(";")
        for e in Letat:
            if int(e)==2 or int(e)==5:
                CA+=float(prod["prix"])
    CA=round(CA,2)
    return CA
    

def calculCAProd(code):
    checkUser()
    CA=0
    req=["SELECT prix,etatProd from facturation join commande on idCmd=id_commande where corbeille=0 and code=?",(code,)]
    l=lecture_BDD(req)
    for prod in l:
        etat=prod["etatProd"]
        Letat=etat.split(";")
        for e in Letat:
            if int(e)==2 or int(e)==5:
                CA+=float(prod["prix"])
    CA=round(CA,2)
    return CA
    

@app.route('/export')
def export():
    checkUser()
    export_Extractor_Stat()
    write_log(str(session['user']['id']),"/export - Exportation des données")
    return '',204
    

##################### STAT CE ####################
@app.route('/statCE',methods=['GET', 'POST'])
def statCE():
    checkUser()
    if session['user']['firstCo']=='-1':
        dateMin=deltaTime(datetime.today().strftime('%Y-%m-%d'),0,6)
        dateMax=datetime.today().strftime('%Y-%m-%d')
    else :
        #TODO ne se réactualise pas en fonction du choix de l'utilisateur
        dateMinForm=getValeurFormulaire("dateMin")
        dateMaxForm=getValeurFormulaire("dateMax")
        dateMin=session['user']['dwDateMin']
        dateMax=session['user']['dwDateMax']
        if dateMinForm!=dateMin:
            dateMin=dateMinForm
        if dateMaxForm!=dateMax:
            dateMax=dateMaxForm    
    session['user']['dwDateMin']=dateMin
    session['user']['dwDateMax']=dateMax
    if dateMax!="" and dateMax!=None:
        if dateMin!="" and dateMin!=None:
            phrase=" and date>='"+dateMin+"' and date<='"+dateMax+"'"

        else:
            phrase=" and date<='"+dateMax+"'"
            req=["SELECT min(date) from commande where corbeille=0",()]
            dateMin=lecture_BDD(req)[0]["min(date)"]
        
    elif dateMin!="" and dateMin!=None:
        dateMax=datetime.today().strftime('%Y-%m-%d')
        phrase=" and date>='"+dateMin+"'"
        
    else:
        phrase=""
        dateMax=datetime.today().strftime('%Y-%m-%d')
        req=["SELECT min(date) from commande where corbeille=0",()]
        dateMin=lecture_BDD(req)[0]["min(date)"]

    req=["SELECT distinct idCE from commande where corbeille=0"+phrase+" order by idCE",()]
    LidCE=lecture_BDD(req)
    LnbCmd=[]
    LCACE=[]
    LbestProd=[]
    LbestSell=[]
    for idCE in LidCE:
        idce=idCE["idCE"]
        req=["SELECT count(distinct client) from client join commande on idClient=idclientCmd where corbeille=0 and idCE=?"+phrase,(idce,)]
        LnbCmd.append(lecture_BDD(req)[0]["count(distinct client)"])
        LCACE.append(calculCACE(idce))
        #calcul du meilleur produit en qte
        req=["SELECT sum(qte),code,libW from facturation join commande on idCmd=id_commande where corbeille=0 and idCE=?"+phrase+" group by code order by sum(qte) desc",(idce,)]
        bestProd=lecture_BDD(req)
        if len(bestProd)>0:
            bestP=bestProd[0]["libW"]
            nbProd=bestProd[0]["sum(qte)"]
        else:
            bestP="Aucun"
            nbProd=0
        LbestProd.append([bestP,nbProd])
        #meilleur vente en €
        req=["SELECT distinct code,libW from facturation join commande on idCmd=id_commande where corbeille=0 and idCE=?"+phrase,(idce,)]
        l=lecture_BDD(req)
        CAProdmax=0
        libMax=0
        for prod in l:
            CAProd=calculCAProd(prod["code"])
            if CAProd>CAProdmax:
                CAProdmax=CAProd
                libMax=prod["libW"]
        LbestSell.append([CAProdmax,libMax])
    write_log(str(session['user']['id']),"/statCE - Visualisation")
    return render_template("dw_stat_CE.html",dateMin=dateMin,dateMax=dateMax,LnbCmd=LnbCmd,LbestProd=LbestProd,LbestSell=LbestSell,LidCE=LidCE,LCACE=LCACE)

@app.route('/exportAdresseCE',methods=['GET', 'POST'])
def exportAdresseCE():
    checkUser()
    export_Infos_CE()
    write_log(str(session['user']['id']),"/exportAdresseCE - Exportation des données")
    
    return '',204


#Stat Ref
@app.route('/statRef',methods=['GET', 'POST'])
def statRef():
    checkUser()
    if session['user']['firstCo']=='-1':
        dateMin=deltaTime(datetime.today().strftime('%Y-%m-%d'),0,1)
        dateMax=datetime.today().strftime('%Y-%m-%d')
    else :
        #TODO ne se réactualise pas en fonction du choix de l'utilisateur
        dateMinForm=getValeurFormulaire("dateMin")
        dateMaxForm=getValeurFormulaire("dateMax")
        dateMin=session['user']['dwDateMin']
        dateMax=session['user']['dwDateMax']
        if dateMinForm!=dateMin:
            dateMin=dateMinForm
        if dateMaxForm!=dateMax:
            dateMax=dateMaxForm    
    session['user']['dwDateMin']=dateMin
    session['user']['dwDateMax']=dateMax
    if dateMax!="" and dateMax!=None:
        if dateMin!="" and dateMin!=None:
            phrase=" and date>='"+dateMin+"' and date<='"+dateMax+"'"
            
        else:
            phrase=" and date<='"+dateMax+"'"
            req=["SELECT min(date) from commande where corbeille=0",()]
            dateMin=lecture_BDD(req)[0]["min(date)"]
            
    elif dateMin!="" and dateMin!=None:
        phrase=" and date>='"+dateMin+"'"
        dateMax=datetime.today().strftime('%Y-%m-%d')
        
    else:
        phrase=""
        dateMax=datetime.today().strftime('%Y-%m-%d')
        req=["SELECT min(date) from commande where corbeille=0",()]
        dateMin=lecture_BDD(req)[0]["min(date)"]
        if dateMin==None:
            dateMin=dateMax
    req=["SELECT id,prenom FROM utilisateur WHERE niveau='REF'",()]
    Lref=lecture_BDD(req)
    #Lref=["2","3","1"]
    LtotRef=[]
    for ref in Lref:
        req1=["SELECT count(id_commande) from commande where corbeille=0 and idCE in (SELECT idCE from listingCE where referente=? and corbeille=0)"+phrase,(ref['id'],)]
        req2=["SELECT prix,etatProd from facturation join commande on idCmd=id_commande where etatCmd>0 and corbeille=0 and idCE in (SELECT idCE from listingCE where referente=? and corbeille=0)"+phrase,(ref['id'],)]
        req3=["SELECT dateFact,date from commande where etatCmd>1 and corbeille=0 and idCE in (SELECT idCE from listingCE where referente=? and corbeille=0)"+phrase,(ref['id'],)]
        
        #nb de commande totales
        cmdTot=lecture_BDD(req1)[0]["count(id_commande)"]
        #calcul du CA
        l=lecture_BDD(req2)
        CA=0
        for prod in l:
            etat=prod["etatProd"]
            Letat=etat.split(";")
            for e in Letat:
                if int(e)==2 or int(e)==5:
                    CA+=float(prod["prix"])
        CA=round(CA,2)
        #calcul temps moyen de traitement
        Ldate=lecture_BDD(req3)
        tpstot=timedelta(0)
        for d in Ldate:
            date=datetime.strptime(d["date"], '%Y-%m-%d')
            if d["dateFact"]!=None:
                dateFact=datetime.strptime(d["dateFact"], '%Y-%m-%d')
                tpstot+=dateFact-date 
        if len(Ldate)>0:
            tpstot=tpstot.days/len(Ldate)
        else:
            tpstot=tpstot.days
        #boucle for datemin to dateMax
        maxD=datetime.strptime(dateMax, '%Y-%m-%d')
        minD=datetime.strptime(dateMin, '%Y-%m-%d')
        Ldate=[]
        for i in range((maxD - minD).days + 1):
            dateFormat=minD + timedelta(days=i)
            dateI=dateFormat.strftime('%Y-%m-%d')
            req=["SELECT count(id_commande) from commande where date<=? and (dateFact>? or dateFact isNull) and corbeille=0 and idCE in (SELECT idCE from listingCE where referente=? and corbeille=0)",(dateI,dateI,ref['id'])]
            nbCmd=int(lecture_BDD(req)[0]["count(id_commande)"])
            Ldate.append([dateI,nbCmd])
        jsondata=json.dumps({'Ldate':Ldate}) 

        LtotRef.append([cmdTot,CA,tpstot,jsondata])
    write_log(str(session['user']['id']),"/statRef - Visualisation")  
    return render_template("dw_stat_ref.html",LtotRef=LtotRef,dateMin=dateMin,dateMax=dateMax,Lref=Lref)
    

#Stat User Commandes
@app.route('/statUser',methods=['GET', 'POST'])
def statUser():
    checkUser()
    if session['user']['firstCo']=='-1':
        dateMin=deltaTime(datetime.today().strftime('%Y-%m-%d'),0,1)
        dateMax=datetime.today().strftime('%Y-%m-%d')
    else :
        #TODO ne se réactualise pas en fonction du choix de l'utilisateur
        dateMinForm=getValeurFormulaire("dateMin")
        dateMaxForm=getValeurFormulaire("dateMax")
        dateMin=session['user']['dwDateMin']
        dateMax=session['user']['dwDateMax']
        if dateMinForm!=dateMin:
            dateMin=dateMinForm
        if dateMaxForm!=dateMax:
            dateMax=dateMaxForm    
    session['user']['dwDateMin']=dateMin
    session['user']['dwDateMax']=dateMax
    if dateMax!="" and dateMax!=None:
        if dateMin!="" and dateMin!=None:
            phrase=" and date>='"+dateMin+"' and date<='"+dateMax+"'"
            
        else:
            phrase=" and date<='"+dateMax+"'"
            req=["SELECT min(date) from stats",()]
            dateMin=lecture_BDD(req)[0]["min(date)"]
            
    elif dateMin!="" and dateMin!=None:
        phrase=" and date>='"+dateMin+"'"
        dateMax=datetime.today().strftime('%Y-%m-%d')
        
    else:
        phrase=""
        dateMax=datetime.today().strftime('%Y-%m-%d')
        req=["SELECT min(date) from stats",()]
        dateMin=lecture_BDD(req)[0]["min(date)"]
        if dateMin==None:
            dateMin=dateMax
    req=["SELECT DISTINCT(niveau) FROM utilisateur",()]
    Lcat=lecture_BDD(req)
    req=["SELECT id,prenom FROM utilisateur ORDER BY(prenom)" ,()]
    Lref=lecture_BDD(req)
    LtotRef=[]
    for ref in Lref:
        #boucle for datemin to dateMax
        maxD=datetime.strptime(dateMax, '%Y-%m-%d')
        minD=datetime.strptime(dateMin, '%Y-%m-%d')
        LdateExtraction=[]
        LdateAjout=[]
        LdatePreparation=[]
        LdateFacturation=[]
        for i in range((maxD - minD).days + 1):
            dateFormat=minD + timedelta(days=i)
            dateI=dateFormat.strftime('%Y-%m-%d')
            #extraction 
            action='extraire'
            req=["SELECT count(cde) from stats where date=? and idUser=? and action=?",(dateI,ref['id'],action)]
            nbCmd=int(lecture_BDD(req)[0]["count(cde)"])
            LdateExtraction.append([dateI,nbCmd])
            #creation
            action='ajouter'
            req=["SELECT count(cde) from stats where date=? and idUser=? and action=?",(dateI,ref['id'],action)]
            nbCmd=int(lecture_BDD(req)[0]["count(cde)"])
            LdateAjout.append([dateI,nbCmd])
            #preparation
            action='preparer'
            req=["SELECT count(cde) from stats where date=? and idUser=? and action=?",(dateI,ref['id'],action)]
            nbCmd=int(lecture_BDD(req)[0]["count(cde)"])
            LdatePreparation.append([dateI,nbCmd])
            #facturation
            action='facturer'
            req=["SELECT count(cde) from stats where date=? and idUser=? and action=?",(dateI,ref['id'],action)]
            nbCmd=int(lecture_BDD(req)[0]["count(cde)"])
            LdateFacturation.append([dateI,nbCmd])

        jsondataExtraction=json.dumps({'Ldate':LdateExtraction})    
        jsondataAjout=json.dumps({'Ldate':LdateAjout})    
        jsondataPreparation=json.dumps({'Ldate':LdatePreparation})    
        jsondataFacturation=json.dumps({'Ldate':LdateFacturation})    

        LtotRef.append([jsondataExtraction,jsondataAjout,jsondataPreparation,jsondataFacturation])
    write_log(str(session['user']['id']),"/statUser - Visualisation")    
    return render_template("dw_stat_user_cde.html",LtotRef=LtotRef,dateMin=dateMin,dateMax=dateMax,Lref=Lref,Lcat=Lcat)

###Stat User Produits
@app.route('/statUserPdt',methods=['GET', 'POST'])
def statUserPdt():
    checkUser()
    if session['user']['firstCo']=='-1':
        dateMin=deltaTime(datetime.today().strftime('%Y-%m-%d'),0,1)
        dateMax=datetime.today().strftime('%Y-%m-%d')
    else :
        #TODO ne se réactualise pas en fonction du choix de l'utilisateur
        dateMinForm=getValeurFormulaire("dateMin")
        dateMaxForm=getValeurFormulaire("dateMax")
        dateMin=session['user']['dwDateMin']
        dateMax=session['user']['dwDateMax']
        if dateMinForm!=dateMin:
            dateMin=dateMinForm
        if dateMaxForm!=dateMax:
            dateMax=dateMaxForm    
    session['user']['dwDateMin']=dateMin
    session['user']['dwDateMax']=dateMax
    if dateMax!="" and dateMax!=None:
        if dateMin!="" and dateMin!=None:
            phrase=" and date>='"+dateMin+"' and date<='"+dateMax+"'"
            
        else:
            phrase=" and date<='"+dateMax+"'"
            req=["SELECT min(date) from stats",()]
            dateMin=lecture_BDD(req)[0]["min(date)"]
            
    elif dateMin!="" and dateMin!=None:
        phrase=" and date>='"+dateMin+"'"
        dateMax=datetime.today().strftime('%Y-%m-%d')
        
    else:
        phrase=""
        dateMax=datetime.today().strftime('%Y-%m-%d')
        req=["SELECT min(date) from stats",()]
        dateMin=lecture_BDD(req)[0]["min(date)"]
        if dateMin==None:
            dateMin=dateMax
    req=["SELECT DISTINCT(niveau) FROM utilisateur",()]
    Lcat=lecture_BDD(req)
    req=["SELECT id,prenom FROM utilisateur ORDER BY(prenom)" ,()]
    Lref=lecture_BDD(req)
    LtotRef=[]
    for ref in Lref:
        #boucle for datemin to dateMax
        maxD=datetime.strptime(dateMax, '%Y-%m-%d')
        minD=datetime.strptime(dateMin, '%Y-%m-%d')
        LdateExtraction=[]
        LdateAjout=[]
        LdatePreparation=[]
        LdateFacturation=[]
        for i in range((maxD - minD).days + 1):
            dateFormat=minD + timedelta(days=i)
            dateI=dateFormat.strftime('%Y-%m-%d')
            #extraction 
            action='extraire'
            req=["SELECT count(pdt) from stats where date=? and idUser=? and action=?",(dateI,ref['id'],action)]
            pdt=int(lecture_BDD(req)[0]["count(pdt)"])
            LdateExtraction.append([dateI,pdt])
            #creation
            action='ajouter'
            req=["SELECT count(pdt) from stats where date=? and idUser=? and action=?",(dateI,ref['id'],action)]
            pdt=int(lecture_BDD(req)[0]["count(pdt)"])
            LdateAjout.append([dateI,pdt])
            #preparation
            action='preparer'
            req=["SELECT count(pdt) from stats where date=? and idUser=? and action=?",(dateI,ref['id'],action)]
            pdt=int(lecture_BDD(req)[0]["count(pdt)"])
            LdatePreparation.append([dateI,pdt])
            #facturation
            action='facturer'
            req=["SELECT count(pdt) from stats where date=? and idUser=? and action=?",(dateI,ref['id'],action)]
            pdt=int(lecture_BDD(req)[0]["count(pdt)"])
            LdateFacturation.append([dateI,pdt])

        jsondataExtraction=json.dumps({'Ldate':LdateExtraction})    
        jsondataAjout=json.dumps({'Ldate':LdateAjout})    
        jsondataPreparation=json.dumps({'Ldate':LdatePreparation})    
        jsondataFacturation=json.dumps({'Ldate':LdateFacturation})    

        LtotRef.append([jsondataExtraction,jsondataAjout,jsondataPreparation,jsondataFacturation])
    write_log(str(session['user']['id']),"/statUserPdt - Visualisation")
    return render_template("dw_stat_user_pdt.html",LtotRef=LtotRef,dateMin=dateMin,dateMax=dateMax,Lref=Lref,Lcat=Lcat)

##########info client##########
@app.route('/clients',methods=['GET', 'POST'])
def infoClient():
    checkUser()
    req=["SELECT * from client order by idCEclient,client",()]
    Lclients=lecture_BDD(req)
    write_log(str(session['user']['id']),"/clients - Visualisation")
    return render_template("dw_clients.html",Lclients=Lclients)
    

@app.route('/actionClient',methods=['GET', 'POST'])
def actionClient():
    checkUser()
    action=getValeurFormulaire("action")
    if action=="0":
        #supression doublons
        req=["SELECT idclient,mail,client FROM client GROUP BY mail,client HAVING COUNT(*) > 1",()]
        Lmail=lecture_BDD(req)
        for mail in Lmail:
            if mail['mail']!='' or len(mail["mail"])>1:
                req=["SELECT id_commande from commande where idclientCmd in (SELECT idclient from client where mail=? and client=?)",(mail["mail"],mail["client"])]
                LidCmd=lecture_BDD(req)
                for idCmd in LidCmd:
                    req=["UPDATE commande set idclientCmd=? where id_commande=?",(mail["idclient"],idCmd["id_commande"])]
                    ecriture_BDD(req)
                req=["delete from client where idclient<>? and mail=? and client=?",(mail["idclient"],mail["mail"],mail["client"])]
                ecriture_BDD(req)
        write_log(str(session['user']['id']),"/actionsClients - Suppression des doublons")
            
        return infoClient()
    if action=="1":
        export_Mail_Clients()
        write_log(str(session['user']['id']),"/actionsClients - Exportation des données clients")
    else:
        export_Infos_CE()
        write_log(str(session['user']['id']),"/actionsClients - Exportation des données CE")
    return '',204


#Traitement des données (CODE QTE OUI) et Calcul
def extraction(txt,cb,user):
    checkUser()
    date=datetime.today().strftime('%Y-%m-%d')
    idExtraction=session['user']['idExtraction']
    user=session['user']['id']
    req=["SELECT idCE from extractions where idExtraction=?",(idExtraction,)]
    nCE=lecture_BDD(req)[0]["idCE"]
    idCSE=txt['NOM cse']
    societe=txt['zone '+"1"]
    nom=txt['zone '+"2"]
    mail=txt['zone '+"3"].lower()
    tel=txt['zone '+"4"]
    adresse=txt['zone '+"5"]
    total=txt['zone '+"38"]
    if nCE=="" or nCE is None:
        if idCSE=="" or idCSE is None:
            req=["SELECT entreprise from listingCE where corbeille=0",()]
            listingCE=lecture_BDD(req)
            societeMax,ratio=getSocietor(societe,listingCE)
            if societeMax!="":
                req=["SELECT idCE from listingCE where entreprise=? and corbeille=0",(societeMax,)]
                idCE=lecture_BDD(req)[0]['idCE']
            else:
                idCE="900099"
        else:
            idCE="900"+idCSE
    else:
        idCE=nCE
        
    req=["insert into client(idExtraction,client,mail,tel,adresse,societe,idCEclient) values (?,?,?,?,?,?,?)",(idExtraction,nom,mail,tel,adresse,societe,idCE)]
    ecriture_BDD(req)
    req=["SELECT max(idclient) from client",()]
    idclient=lecture_BDD(req)[0]['max(idclient)']

    req=["insert into commande(idclientCmd,idExtractionCmd,total,idCE,idclientHW,etatCmd,date,corbeille,extractedBy) values (?,?,?,?,?,?,?,0,?)",(idclient,idExtraction,total,idCE,-1,0,date,user)]
    ecriture_BDD(req)

    req=["SELECT max(id_commande) from commande",()]
    idCmd=lecture_BDD(req)[0]['max(id_commande)']

    try :
        for i in range (ligne):
            offset=4*i
            strCode=txt['zone '+str(6+offset)]
            if strCode is not None:
                
                for parasite in parasites:
                    strCode=strCode.replace(parasite,"")
        
                if len(strCode)>0:
                    txtlib=txt['zone '+str(7+offset)]
                    prix=txt['zone '+str(8+offset)]
                    strQte=txt['zone '+str(9+offset)]
                    if i==0:
                        ato=cb['Case #C3#A0 cocher 1']['/V']
                    else:
                        ato=cb['Case #C3#A0 cocher 1'+"_"+str(2*i+1)]['/V']

                    if ato=="/Yes":
                        ato="oui"
                    else:
                        ato="non"
                    errone,strCode,ean,libW=checkCode(strCode)
                    if errone==0:
                        errone=checkPrix(prix,strCode)
                        if errone==0:
                            try:
                                for p in LparasiteQte:
                                    if strQte==p:
                                        strQte=1
                                intQte=int(strQte)
                                if intQte<=0 or intQte>3:
                                    raise ValueError
                            except ValueError:
                                errone=3
                    E=0
                    req=["insert into facturation(idCmd,code,ean,lib,libW,prix,qte,ato,errone,idHW,etatProd,etatMin,etatMax) values (?,?,?,?,?,?,?,?,?,?,?,?,?)",(idCmd,strCode,ean,txtlib,libW,prix,strQte,ato,errone,-1,E,E,E)]
                    ecriture_BDD(req)
    except:
        req=["delete from commande WHERE id_commande=?",(idCmd,)]
        ecriture_BDD(req)
    return idCmd
           

def initTraitement(nCE,user,repertoire,erreurFile):
    checkUser()
    #Parcours les PDFs - Récupération des données brutes - Traitement des données - Déplacement PDFs
    nbError=0
    nbFichier=0
    #repertoire=Luser[int(user)]["repertoire"]
    idExtraction=session['user']['idExtraction']
    #erreurFile=Luser[int(user)]["erreurFile"]
    separation_des_pages(repertoire)
    for nom in os.listdir(repertoire) :
        nbFichier+=1
        extension=nom.split('.')[-1]
        if extension=='csv' or extension=='CSV':
            extraction_auto(repertoire+"/",targetFile+"/",erreurFile+"/",nom)
            # try:
            #     chemin=repertoire+"/"
            #     liste,idclient=infos_dans_csv(chemin,nom,idExtraction,session['user']['id'])
            #     os.rename(repertoire+"/"+nom,targetFile+"/"+str(idclient)+".csv")
            # except Exception as e:
            #     print(str(e))
            #     print("error csv 1 :"+nom)
            #     nbError+=1
            #     try:
            #         shutil.move(repertoire+"/"+nom,erreurFile)
            #     except Exception as e:
            #         print("Already exists")
            #         os.remove(repertoire+"/"+nom)
        else:
            try :
                pdfobject=open(repertoire+"/"+nom,'rb')
                pdf=pypdf.PdfFileReader(pdfobject)
                txt=pdf.getFormTextFields()
                cb=pdf.getFields()
                pdfobject.close()
                idclient=extraction(txt,cb,user)
                os.rename(repertoire+"/"+nom,targetFile+"/"+str(idclient)+".pdf")

            except Exception as e:
                print(str(e))
                print("error 1 : "+nom)
                write_log(user,"WARNING: Le fichier "+nom+" a l erreur suivante : "+str(e))
                try:
                    pdfobject.close()
                    name, file_extension = os.path.splitext(nom)

                    if file_extension==".pdf" or file_extension==".PDF":
                        pages = convert_from_path(repertoire+"/"+nom,500)
                        pages[0].save(repertoire+"/"+name+'.jpg', 'JPEG')
                        try:
                            idclient=extractHandwrite(repertoire+"/"+name+".jpg",idExtraction,nCE)
                            os.remove(repertoire+"/"+name+'.jpg')
                        except Exception as e:
                            print(str(e))
                            print("Erreur PDF en Image extractHW")
                            write_log(user,"WARNING: Le fichier "+nom+" a l erreur suivante : "+str(e))

                            os.remove(repertoire+"/"+name+'.jpg')
                            raise TypeError
                    else:
                        idclient=extractHandwrite(repertoire+"/"+nom,idExtraction,nCE)
                    os.rename(repertoire+"/"+nom,targetFile+"/"+str(idclient)+file_extension)

                    
                except Exception as e:
                    print(str(e))
                    print("error 2 : "+nom)
                    write_log(user,"WARNING: Le fichier "+nom+" a l erreur suivante : "+str(e))

                    nbError+=1
                    try:
                        shutil.move(repertoire+"/"+nom,erreurFile)
                    except Exception as e:
                        print("Already exists")
                        write_log(user,"WARNING: Le fichier "+nom+" a l erreur suivante : "+str(e))
                        os.remove(repertoire+"/"+nom)
    return nbError,nbFichier


def separation_des_pages(repertoire):
    checkUser()
    n=0
    for nom in os.listdir(repertoire) :
        name, file_extension = os.path.splitext(nom)
        if file_extension==".pdf" or file_extension==".PDF":
            #JEANNE AVEC POPPLER
            pages = convert_from_path(repertoire+"/"+nom,500)
            #JEANNE SANS POPPLER
            #pages=[]
            if len(pages)>1:
                i=0
                for page in pages:
                    page.save(repertoire+"/"+name+'_'+str(n)+"_"+str(i)+'.jpg', 'JPEG')
                    i+=1
                os.remove(repertoire+"/"+nom)
            # try:
            #     pdfobject=open(repertoire+"/"+nom,'rb')
            #     pdf=pypdf.PdfFileReader(pdfobject)
            #     _=str(pdf.getFormTextFields())
            #     if pdf.getNumPages()>1:
            #         for page in range(pdf.getNumPages()):
            #             pdf_writer = pypdf.PdfFileWriter()
            #             pdf_writer.addPage(pdf.getPage(page))
            #             cmd=open(repertoire+"/"+name+"_" +str(n)+"_"+str(page)+ '.pdf','wb')
            #             pdf_writer.write(cmd)
            #             cmd.close()

            #         pdfobject.close()
            #         os.remove(repertoire+"/"+nom)
            #     else:
            #         pdfobject.close()
                
            # except Exception:
            #     pdfobject.close()
            #     pages = convert_from_path(repertoire+"/"+nom,500)
            #     i=0
            #     for page in pages:
            #         page.save(repertoire+"/"+name+'_'+str(n)+"_"+str(i)+'.jpg', 'JPEG')
            #         i+=1
            #     os.remove(repertoire+"/"+nom)
        n+=1
#endregion   

getXML()

if __name__ == '__main__':
    #webbrowser.open('http://172.20.10.10:5000')
    app.run(host='0.0.0.0', debug=False)