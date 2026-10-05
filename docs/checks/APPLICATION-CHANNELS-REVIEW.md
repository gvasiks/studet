# Каналы подачи — черновики на проверку

Собрано 2026-10-05. Это черновики таблицы `application_channel`: где подают
документы в каждый вуз на каждом уровне. На сайте ссылка появляется **только
после вашего подтверждения** — «через кого подача» относится к полям правила 6.

Источник данных — `pipeline/src/seed_application_channels.py`; эта таблица
печатается командой `python src/seed_application_channels.py --review`.

## Итог сбора

- Черновиков: **64** строк для **43** учреждений из 44.
- Закрывают 85 из 86 пар «вуз, уровень» каталога — 897 программ из 899.
- С дословной цитатой из источника: 40 строк; без цитаты: 24.
- Не собрано: Novikontas Jūras koledža (2 программы) — см. раздел 4.

## Что проверять в каждой строке

1. Ссылка открывается и ведёт туда, где абитуриент **с латвийским
   образованием** подаёт документы или читает, как их подать, на этот уровень.
2. Тип верный: «единая подача» (одна заявка через государственный портал)
   или «в сам вуз».
3. Страница не устарела: осенью многие вузы пишут, что набор закончен, а
   порядок на следующий год появится позже.

Чего в таблице нет: порядка для иностранных абитуриентов (это выпуск 4) и
сроков подачи (они хранятся отдельно, в `application_round`).

**Когда пересматривать:** в декабре, после того как вузы до 30 ноября
опубликуют правила на 2027/28 год. Состав участников единой подачи
объявляется на каждый год заново — список ниже относится к набору 2026 года.

## 1. Единая подача — 15 строк, 8 вузов

Все строки ведут на одну услугу: https://latvija.gov.lv/Services/54419
(«Elektroniskā pieteikšanās studijām pamatstudiju programmās»).

Источник — https://vienotauznemsana.lv/ : Vienoto uzņemšanu rīkoja Ekonomikas un kultūras augstskola, Daugavpils Universitāte, Latvijas Biozinātņu un tehnoloģiju universitāte, Latvijas Universitāte, Rīgas Tehniskā universitāte, Rīgas Ziemeļvalstu augstskola, Ventspils Augstskola un Vidzemes Augstskola. […] Pieteikties elektroniski var […] vienotajā valsts pārvaldes pakalpojumu portāla e-pakalpojumā “Elektroniskā pieteikšanās studijām pamatstudiju programmās”. (otrais teikums — no vienotauznemsana.lv/daliba/ka-pieteikties/)

Вузы: `du`, `eka`, `lbtu`, `lu`, `rnu`, `rtu`, `venta`, `via`. У всех — бакалавриат и, где есть, программы короткого
цикла (колледж-уровень).

Что стоит проверить отдельно:
- **RNU** (Rīgas Ziemeļvalstu augstskola) — в списке участников есть, но на
  своём сайте вуз предлагает собственную форму `apply.rnu.lv`. Возможно, обе
  дороги действуют одновременно.
- **EKA** — частный вуз в списке участников; на его сайте фразы о порядке
  подачи я не нашёл.
- Все ли программы уровня идут через единую подачу: заочные, англоязычные,
  программы Морской академии РТУ (по сайту единой подачи, заявку туда нельзя
  подтвердить электронно — только лично).
- **RSU в списке участников нет** — у него собственная система (раздел 2).
  В плане проекта было записано обратное («государственные — единая подача»).

