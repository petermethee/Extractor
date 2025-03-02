from flask import Flask

#----------------Constantes PC Jeanne

staticDir="C:/Users/jeann/Desktop/Parfumerie/CE_V4/bdd/static"
app = Flask(__name__,static_folder=staticDir)
app.secret_key = "jpcorp"
app.config['FACTURE_FOLDER'] = 'C:/Users/jeann/Desktop/Parfumerie/CE_V4/Factures'
targetFile='C:/Users/jeann/Desktop/Parfumerie/CE_V4/Succes'
repertoireImgClient='C:/Users/jeann/Desktop/Parfumerie/CE_V4/bdd/static/image_client'
repertoireImgCmd='C:/Users/jeann/Desktop/Parfumerie/CE_V4/bdd/static/image_cmd'
exportFold="C:/Users/jeann/Desktop/Parfumerie/CE_V4/Export"
statFold="C:/Users/jeann/Desktop/Parfumerie/CE_V4/Stat"
logFold="C:/Users/jeann/Desktop/Parfumerie/CE_V4/Stat"
bdd="C:/Users/jeann/Desktop/Parfumerie/CE_V4/bdd/bdd_hist_extraction.db"
bddCP="C:/Users/jeann/Desktop/Parfumerie/CE_V4/bdd/bdd_code_postal.db"
xmlARTICLE="C:/Users/jeann/Desktop/Parfumerie/CE_V4/xml/ARTICLE.xml"
xmlARTMAG="C:/Users/jeann/Desktop/Parfumerie/CE_V4/xml/ARTMAG.xml"
fact="C:/Users/jeann/Desktop/Parfumerie/CE_V4/Factures"
extraction_auto_fold_todo="C:/Users/jeann/Desktop/Parfumerie/CE_V4/Extraction_auto/A_Traiter/"
extraction_auto_fold_OK="C:/Users/jeann/Desktop/Parfumerie/CE_V4/Extraction_auto/Traites/"
extraction_auto_fold_KO="C:/Users/jeann/Desktop/Parfumerie/CE_V4/Extraction_auto/Echec/"

#------------------Constantes PC JD

# staticDir="/home/jamessou/CEPROG/bdd/static"
# app = Flask(__name__,static_folder=staticDir)
# app.secret_key = "jpcorp"
# app.config['FACTURE_FOLDER'] = '/home/jamessou/CE/Factures'
# targetFile='/home/jamessou/CE/Succes'
# repertoireImgClient='/home/jamessou/CEPROG/bdd/static/image_client'
# repertoireImgCmd='/home/jamessou/CEPROG/bdd/static/image_cmd'
# exportFold="/home/jamessou/CE/Export"
# statFold="/home/jamessou/CE/Stat"
# logFold= "/home/jamessou/CE/Stat"
# bdd="/home/jamessou/CEPROG/bdd/bdd_hist_extraction.db"
# bddCP="/home/jamessou/CEPROG/bdd/bdd_code_postal.db"
# xmlARTICLE="/home/jamessou/xmlpm/ARTICLE.xml"
# xmlARTMAG="/home/jamessou/xmlpm/ARTMAG.xml"
# fact="/home/jamessou/CE/Factures"

#-----------------Constantes globales

Lmag=["1-Sorgues","2-République","3-Les Halles","5-Isle","6-Vedène","Michael"]
infoIndex=["1","2","3","4","5","14_3"]
ligne=8
parasites=[",",".",":",";"," ","-","_","None",'REFERENCE','Reference','Référence','reference','référence','REF','Ref','ref','Réf','réf','/']
LparasiteQte=["l","L","i","I","|"]
delaiRupt=8

#-----------------Constantes mail
EMAIL_ADDRESS="cseparfums@gmail.com"
PASSWORD="rdlyghzgsadlfeue"
Lcode=[]
passkey="par84fumerie700"

#-----------------Constantes Sessions
app.config['SECRET_KEY']=b'a8ab364e355734de641db4e18298c74bff8625fe76c6725ce7ba25417f6a7d1a'

#-----------------Etats Commandes
# 0 -> Préparation
# 1 -> Facturation
# 2 -> Facturé
# 3 -> Livré
# 99 -> Annulé

#-----------------Etats Produits
# 0 -> Préparation
# 1 -> Reliquat
# 2 -> Facturé
# 3 -> Rupture
# 4 -> Annulé
# 5 -> Livré

#----------------Etats Paiements
# 0 -> Impayé
# 1 -> Payé
# 2 -> Annulé