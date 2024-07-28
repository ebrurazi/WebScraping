import os
import re
from bs4 import BeautifulSoup
import requests
from .veritabani import baglanti
from elasticsearch import Elasticsearch
import PyPDF2
# Elasticsearch bağlantısını kur
es = Elasticsearch(['http://localhost:9200'])

def elastic_search_kaydet(arama_kelimesi):
    # Elasticsearch'e veriyi kaydet
    elastic_data = {"kelime": arama_kelimesi}
    res = es.index(index='yazlab', body=elastic_data)  
    print(res)

# Örnek kullanım
#elastic_search_kaydet("deneme")

def google_scholar_arama(sorgu):
    # URL oluşturma
    url = f"https://scholar.google.com/scholar?hl=tr&as_sdt=0%2C5&q={sorgu}"

    # Sayfa kaynağını alma
    response = requests.get(url)
    html_icerik = response.content

    # BeautifulSoup ile ayrıştırma
    soup = BeautifulSoup(html_icerik, "html.parser")

    # Sonuçları bulma
    sonuclar = soup.find_all("div", class_="gs_r gs_or gs_scl")

    klasor_yolu = "./pdfler"
    if not os.path.exists(klasor_yolu):
        os.makedirs(klasor_yolu)

    # Sonuçları depolamak için bir liste oluşturalım
    sonuc_listesi = []
    yazimHatasi = "Yazım Hatası Yok"
    try:
        # Sonuçları bulma
        sonuclar = soup.find_all("div", class_="gs_r gs_or gs_scl")
        sonuc_yazim = soup.find("div", id="gs_res_ccl_top")

    except (AttributeError, TypeError, KeyError):
        yazimHatasi = None

    try:
        if sonuc_yazim.find("div", class_="gs_r") is not None:
            link_etiketi = sonuc_yazim.find("div", class_="gs_r").a
            if link_etiketi:
                link_href = link_etiketi.get("href")
                if link_href:
                    yazimHatasi = link_href.split("q=")[1]
                    yazimHatasi=yazimHatasi.replace("+", " ")


    except (AttributeError, TypeError, KeyError):
        yazimHatasi = None
    sayfa_sayisi =10
    while len(sonuc_listesi) < 10 and sayfa_sayisi <41:
        sonuc_listesi = liste_temizle(sonuc_listesi)
        for sonuc in sonuclar:
            referanslar = None 
            anahtarkelime = None
            doiNo=None
            ozet = "özet yok"
            alintiSayisi = "Bilgi Yok"  # alintiSayisi için varsayılan bir değer atandı
            Tarih = "Bilgi Yok"  # Tarih için varsayılan bir değer atama
            pdf_link = None  # pdf_link için varsayılan bir değer atama

            link = sonuc.find("h3", class_="gs_rt").a["href"] if sonuc.find("h3", class_="gs_rt").a else None

            if link.find("dergipark") != -1 and link.find("pub") != -1:
            
                response2 = requests.get(link)
                icerik2 = response2.content
                soup2 = BeautifulSoup(icerik2, "html.parser")
            # Başlık (try except block to handle missing title)
                try:
                    tmp = soup2.find("div", class_="tab-pane",id="article_tr")
                    baslik = tmp.find("h3", class_="article-title").text.strip()
                except (AttributeError, TypeError, KeyError):
                    baslik = None

                try:
                    alintiSayisi = sonuc.find("div", class_="gs_fl gs_flb").text
                    alintiSayisi = re.search(r'(?<=:)\s*\d+', alintiSayisi).group().strip()  # İlk sayıyı al
                    alintiSayisi = int(alintiSayisi)
                except AttributeError:
                    pass  # alintiSayisi zaten varsayılan bir değere sahip


            # Tarih
                try:
                    Tarih = sonuc.find("div", class_="gs_a").text
                    Tarih = re.search(r'(?<=,)\s*\d+', Tarih).group().strip()  # İlk sayıyı al
                    Tarih = int(Tarih)
                except AttributeError:
                    Tarih = "****"


                try:
                    yazarlar = soup2.find_all("meta", {"name": "citation_author"})
                    yazar = [ref["content"] for ref in yazarlar]
                except (AttributeError, TypeError, KeyError):
                    yazar = None

                try:
                    tmp = soup2.find("div", class_="tab-pane",id="article_tr")
                    ozet = tmp.find("div",class_="article-abstract data-section").text.strip()
                except (AttributeError, TypeError, KeyError):
                    ozet ="Ozet yok"
                try:
                    referans= soup2.find_all("meta", {"name": "citation_reference"})
                    referanslar = [ref["content"] for ref in referans] if referans else None
                except (AttributeError, TypeError, KeyError):
                    referanslar = None 
                try:
                    anahtarkelime= soup2.find("meta", {"name": "citation_keywords"})["content"]
                    anahtarKelimeler = anahtarkelime.split(",")
                except (AttributeError, TypeError, KeyError):
                    anahtarKelimeler = None

                try:
                    doiNo = "https://doi.org/"+soup2.find("meta", {"name": "citation_doi"})["content"]
                except (AttributeError, TypeError, KeyError):
                    doiNo= None
                try:
                    pdf_link = sonuc.find("div", class_="gs_or_ggsm").find("a")["href"]
                except AttributeError:
                    pdf_link = None

            else:
                try:
                    baslik = sonuc.find("h3", class_="gs_rt").a.text
                except AttributeError:
                    baslik = "Başlık Bulunamadı"
                try:
                    ozet = sonuc.find("div", class_="gs_rs").text
                except AttributeError:
                    ozet =  "Ozet Bulunamadı"

                try:
                    referanslar = sonuc.find("div", class_="gs_rs").text
                except AttributeError:
                    referanslar = "referans Bulunamadı"

            # Yazar (try except block to handle missing author)
                try:
                    yazar = sonuc.find("div", class_="gs_a").text
                    yazar = re.search(r'[^-]+',yazar).group().strip()
                except AttributeError:
                    yazar= "Yazar Bilgisi Bulunamadı"

            # Alıntılama sayısı
                try:
                    alintiSayisi = sonuc.find("div", class_="gs_fl gs_flb").text
                    alintiSayisi = re.search(r'(?<=:)\s*\d+', alintiSayisi).group().strip()  # İlk sayıyı al
                    alintiSayisi = int(alintiSayisi)
                except AttributeError:
                    pass  # alintiSayisi zaten varsayılan bir değere sahip


            # Tarih
                try:
                    Tarih = sonuc.find("div", class_="gs_a").text
                    Tarih = re.search(r'(?<=,)\s*\d+', Tarih).group().strip()  # İlk sayıyı al
                    Tarih = int(Tarih)
                except AttributeError:
                    Tarih = "****"
            # PDF Linki (try except block to handle missing link)
                try:
                    pdf_link = sonuc.find("div", class_="gs_or_ggsm").find("a")["href"]
                except AttributeError:
                    pdf_link = None

                if pdf_link:
                    # PDF dosya adını al
                    pdf_dosya_adı = pdf_link.split("/")[-1]+".pdf"

                    #PDF dosyasını indir ve kaydet
                    #with open(os.path.join(klasor_yolu, pdf_dosya_adı), "wb") as pdf_dosyasi:
                    #    pdf_response = requests.get(pdf_link)
                    #    pdf_dosyasi.write(pdf_response.content)

    
            sonuc_dict = {
                        "Baslik": baslik,
                         "Yazar": yazar,
                        "Alinti": alintiSayisi,
                        "Tarih": Tarih,
                        "PDF_Linki": pdf_link,
                        #"----------------------------------------------------------"
                        "Ozet":ozet,
                        #"----------------------------------------------------------"
                        "Referanslar":referanslar,
                        "Anahtar_Kelimeler":anahtarkelime,
                        "Doi_Numarası":doiNo,
                        "link":link,
                        "yazimHatasi":yazimHatasi
                    }

                # Sonuçları listeye ekleyin
            baglanti(sonuc_dict)
            sonuc_listesi.append(sonuc_dict)
        
        if len(sonuc_listesi) < 10 and sayfa_sayisi <41:

            url = f"https://scholar.google.com/scholar?start={sayfa_sayisi}hl=tr&as_sdt=0%2C5&q={sorgu}"
            sayfa_sayisi+=10
            # Sayfa kaynağını alma
            response = requests.get(url)
            html_icerik = response.content

            # BeautifulSoup ile ayrıştırma
            soup = BeautifulSoup(html_icerik, "html.parser")

            # Sonuçları bulma
            sonuclar = soup.find_all("div", class_="gs_r gs_or gs_scl")
        else :
            break    
        
        sonuc_listesi = liste_temizle(sonuc_listesi)


    sonuc_listesi_yeni = EksikDoldur(sonuc_listesi) 
    # Sonuçları döndür
    return sonuc_listesi_yeni

