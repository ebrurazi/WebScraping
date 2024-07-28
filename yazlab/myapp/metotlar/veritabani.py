import pymongo
from elasticsearch import Elasticsearch
import hashlib

# MongoDB için bağlantı dizesi
connection_string = "mongodbclient//"
client = pymongo.MongoClient(connection_string)
db = client["yazlab"]
collection = db["yazlab21c"]


# Elasticsearch bağlantısını kur
es = Elasticsearch(['http://localhost:9200'])

# Elasticsearch'de bir index oluştur
index_adi = "yazlab"
# veritabani.py içindeki örnek bir `baglanti` fonksiyonu
def baglanti(veri):
    # Veriyi MongoDB koleksiyonuna kaydet
    collection.insert_one(veri)

def uygun_format_duzenle(veri):
    uygun_format = veri.copy()

    uygun_format.pop('_id', None)

    tarih_degeri = veri.get('Tarih', {})
    if isinstance(tarih_degeri, dict):
        tarih_degeri = tarih_degeri.get('$numberInt', 0)

    try:
        uygun_format['Tarih'] = int(tarih_degeri)
    except ValueError:
        uygun_format['Tarih'] = 0

    alinti_degeri = veri.get('Alinti', {})
    if isinstance(alinti_degeri, dict):
        alinti_degeri = alinti_degeri.get('$numberInt', '0')
    try:
        uygun_format['Alinti'] = int(alinti_degeri)
    except ValueError:
        uygun_format['Alinti'] = 0  # veya uygun gördüğünüz başka bir değer

    return uygun_format


def elastic_search_kaydet(arama_kelimesi, veri):
    # Benzersiz bir ID üret (Örneğin kelimenin kendisini kullanabilirsiniz)
    kelime_id = hashlib.sha256(arama_kelimesi.encode('utf-8')).hexdigest()
    
    # Elasticsearch'e veriyi kaydet
    res = es.index(index='yazlab', id=kelime_id, body=veri)
    print(res['result'], res['_id'])

def verileri_mongodb_den_cek():
    # MongoDB'den tüm verileri çek
    veriler = collection.find()
    return list(veriler)

def verileri_elasticsearche_kaydet(veriler):
    # Elasticsearch'e verileri kaydet
    for veri in veriler:
        veri_id = str(veri['_id'])
        uygun_format = uygun_format_duzenle(veri)
        elastic_search_kaydet(veri_id, uygun_format)

# Verileri MongoDB'den çek
mongodb_verileri = verileri_mongodb_den_cek()

# Verileri Elasticsearch'e kaydet
verileri_elasticsearche_kaydet(mongodb_verileri)