# cervejarias/models.py
from django.db import models
from django.contrib.auth.models import User
import re


from django.db import models
from django.utils.text import slugify


class Cervejaria(models.Model):
    nome = models.CharField(max_length=100)
    cep = models.CharField(max_length=9)
    logradouro = models.CharField(max_length=100)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100, default='Recife')
    estado = models.CharField(max_length=100, default='PE')
    numero = models.CharField(max_length=10)
    mapa_embed = models.TextField(blank=True, null=True)
    descricao = models.TextField(blank=True, null=True, default='nada')
    foto_principal = models.ImageField(upload_to='cervejarias/')
    dono = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cervejarias')
    slug = models.SlugField(blank=True, unique=True)

    def save(self, *args, **kwargs):
        # Gera slug automaticamente, se estiver em branco
        if not self.slug:
            self.slug = slugify(self.nome)

        # Salva a Cervejaria primeiro
        super().save(*args, **kwargs)

        # Extração automática da localização (lat/lon) se houver mapa_embed
        if self.mapa_embed:
            src_match = re.search(r'src="([^"]+)"', self.mapa_embed)
            if src_match:
                src = src_match.group(1)
                lat_match = re.search(r'!3d(-?\d+\.\d+)', src)
                lon_match = re.search(r'!2d(-?\d+\.\d+)', src)

                if lat_match and lon_match:
                    from .models import Localizacao  # evitar import circular no topo
                    Localizacao.objects.update_or_create(
                        cervejaria=self,
                        defaults={
                            'latitude': float(lat_match.group(1)),
                            'longitude': float(lon_match.group(1)),
                        }
                    )


    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.nome)
            slug = base_slug
            contador = 1
            while Cervejaria.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{contador}"
                contador += 1
            self.slug = slug
        super().save(*args, **kwargs)


class CervejariaImagem(models.Model):
    cervejaria = models.ForeignKey(Cervejaria, related_name='imagens', on_delete=models.CASCADE)
    imagem = models.ImageField(upload_to='cervejarias/')
    def __str__(self):
        return f"Imagem da cervejaria {self.cervejaria.nome}"


class Avaliacao(models.Model):
    cervejaria = models.ForeignKey(Cervejaria, on_delete=models.CASCADE, related_name='avaliacoes')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='avaliacoes')
    nota = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comentario = models.TextField(blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)


class Localizacao(models.Model):
    cervejaria = models.OneToOneField(Cervejaria, on_delete=models.CASCADE, related_name='localizacao')
    latitude = models.FloatField()
    longitude = models.FloatField()
    def __str__(self):
        return f"{self.cervejaria.nome} - ({self.latitude}, {self.longitude})"
    

class Contato(models.Model):
    TIPOS = [
        ('telefone', 'Telefone'),
        ('email', 'E-mail'),
        ('whatsapp', 'WhatsApp'),
        ('site', 'Website'),
        ('instagram', 'Instagram'),
        ('linkedin', 'LinkedIn'),
    ]

    cervejaria = models.ForeignKey(Cervejaria, related_name='contatos', on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    valor = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.cervejaria.nome} - {self.tipo}: {self.valor}'