def extract_information(pdf_path):
    directory = os.path.dirname(pdf_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ''
            for page in reader.pages:
                text += page.extract_text() + ' '
    except PyPDF2.errors.PdfReadError as e:
        print(f"PDF dosyası okunamadı: {pdf_path}, hata: {e}")
        # Hata durumunda boş bir sözlük veya hata mesajını içeren bir sözlük döndürebilirsiniz
        return {"Hata": "PDF dosyası okunamadı"}

    patterns = {
        'Ozet': r'Özet\s*([\s\S]*?)\n(?:Anahtar Kelimeler|Giriş|1\.)',
        'Referanslar': r'(Referanslar|Kaynakça|Kaynaklar|References|KAYNAKLAR|Bibliography)\s*([\s\S]*?)(?=\n(?:Ekler|Teşekkürler|Appendix|Acknowledgements|Özgeçmiş|Index|\Z))',
        'Doi_Numarası': r'doi:\s*(\S+)',
        'Anahtar_Kelimeler': r'Anahtar Kelimeler:\s*([^\n]+)',
    }

    extracted_info = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if key == 'Referanslar':
                references_section = match.group(2).strip()
                # Referanslar bölümünde her bir referansı ayırma yöntemi, belgenizin formatına bağlı olarak değişebilir.
                references = references_section.split('\n')
                extracted_info[key] = [ref.strip() for ref in references if ref.strip()]
            else:
                extracted_info[key] = match.group(1).strip()
        else:
            extracted_info[key] = None

    return extracted_info

def EksikDoldur(sonuc_listesi_tmp):

    sonuc_listesi = []
    for sonuc in sonuc_listesi_tmp:

        try:
            # Referanslar eksikse ve link DergiPark'ta değilse
            if 'pub' not in sonuc.get("PDF_Link", ""):
                print("hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh")
                pdf_link = sonuc.get("PDF_Link")
                if pdf_link:
                    # PDF'i indir
                    response = requests.get(pdf_link)
                    if response.status_code == 200:
                        pdf_path = os.path.join('pdfler', pdf_link.split('/')[-1])+".pdf"
                        with open(pdf_path, 'wb') as pdf_file:
                            pdf_file.write(response.content)
                        # PDF'den bilgileri çıkar
                        extracted_info = extract_information(pdf_path)
                        # Eksik bilgileri güncelle
                        sonuc["Referanslar"] = extracted_info.get("Referanslar", "Referanslar bulunamadı")
                        tmp = sonuc.get("Ozet")
                        
                        sonuc["Ozet"] = extracted_info.get("Ozet", "Ozet Bulunamadı")
                        if sonuc["Ozet"] is None:
                            sonuc["Ozet"] =tmp

                        if sonuc["Anahtar_Kelimeler"] is None:
                            sonuc["Anahtar_Kelimeler"] = extracted_info.get("Anahtar_Kelimeler", "Anahtar Kelimeler bulunamadı")
                        if sonuc["Doi_Numarası"] is None:
                            sonuc["Doi_Numarası"] = extracted_info.get("Doi_Numarası", "Doi Numarası bulunamadı")
                sonuc_listesi.append(sonuc)
        
        except IOError as e:  # Giriş/çıkış hataları için genel bir hata yakalama
            print(f"PDF dosyası yazılamadı: {pdf_path}, hata: {e}")
            # Burada, hata durumunda nasıl bir eylemde bulunmak istediğinize dair kod ekleyebilirsiniz
        except Exception as e:  # Diğer tüm hatalar için genel bir hata yakalama
            print(f"Beklenmedik bir hata oluştu: {e}")
                
        
    return sonuc_listesi


def liste_temizle(liste):
    temiz_liste = []  # PDF linki olan sonuçları saklamak için boş bir liste

    for eleman in liste:
        if eleman['PDF_Link']:  # Eğer PDF_Linki anahtarının değeri varsa (None veya boş string değilse)
            temiz_liste.append(eleman)  # Elemanı temiz listeye ekle

    return temiz_liste  # Temizlenmiş listeyi döndür

    



    