| Вуз | Уровень | Куда ведёт ссылка | Источник | Цитата из источника | Заметка |
|---|---|---|---|---|---|
| `lu` | бакалавриат | https://latvija.gov.lv/Services/54419 | https://vienotauznemsana.lv/ | «Vienoto uzņemšanu rīkoja Ekonomikas un kultūras augstskola, Daugavpils Universitāte, Latvijas Biozinātņu un tehnoloģiju universitāte, Latvijas Universitāte, Rīgas Tehniskā universitāte, Rīgas Ziemeļvalstu augstskola, Ventspils Augstskola un Vidzemes Augstskola. […] Pieteikties elektroniski var […] vienotajā valsts pārvaldes pakalpojumu portāla e-pakalpojumā “Elektroniskā pieteikšanās studijām pamatstudiju programmās”. (otrais teikums — no vienotauznemsana.lv/daliba/ka-pieteikties/)» |  |
| `lu` | колледж | https://latvija.gov.lv/Services/54419 | https://vienotauznemsana.lv/ | «Vienoto uzņemšanu rīkoja Ekonomikas un kultūras augstskola, Daugavpils Universitāte, Latvijas Biozinātņu un tehnoloģiju universitāte, Latvijas Universitāte, Rīgas Tehniskā universitāte, Rīgas Ziemeļvalstu augstskola, Ventspils Augstskola un Vidzemes Augstskola. […] Pieteikties elektroniski var […] vienotajā valsts pārvaldes pakalpojumu portāla e-pakalpojumā “Elektroniskā pieteikšanās studijām pamatstudiju programmās”. (otrais teikums — no vienotauznemsana.lv/daliba/ka-pieteikties/)» |  |
| `rtu` | бакалавриат | https://latvija.gov.lv/Services/54419 | https://vienotauznemsana.lv/ | «Vienoto uzņemšanu rīkoja Ekonomikas un kultūras augstskola, Daugavpils Universitāte, Latvijas Biozinātņu un tehnoloģiju universitāte, Latvijas Universitāte, Rīgas Tehniskā universitāte, Rīgas Ziemeļvalstu augstskola, Ventspils Augstskola un Vidzemes Augstskola. […] Pieteikties elektroniski var […] vienotajā valsts pārvaldes pakalpojumu portāla e-pakalpojumā “Elektroniskā pieteikšanās studijām pamatstudiju programmās”. (otrais teikums — no vienotauznemsana.lv/daliba/ka-pieteikties/)» |  |
| `rtu` | колледж | https://latvija.gov.lv/Services/54419 | https://vienotauznemsana.lv/ | «Vienoto uzņemšanu rīkoja Ekonomikas un kultūras augstskola, Daugavpils Universitāte, Latvijas Biozinātņu un tehnoloģiju universitāte, Latvijas Universitāte, Rīgas Tehniskā universitāte, Rīgas Ziemeļvalstu augstskola, Ventspils Augstskola un Vidzemes Augstskola. […] Pieteikties elektroniski var […] vienotajā valsts pārvaldes pakalpojumu portāla e-pakalpojumā “Elektroniskā pieteikšanās studijām pamatstudiju programmās”. (otrais teikums — no vienotauznemsana.lv/daliba/ka-pieteikties/)» |  |
| `lbtu` | бакалавриат | https://latvija.gov.lv/Services/54419 | https://vienotauznemsana.lv/ | «Vienoto uzņemšanu rīkoja Ekonomikas un kultūras augstskola, Daugavpils Universitāte, Latvijas Biozinātņu un tehnoloģiju universitāte, Latvijas Universitāte, Rīgas Tehniskā universitāte, Rīgas Ziemeļvalstu augstskola, Ventspils Augstskola un Vidzemes Augstskola. […] Pieteikties elektroniski var […] vienotajā valsts pārvaldes pakalpojumu portāla e-pakalpojumā “Elektroniskā pieteikšanās studijām pamatstudiju programmās”. (otrais teikums — no vienotauznemsana.lv/daliba/ka-pieteikties/)» |  |
| `lbtu` | колледж | https://latvija.gov.lv/Services/54419 | https://vienotauznemsana.lv/ | «Vienoto uzņemšanu rīkoja Ekonomikas un kultūras augstskola, Daugavpils Universitāte, Latvijas Biozinātņu un tehnoloģiju universitāte, Latvijas Universitāte, Rīgas Tehniskā universitāte, Rīgas Ziemeļvalstu augstskola, Ventspils Augstskola un Vidzemes Augstskola. […] Pieteikties elektroniski var […] vienotajā valsts pārvaldes pakalpojumu portāla e-pakalpojumā “Elektroniskā pieteikšanās studijām pamatstudiju programmās”. (otrais teikums — no vienotauznemsana.lv/daliba/ka-pieteikties/)» |  |
| `du` | бакалавриат | https://latvija.gov.lv/Services/54419 | https://vienotauznemsana.lv/ | «Vienoto uzņemšanu rīkoja Ekonomikas un kultūras augstskola, Daugavpils Universitāte, Latvijas Biozinātņu un tehnoloģiju universitāte, Latvijas Universitāte, Rīgas Tehniskā universitāte, Rīgas Ziemeļvalstu augstskola, Ventspils Augstskola un Vidzemes Augstskola. […] Pieteikties elektroniski var […] vienotajā valsts pārvaldes pakalpojumu portāla e-pakalpojumā “Elektroniskā pieteikšanās studijām pamatstudiju programmās”. (otrais teikums — no vienotauznemsana.lv/daliba/ka-pieteikties/)» |  |
| `du` | колледж | https://latvija.gov.lv/Services/54419 | https://vienotauznemsana.lv/ | «Vienoto uzņemšanu rīkoja Ekonomikas un kultūras augstskola, Daugavpils Universitāte, Latvijas Biozinātņu un tehnoloģiju universitāte, Latvijas Universitāte, Rīgas Tehniskā universitāte, Rīgas Ziemeļvalstu augstskola, Ventspils Augstskola un Vidzemes Augstskola. […] Pieteikties elektroniski var […] vienotajā valsts pārvaldes pakalpojumu portāla e-pakalpojumā “Elektroniskā pieteikšanās studijām pamatstudiju programmās”. (otrais teikums — no vienotauznemsana.lv/daliba/ka-pieteikties/)» |  |
| `venta` | бакалавриат | https://latvija.gov.lv/Services/54419 | https://vienotauznemsana.lv/ | «Vienoto uzņemšanu rīkoja Ekonomikas un kultūras augstskola, Daugavpils Universitāte, Latvijas Biozinātņu un tehnoloģiju universitāte, Latvijas Universitāte, Rīgas Tehniskā universitāte, Rīgas Ziemeļvalstu augstskola, Ventspils Augstskola un Vidzemes Augstskola. […] Pieteikties elektroniski var […] vienotajā valsts pārvaldes pakalpojumu portāla e-pakalpojumā “Elektroniskā pieteikšanās studijām pamatstudiju programmās”. (otrais teikums — no vienotauznemsana.lv/daliba/ka-pieteikties/)» |  |
| `venta` | колледж | https://latvija.gov.lv/Services/54419 | https://vienotauznemsana.lv/ | «Vienoto uzņemšanu rīkoja Ekonomikas un kultūras augstskola, Daugavpils Universitāte, Latvijas Biozinātņu un tehnoloģiju universitāte, Latvijas Universitāte, Rīgas Tehniskā universitāte, Rīgas Ziemeļvalstu augstskola, Ventspils Augstskola un Vidzemes Augstskola. […] Pieteikties elektroniski var […] vienotajā valsts pārvaldes pakalpojumu portāla e-pakalpojumā “Elektroniskā pieteikšanās studijām pamatstudiju programmās”. (otrais teikums — no vienotauznemsana.lv/daliba/ka-pieteikties/)» |  |
| `via` | бакалавриат | https://latvija.gov.lv/Services/54419 | https://vienotauznemsana.lv/ | «Vienoto uzņemšanu rīkoja Ekonomikas un kultūras augstskola, Daugavpils Universitāte, Latvijas Biozinātņu un tehnoloģiju universitāte, Latvijas Universitāte, Rīgas Tehniskā universitāte, Rīgas Ziemeļvalstu augstskola, Ventspils Augstskola un Vidzemes Augstskola. […] Pieteikties elektroniski var […] vienotajā valsts pārvaldes pakalpojumu portāla e-pakalpojumā “Elektroniskā pieteikšanās studijām pamatstudiju programmās”. (otrais teikums — no vienotauznemsana.lv/daliba/ka-pieteikties/)» |  |
| `eka` | бакалавриат | https://latvija.gov.lv/Services/54419 | https://vienotauznemsana.lv/ | «Vienoto uzņemšanu rīkoja Ekonomikas un kultūras augstskola, Daugavpils Universitāte, Latvijas Biozinātņu un tehnoloģiju universitāte, Latvijas Universitāte, Rīgas Tehniskā universitāte, Rīgas Ziemeļvalstu augstskola, Ventspils Augstskola un Vidzemes Augstskola. […] Pieteikties elektroniski var […] vienotajā valsts pārvaldes pakalpojumu portāla e-pakalpojumā “Elektroniskā pieteikšanās studijām pamatstudiju programmās”. (otrais teikums — no vienotauznemsana.lv/daliba/ka-pieteikties/)» |  |
| `eka` | колледж | https://latvija.gov.lv/Services/54419 | https://vienotauznemsana.lv/ | «Vienoto uzņemšanu rīkoja Ekonomikas un kultūras augstskola, Daugavpils Universitāte, Latvijas Biozinātņu un tehnoloģiju universitāte, Latvijas Universitāte, Rīgas Tehniskā universitāte, Rīgas Ziemeļvalstu augstskola, Ventspils Augstskola un Vidzemes Augstskola. […] Pieteikties elektroniski var […] vienotajā valsts pārvaldes pakalpojumu portāla e-pakalpojumā “Elektroniskā pieteikšanās studijām pamatstudiju programmās”. (otrais teikums — no vienotauznemsana.lv/daliba/ka-pieteikties/)» |  |
| `rnu` | бакалавриат | https://latvija.gov.lv/Services/54419 | https://vienotauznemsana.lv/ | «Vienoto uzņemšanu rīkoja Ekonomikas un kultūras augstskola, Daugavpils Universitāte, Latvijas Biozinātņu un tehnoloģiju universitāte, Latvijas Universitāte, Rīgas Tehniskā universitāte, Rīgas Ziemeļvalstu augstskola, Ventspils Augstskola un Vidzemes Augstskola. […] Pieteikties elektroniski var […] vienotajā valsts pārvaldes pakalpojumu portāla e-pakalpojumā “Elektroniskā pieteikšanās studijām pamatstudiju programmās”. (otrais teikums — no vienotauznemsana.lv/daliba/ka-pieteikties/)» | У RNU есть и собственная форма apply.rnu.lv («Aizpildi RNU tiešsaistes pieteikuma formu») — проверить, что для бакалавриата верна единая подача. |
| `rnu` | колледж | https://latvija.gov.lv/Services/54419 | https://vienotauznemsana.lv/ | «Vienoto uzņemšanu rīkoja Ekonomikas un kultūras augstskola, Daugavpils Universitāte, Latvijas Biozinātņu un tehnoloģiju universitāte, Latvijas Universitāte, Rīgas Tehniskā universitāte, Rīgas Ziemeļvalstu augstskola, Ventspils Augstskola un Vidzemes Augstskola. […] Pieteikties elektroniski var […] vienotajā valsts pārvaldes pakalpojumu portāla e-pakalpojumā “Elektroniskā pieteikšanās studijām pamatstudiju programmās”. (otrais teikums — no vienotauznemsana.lv/daliba/ka-pieteikties/)» | У RNU есть и собственная форма apply.rnu.lv («Aizpildi RNU tiešsaistes pieteikuma formu») — проверить, что для бакалавриата верна единая подача. |

