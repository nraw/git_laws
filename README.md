# Format laws as git repos


[Zakone lahko predlagajo](https://www.dz-rs.si/wps/portal/Home/zakonodaja/zakonodajniPostopek):
– Vlada,
– vsak poslanec,
– Državni svet,
– najmanj pet tisoč volivcev.

Predlogi so [tukaj](https://e-uprava.gov.si/si/drzava-in-druzba/e-demokracija/predlogi-predpisov.html)

## Podatki:

Predpisi: https://podatki.gov.si/dataset/osnovni-podatki-o-predpisih-rs
Predlogi: https://podatki.gov.si/dataset/dzpredlogi-zakonov

Drzavni Zbor: https://www.dz-rs.si/wps/portal/Home/ostalo/OpenData
- Sprejeti predlogi: https://fotogalerija.dz-rs.si/datoteke/opendata/SZ.XML
Vlada: https://podatki.gov.si/dataset/vladna-gradiva-2


## IDs:
SOP:
podatke o objavi predpisa v Uradnem listu Republike Slovenije s slovensko oznako predpisa (v nadaljnjem besedilu: SOP),


EVA:
EVA je enotna identifikacijska oznaka, ki jo je potrebno določiti vsakemu 
predlogu predpisa, ki ga sprejme minister, vlada ali drug nosilec javnih pooblastil 
ali ki se vlaga v zakonodajni postopek v državni zbor, in vsakemu predlogu 
drugega predpisa ali akta iz 8. člena te priloge (v nadaljnjem besedilu: predpis), 
ki se po sprejemu objavi v Uradnem listu Republike Slovenije.
     EVA omogoča povezovanje podatkov v različnih uradnih evidencah in 
dokumentnih bazah podatkov, ki jih z namenom spremljanja zakonodajnega 
postopka vodijo državni organi.
https://www.uradni-list.si/glasilo-uradni-list-rs/vsebina/2003-01-1438?sop=2003-01-1438


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

### API

```
curl -X 'GET' \
  'https://pisrs.si/extapi/predpis/register-predpisov/seznam' \
  -H 'accept: */*' -H 'X-API-Key: $PISRS_API_KEY'
```
