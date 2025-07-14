from django import forms
from .models import Cervejaria, Contato
from django.contrib.auth.models import User

class CervejariaForm(forms.ModelForm):
    class Meta:
        model = Cervejaria
        exclude = ['slug','dono','foto_principal']
        fields = [
            'nome', 'cep', 'logradouro', 'bairro', 'cidade', 'estado',
            'numero', 'mapa_embed', 'descricao',]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)


class ContatoForm(forms.ModelForm):
    class Meta:
        model = Contato
        fields = ['tipo', 'valor']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'valor': forms.TextInput(attrs={'class': 'form-control'}),
        }   