## 2. Подача в сам вуз — с цитатой (25 строк)

| Вуз | Уровень | Куда ведёт ссылка | Источник | Цитата из источника | Заметка |
|---|---|---|---|---|---|
| `rtu` | магистратура | https://www.rtu.lv/lv/studijas/uznemsana/pieteiksanas-magistra-limena-studijam | та же страница | «Dokumentu iesniegšana maksas studiju vietās otrā cikla augstākās izglītības (maģistra) studiju programmās norisinās elektroniski un klātienē RTU Uzņemšanas un servisa nodaļas darba laikā» |  |
| `rtu` | докторантура | https://www.rtu.lv/lv/studijas/doktora-limena-studijas/uznemsana-doktora/uznemsanas-process | та же страница | «Piesakoties doktorantūras vakancei, gan pretendenti uz budžeta vietām, gan tie, kuri plāno studēt par fizisko un juridisko personu līdzekļiem, iesniedz visus nepieciešamos dokumentus […], nosūtot tos uz e‑pastu: doktorantura@rtu.lv.» |  |
| `rnu` | все уровни | https://rnu.lv/uznemsana/pieteiksanas-kartiba/ | та же страница | «Aizpildi RNU tiešsaistes pieteikuma formu. […] Iesniedz dokumentus elektroniski vai klātienē atbilstoši Uzņemšanas komisijas norādījumiem.» |  |
| `venta` | магистратура | https://www.venta.lv/pieteiksanas-magistra-studiju-programmam | та же страница | «sūtot elektroniski parakstītu pieteikumu uz e-pastu studijas@venta.lv vai papīrā pašrocīgi parakstītu pa pastu uz adresi Inženieru iela 101, Ventspils, LV-3601, adresējot to Ventspils Augstskolas Uzņemšanas komisijai.» | Страница «Kā pieteikties maģistra studijām?»; ссылка на неё — со страниц магистерских программ. |
| `rsu` | бакалавриат | https://uznemsana.rsu.lv/ | https://www.rsu.lv/studiju-iespejas/uznemsana-pamatstudiju-programmas | «RSU e-Uzņemšanā ir iespējams pieteikties tikai ar Latvija.lv autorizācijas starpniecību.» | RSU нет в списке участников единой подачи 2026 года. |
| `rsu` | колледж | https://uznemsana.rsu.lv/ | https://www.rsu.lv/studiju-iespejas/uznemsana-pamatstudiju-programmas | «RSU e-Uzņemšanā ir iespējams pieteikties tikai ar Latvija.lv autorizācijas starpniecību.» | RSU нет в списке участников единой подачи 2026 года. |
| `rsu` | магистратура | https://uznemsana.rsu.lv/ | https://www.rsu.lv/uznemsana-magistra-studiju-programmas | «Pēc apstiprinājuma e-pasta saņemšanas tev ir jāatgriežas savā elektroniskajā pieteikumā (RSU e-Uzņemšanā) un no savas puses jāapstiprina pieteikums.» |  |
| `rsu` | докторантура | https://uznemsana.rsu.lv/ | https://www.rsu.lv/uznemsana-doktorantura | «Elektroniskā pieteikšanās studijām 3.08.–25.09. plkst. 16» |  |
| `lma` | магистратура | https://apply.lma.lv/ | та же страница | «Sveicam, Latvijas Mākslas akadēmijas elektroniskās reģistrēšanās sistēmā! […] Reģistrēšanās un pieteikšanās studijām Latvijas Mākslas akadēmijas maģistra programmā 2026./2027. studiju gadā no 1. aprīļa plkst.12:00 līdz 9. jūlija plkst. 23:59» | В меню lma.lv раздела приёма нет; сюда ведёт кнопка «PIETEIKTIES STUDIJĀM» со страниц специальностей. |
| `lma` | бакалавриат | https://apply.lma.lv/ | та же страница | «Sveicam, Latvijas Mākslas akadēmijas elektroniskās reģistrēšanās sistēmā!» | Тексты на странице говорят о магистратуре. Что бакалавриат подаётся там же — НЕ подтверждено; проверить по правилам приёма бакалавриата на lma.lv. |
| `lnaa` | все уровни | https://www.klustikaravirs.lv/pieteikties | https://www.naa.mil.lv/lv | «Latvijas pilsoņi no 18 gadiem var pieteikties dažādiem dienestiem un apmācībām, aizpildot pieteikuma anketu tiešsaistē.» | Ссылка «Piesakies» с главной страницы LNAA ведёт на klustikaravirs.lv; цитата — оттуда. |
| `turiba` | все уровни | https://www.turiba.lv/lv/uznemsana | та же страница | «Aizpildi elektronisko pieteikšanās formu. […] Sagatavo iesniedzamos dokumentus un dodies uz augstskolu vai iesniedz tos attālināti, ja tev ir drošs elektroniskais paraksts.» |  |
| `riseba` | все уровни | https://riseba.lv/nac-studet/ka-pieteikties-studijam/ | та же страница | «Pietiekties studijām var gan tiešsaistē, gan arī klātienē, ierodoties augstskolā.» |  |
| `tsi` | все уровни | https://tsi.lv/future-students/admission/ | та же страница | «Applications are made online, at the official admission portal admission.tsi.lv. Submit your documents electronically in just a few clicks!» |  |
| `bsa` | все уровни | https://bsa.edu.lv/index.php/lv/uznemsana/e-pieteikums-studijam.html | та же страница | «Pieteikumu iesniegšana, aizpildot elektronisko veidlapu un augšupielādējot nepieciešamos dokumentus:» |  |
| `sse-riga` | бакалавриат | https://www.sseriga.edu/education/bachelor/admission | та же страница | «Step 1: Submit the Online Application by April 6, 2027» |  |
| `ekra` | все уровни | https://kra.lv/studiju-programmas/studentu-uznemsana/ | та же страница | «Aizpildi elektronisko Pieteikuma veidlapu» |  |
| `bvk` | все уровни | https://www.bvk.lv/uznemsana/ | та же страница | «Uzņemšanai nepieciešamos dokumentus iesniedz elektroniski – bvk@bvk.lv vai BVK birojā Rīgas centrā, Alberta ielā 13, iepriekš saskaņajot ierašanās laiku.» |  |
| `dmk` | все уровни | https://dmk.lv/uznemsanas-noteikumi/ | та же страница | «Pieteikšanās studijām īsā cikla profesionālās Augstākās izglītības programmās 2026./2027. akadēmiskajam gadam notiks klātienē» |  |
| `gfk` | все уровни | https://www.koledza.lv/index.php/lv/uznemsana | та же страница | «Pieteikšanās studijām elektroniski no 2. aprīļa» |  |
| `juridiska-koledza` | все уровни | https://jk.lv/uznemsana/uznemsana/iesniedzamie-dokumenti/ | та же страница | «Pieteikšanās studijām notiek elektroniski. […] Lūdzu, aizpildiet pieteikuma veidlapu elektroniski!» |  |
| `malnavas-koledza` | все уровни | https://malnavaskoledza.lv/lv/uznemsana-isa-cikla-profesionala-augstaka-izglitiba | та же страница | «Dokumentus var iesniegt klātienē, ierodoties LBTU Malnavas koledžas Studiju daļā, 63. kabinetā […] vai elektroniski, parakstītus ar drošu elektronisko parakstu, nosūtot uz e-pasta adresi» |  |
| `rbk` | все уровни | https://www.rck.lv/augstaka-izglitiba/uznemsana/ | та же страница | «DOKUMENTU IESNIEGŠANA ELEKTRONISKI LĪDZ 2026. GADA 6.SEPTEMBRIM […] Piesakies studijām un iesniedz dokumentus šeit;» |  |
| `rmenk` | все уровни | https://college.lv/uznemsanas-kartiba/ | та же страница | «Lai pieteiktos studijām reflektantam ir jāaizpilda elektroniskā pieteikuma forma pievienojot visus nepieciešamos dokumentus.» |  |
| `vrsk` | все уровни | https://www.vrk.rs.gov.lv/lv/isa-cikla-profesionalas-augstakas-izglitibas-programma-robezapsardze | та же страница | «Uzņemšanas noteikumi pilna un nepilna laika studijām Valsts robežsardzes koledžā 2026.gadā» | Страница программы короткого цикла «Robežapsardze»; цитата — название документа с правилами приёма на ней. Порядок подачи — в самих правилах. |

