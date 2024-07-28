from django.shortcuts import render
from django.http import JsonResponse
from elasticsearch import Elasticsearch
from .forms import PublicationFilterForm
from .metotlar.deneme import google_scholar_arama, elastic_search_kaydet
from .models import Publication  # Model adını kendi modelinle değiştir
import pymongo
import requests

es = Elasticsearch(['http://localhost:9200'])
MAX_SUGGESTIONS = 10  # Maksimum öneri/arayış sayısı

def get_external_suggestions(prefix):
    api_url = f"https://api.datamuse.com/words?sp={prefix}*"
    response = requests.get(api_url)
    
    if response.status_code == 200:
        data = response.json()
        suggestions = [item['word'] for item in data][:MAX_SUGGESTIONS]
        return suggestions
    else:
        return []

def search_suggestions(request):
    query = request.GET.get('query', '')
    suggestions = []

    if not query:  # Eğer sorgu boşsa, önceki aramaları getir
        response = es.search(
            index='your_index_name',  # ElasticSearch index adınız
            body={
                "sort": [
                    {"search_date": {"order": "desc"}}  # Aramaları tarihine göre sırala
                ],
                "query": {
                    "match_all": {}  # Tüm dokümanları getir
                },
                "size": 10  # Son 10 aramayı getir
            }
        )
        suggestions = [hit['_source']['search_query'] for hit in response['hits']['hits']]  # 'search_query' alanınızın adı
    else:  # Eğer sorgu varsa, sorguyla eşleşen önerileri getir
        response = es.search(index='your_index_name', body={"query": {"prefix": {"search_query": query}}})
        suggestions = [hit['_source']['search_query'] for hit in response['hits']['hits']]

    return JsonResponse(suggestions, safe=False)
def home(request):
    form = PublicationFilterForm(request.GET or None)

    connection_string = "mongodbclient//"
    client = pymongo.MongoClient(connection_string)
    db = client["yazlab"]
    collection = db["yazlab21c"]

    query = {}
    if request.method == 'GET' and form.is_valid():
        title = form.cleaned_data.get('title')
        authors = form.cleaned_data.get('authors')
        citation_count = form.cleaned_data.get('citation_count')
        publication_year = form.cleaned_data.get('publication_year')
        
        if title:
            query['Baslik'] = {"$regex": title, "$options": "i"}
        if authors:
            query['Yazar'] = {"$regex": authors, "$options": "i"}
        if citation_count:
            query['Alinti'] = citation_count
        if publication_year:
            # Yıl için sorgu yaparken MongoDB'deki tam sayı değeriyle eşleşmesi gerekir
            query['Tarih'] = publication_year

    publications = list(collection.find(query))

    # MongoDB'den alınan bazı verilerin dönüşümü için döngü
    for publication in publications:
           # Başlık alanını işle
        publication['Baslik'] = publication.get('Baslik', 'Başlık Yok')

        if isinstance(publication.get('Yazar'), list):
            publication['Yazar'] = ', '.join(publication.get('Yazar', ['Yazar Yok']))
        else:
            publication['Yazar'] = publication.get('Yazar', 'Yazar Yok')

        if 'Alinti' in publication and isinstance(publication['Alinti'], dict):
            publication['Alinti'] = publication['Alinti'].get('$numberInt', 'Bilgi Yok')
        if 'Tarih' in publication and isinstance(publication['Tarih'], dict):
            try:# MongoDB'den gelen veriyi int'e çevir
                publication['Tarih'] = int(publication['Tarih'].get('$numberInt', "0"))
            except ValueError: # Dönüşüm sırasında bir hata olursa, varsayılan olarak 0 değerini ata
                publication['Tarih'] = 0
        

    return render(request, 'myapp/home.html', {'form': form, 'publications': publications})


def search_suggestions(request):
    query = request.GET.get('query', '')
    response = es.search(index='yazlab', body={"query": {"wildcard": {"kelime": f"*{query}*"}}})
    current_suggestions = {hit['_source']['kelime'] for hit in response['hits']['hits']}
    previous_searches = request.session.get('previous_searches', [])
    
    # Mevcut ve önceki önerileri birleştir
    all_suggestions = list(set(previous_searches).union(current_suggestions))
    
    # En yeni öneriden en eski öneriye sırala (en yeni öneri listenin başında)
    all_suggestions = all_suggestions[:MAX_SUGGESTIONS]  # En son 10 öneriyi al
    
    request.session['previous_searches'] = all_suggestions
    request.session.modified = True
    return JsonResponse(all_suggestions, safe=False)
def search_results(request):
    if request.method == 'POST':
        arama_kelimesi = request.POST.get('search_query')
        previous_searches = request.session.get('previous_searches', [])
        
        # Eğer arama kelimesi zaten listedeyse, çıkar
        if arama_kelimesi in previous_searches:
            previous_searches.remove(arama_kelimesi)
        
        # Yeni arama kelimesini listenin başına ekle
        previous_searches.insert(0, arama_kelimesi)
        
        # Listenin boyutunu kontrol et, fazla ise en sondakini çıkar
        if len(previous_searches) > MAX_SUGGESTIONS:
            previous_searches.pop()

        request.session['previous_searches'] = previous_searches
        request.session.modified = True
        
        # Google Scholar'dan arama sonuçlarını getir (veya benzeri bir işlem)
        search_results = google_scholar_arama(arama_kelimesi)
        
        # Arama sonuçlarını kaydet (isteğe bağlı)
        for result in search_results:
            elastic_search_kaydet(arama_kelimesi)
        
        # Arama sonuçlarını ve önceki aramaları şablona gönder
        return render(request, 'myapp/search_results.html', {'search_results': search_results, 'previous_searches': previous_searches})
    else:
        # POST olmayan istekler için önceki aramaları şablona gönder
        previous_searches = request.session.get('previous_searches', [])
        return render(request, 'myapp/home.html', {'previous_searches': previous_searches})


def search_results_sorted(request):
    if request.method == 'POST':
        sorting_criteria = request.POST.get('sorting', 'latest')  # Varsayılan olarak en sonu seç
        arama_kelimesi = request.POST.get('search_query')  # Arama kelimesini al

        # google_scholar_arama fonksiyonundan sonuçları al
        search_results = google_scholar_arama(arama_kelimesi)

        def safe_int(value, default=0):
            """Sayısal olmayan değerler için güvenli tamsayı dönüştürme."""
            try:
                return int(value)
            except (ValueError, TypeError):
                return default

        # Sıralama kriterine göre sonuçları sırala
        if sorting_criteria == 'latest':
            sorted_results = sorted(search_results, key=lambda x: safe_int(x.get('Tarih', "0")), reverse=True)
        elif sorting_criteria == 'oldest':
            sorted_results = sorted(search_results, key=lambda x: safe_int(x.get('Tarih', "0")))
        elif sorting_criteria == 'most_cited':
            sorted_results = sorted(search_results, key=lambda x: safe_int(x.get('Alinti', "0")), reverse=True)
        elif sorting_criteria == 'least_cited':
            sorted_results = sorted(search_results, key=lambda x: safe_int(x.get('Alinti', "0")))

        # Sıralanmış sonuçları şablona gönder
        return render(request, 'myapp/search_results.html', {'search_results': sorted_results})
    else:
        # GET isteği durumunda varsayılan eylem
        return render(request, 'myapp/search_results.html')
