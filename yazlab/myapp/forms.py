from django import forms

class PublicationFilterForm(forms.Form):
    title = forms.CharField(required=False, label='Başlık')
    authors = forms.CharField(required=False, label='Yazarlar')
    citation_count = forms.IntegerField(required=False, label='Alıntı Sayısı')
    publication_year = forms.IntegerField(required=False, label='Yayımlanma Yılı')