## 3. Подача в сам вуз — без цитаты (24 строк), проверить в первую очередь

Страница приёма найдена по ссылке «Uzņemšana» (или «Apply») с главной
страницы вуза, но фразы о том, как подавать документы, на ней автоматически
не нашлось. Ссылка может вести не на ту страницу.

| Вуз | Уровень | Куда ведёт ссылка | Источник | Цитата из источника | Заметка |
|---|---|---|---|---|---|
| `lu` | магистратура | https://www.lu.lv/gribustudet/uznemsanas-kartiba/magistra-limena-studijas/ | та же страница | нет | На 2026-10-05 страница сообщает, что набор закончен, сведения на 2027/28 появятся позже. |
| `lu` | докторантура | https://doktorantura.lu.lv/uznemsana/ | та же страница | нет |  |
| `lbtu` | все уровни | https://www.lbtu.lv/lv/uznemsana-latvijas-biozinatnu-un-tehnologiju-universitate-lbtu | та же страница | нет | Общая страница приёма; для магистратуры на ней ссылка «pieteikuma anketa» (lbtu.lv/lv/pieteiksanas/magistriem). |
| `du` | все уровни | https://du.lv/gribu-studet/uznemsana/ | та же страница | нет | Общая страница «Uzņemšana 2026. gadā» с правилами приёма по уровням (PDF). |
| `via` | все уровни | https://va.lv/uznemsana | та же страница | нет | Общая страница приёма; для иностранцев там же ссылка на va.dreamapply.com. |
| `eka` | все уровни | https://www.augstskola.lv/?parent=96&lng=lva | та же страница | нет | Страница «Uzņemšanas prasības» найдена по ссылке с главной; фразы о порядке подачи не нашлось. |
| `lka` | все уровни | https://lka.edu.lv/lv/gribu-studet-akademija/ | та же страница | нет |  |
| `jvlma` | все уровни | https://www.jvlma.lv/studijas/uznemsana | та же страница | нет | На странице — ссылки на формы заявлений (Google Forms) и документы по уровням. |
| `rgsl` | все уровни | https://apply.rgsl.edu.lv/ | https://www.rgsl.edu.lv/ | нет | Ссылка «Apply» в шапке сайта RGSL. |
| `rai` | все уровни | https://rai.lv/news/uznemsana/uznemsana-2026-2027/tiessaites-pieteikuma-forma/ | https://rai.lv/news/uznemsana/uznemsana-2026-2027/ | нет | Адрес с годом набора (2026-2027) — в следующем сезоне сменится. |
| `lutera` | все уровни | https://luteraakademija.lv/?ct=uznemsana | та же страница | нет |  |
| `rarzi` | все уровни | https://www.rarzi.lv/uz%C5%86em%C5%A1ana | та же страница | нет | На странице — анкеты бакалавра и магистра (Google Docs). |
| `rti` | все уровни | https://garigais.lv/programma/ | та же страница | нет | Кнопка «PIETEIKTIES» ведёт на страницу контактов; правила приёма — PDF 2023 года. |
| `alberta` | все уровни | https://www.alberta-koledza.lv/?parent=19&lng=lva | та же страница | нет | На странице ссылка на систему pieteikumi.alberta-koledza.lv. |
| `hotel-school` | все уровни | https://hotelschool.lv/prasibas-reflektantiem/ | та же страница | нет | На странице ссылка на форму hotelschool.lv/tiessaistes-pieteikuma-forma/. |
| `psmk` | все уровни | https://psk.lu.lv/uznemsanas-noteikumi | та же страница | нет |  |
| `r1mk` | все уровни | https://www.rmk1.lv/lv/studiju-iespejas/uznemsana/ | та же страница | нет |  |
| `rmk` | все уровни | https://rmkoledza.lu.lv/lv/nac-studet/ | та же страница | нет |  |
| `rtk` | все уровни | https://www.rtk.lv/lv/uznemsana-koledza | та же страница | нет |  |
| `siva` | все уровни | https://www.siva.gov.lv/lv/izglitibas-programmas | та же страница | нет |  |
| `skmk` | все уровни | https://rcmc.lv/studiju-programmas/pieteiksanas-studijam/ | та же страница | нет | Заголовок страницы — «Pieteikšanās studijām». |
| `ucak` | все уровни | https://www.ucak.vugd.gov.lv/lv/uznemsana-studijam-0 | та же страница | нет | Заголовок страницы — «Uzņemšana studijām». |
| `vpk` | все уровни | https://www.policijas.koledza.gov.lv/lv/uznemsanas-noteikumi-0 | та же страница | нет | На странице ссылка «elektroniskais pieteikums» (e-studijas.vp.gov.lv/uznemsana). |
| `ljk` | все уровни | https://ljk.lv/uznemsana | та же страница | нет | На главной ljk.lv рядом — ссылка «UZŅEMŠANAS ANKETA» (registracija.ljk.lv). 2026-10-05 сайт сначала не отвечал (HTTP 522), потом открылся. |

