# Ugh...



Data structure, need to recheck how I got it
```
data
├── osnovni.csv
├── vplivana.csv
├── vsebina.bson
│   └── pisrs
│       ├── vsebina.bson
│       └── vsebina.metadata.json
└── vsebina.tar.gz
```

## Notes:

### mail PISRS
PISRS ima tudi spletni servis, ki za potrebe ponovne uporabe informacij javnega značaja omogoča prevzem prečiščenih in osnovnih besedil v formatu .pdf, .htm in .doc.

- Za prevzem prečiščenih besedil:
http://pisrs.si/Pis.web/npbDocPdf?idPredpisa=(ID osnovnga predpisa)&idPredpisaChng=(ID novele)&type=(vrsta zapisa:pdf, doc, html)
Primer:
http://pisrs.si/Pis.web/npbDocPdf?idPredpisa=ZAKO8009&idPredpisaChng=ZAKO4697&type=doc


- Za prevzem osnovnih besedil:
http://www.pisrs.si/Pis.web/npbDocPdf?idPredpisa=(ID osnovnega predpisa)&type=(vrsta zapisa:pdf, doc, html)
Primer:
http://www.pisrs.si/Pis.web/npbDocPdf?idPredpisa=ZAKO4697&type=doc

Osnovno besedilo Zakona o dohodnini – ZDoh-2 (Uradni list RS, št. 117/06 z dne 16. 11. 2006) je dostopno na:
http://www.pisrs.si/Pis.web/npbDocPdf?idPredpisa=ZAKO4697&type=doc v .doc formatu
http://www.pisrs.si/Pis.web/npbDocPdf?idPredpisa=ZAKO4697&type=pdf v .pdf formatu in
http://www.pisrs.si/Pis.web/npbDocPdf?idPredpisa=ZAKO4697&type=html v .html formatu

### Q: A je slucajno kje mozno dobiti seznam vseh idPredpis ter idPredpisaChng?
A: na portalu OPSI se nahajajo vsi podatki (tudi NPBji):
https://podatki.gov.si/publisher/vlada_republike_slovenije_sluzba_za_zakonodajo.

Med osnovnimi podatki je na voljo tudi tabela "vpliva_na", ki prikazuje na kateri predpis posamezen predpisa (ali njegov predlog) vpliva.

Podatki se lahko uparjo z "osnovni" kjer so na ID vezani še podatki o naslovu, vrsti, veljavnosti, objavi itd. predpisa.

### Pravna podlaga za pripravo prečiščenih besedil predpisov je podana:


za vse predpise v 1. točki prvega odstavka 10. člena Zakona o dostopu do informacij javnega značaja ( Uradni list RS, št 51/06 – uradno prečiščeno besedilo 2 in 117/06-ZDavP), po kateri je vsak organ dolžan, kot informacijo javnega značaja, posredovati v svetovni splet neuradna prečiščena besedila predpisov, ki se nanašajo na njegovo delovno področje;
 

za zakone v 153. členu Poslovnika Državnega zbora, po katerem
neuradno prečiščeno besedilo, ki se objavi na spletnih straneh Državnega zbora, pripravi Zakonodajno-pravna služba Državnega zbora po vsaki spremembi ali dopolnitvi zakona,
uradno prečiščeno besedilo, ki se objavi v Uradnem listu Republike Slovenije in na spletnih straneh Državnega zbora, potrdi Državni zbor na podlagi sklepa, ki ga sprejme na predlog matičnega delovnega telesa, Vlade ali poslanske skupine;


### Komentar o neuradnih preciscenih besedilih
neuradna prečiščena besedila, ki so dostopna v pravno-informacijskem sistemu, le informativnega značaja, pravno veljavni pa so le podatki in besedila pravnih aktov, ki so objavljeni v Uradnem listu Republike Slovenije. Neuradna prečiščena besedila predstavljajo le informativni delovni pripomoček, ki sicer pomembno prispeva k preglednosti in uporabnosti predpisov, vendar nima pravne veljavnosti.