## 4. Не собрано

| Что | Почему |
|---|---|
| `novikonta` | страницы колледжа на novikontas.org отдают 404 — и адрес из базы (/college/lv), и ссылка «Novikontas Academy» с главной страницы самого сайта, и /college/lv/ka_iestaties, которую показывает поиск |

У этих программ блока «Kur pieteikties» не будет, пока запись не появится.

## Как подтвердить

Подтверждение — в Supabase Studio, SQL Editor. Имя в `verified_by` — ваше.

Одна запись вуза и уровня:

```sql
update application_channel ac
set verified_at = now(), verified_by = 'ваше имя'
from university u
where u.id = ac.university_id
  and u.slug = 'rsu'
  and ac.degree_level = 'master';
```

Запись «все уровни» — вместо последней строки `and ac.degree_level is null;`.

Все строки единой подачи разом (после проверки списка участников):

```sql
update application_channel
set verified_at = now(), verified_by = 'ваше имя'
where channel_type = 'unified_portal';
```

Исправить ссылку перед подтверждением:

```sql
update application_channel ac
set url = 'https://…', source_url = 'https://…'
from university u
where u.id = ac.university_id and u.slug = 'lka' and ac.degree_level is null;
```

Посмотреть, что ещё не подтверждено:

```sql
select u.slug, ac.degree_level, ac.channel_type, ac.url
from application_channel ac
join university u on u.id = ac.university_id
where ac.verified_at is null
order by u.slug, ac.degree_level;
```

Повторный запуск `seed_application_channels.py --apply` подтверждённые
строки не трогает.
