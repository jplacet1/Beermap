from django.shortcuts import render
from .models import Cervejaria, CervejariaImagem, Avaliacao, Localizacao, Contato
from django.db import models
from django.contrib import messages
from django.http import HttpResponse
from django.http import JsonResponse
import json
from django.shortcuts import  get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.views.decorators.csrf import csrf_exempt
from .utils import haversine
import re
from django.core.management.base import BaseCommand
from django import forms
from .forms import CervejariaForm, ContatoForm
from django.utils.text import slugify
from django.contrib.auth import authenticate, login as auth_login
from django.forms import modelformset_factory


@login_required
def adicionar_cervejaria(request):
    if request.method == 'GET':
        return render(request, 'adicionar_cervejaria.html')

    elif request.method == 'POST':
        nome = request.POST.get('nome')
        logradouro = request.POST.get('logradouro')
        numero = request.POST.get('numero')
        bairro = request.POST.get('bairro')
        cidade = request.POST.get('cidade')
        estado = request.POST.get('estado')
        mapa_embed = request.POST.get('mapa_embed')
        imagens = request.FILES.getlist('imagens')
        foto_principal = request.FILES.get('foto_principal')

        cervejaria = Cervejaria.objects.create(
            nome=nome,
            logradouro=logradouro,
            numero=numero,
            bairro=bairro,
            cidade=cidade,
            estado=estado,
            mapa_embed=mapa_embed,
            foto_principal=foto_principal,
            dono=request.user
        )

        for imagem in imagens:
            CervejariaImagem.objects.create(
                cervejaria=cervejaria,
                imagem=imagem
            )

        messages.success(request, 'Cervejaria criada com sucesso!')
        return render(request, 'adicionar_cervejaria.html')


def cadastro(request):
    if request.method == 'GET':
        return render(request, 'cadastro.html')
    else:
        username = request.POST.get('username')
        email = request.POST.get('email')
        senha = request.POST.get('senha')
        
        if User.objects.filter(username=username).exists():
            return HttpResponse('Nome já usado')
        
        user = User.objects.create_user(username=username, email=email, password=senha)
        user.save()
        
        return render(request, 'login.html')



def logar(request):
    if request.method == 'GET':
        return render(request, 'login.html')
    else:
        username=request.POST.get('username')
        senha=request.POST.get('senha')

        user= authenticate(username=username, password=senha)

        if user:
            auth_login(request, user)
            return redirect('home')
        else:
            erro = 'Usuário ou senha incorretos.'
            return render(request, 'login.html', {'erro': erro})


def calcula_media():
    media = Avaliacao.objects.aggregate(media_nota=Avg('nota'))['media_nota']
    if media is not None:
        print(f'Média geral das avaliações: {media:.2f}')
    else:
        print('Ainda não há avaliações cadastradas.')



def home(request):
    cervejarias_ordenadas = []
    cervejarias = Cervejaria.objects.all()
    if request.method == 'POST':
        try:
            usuario_lat = float(request.POST.get('latitude'))
            usuario_lon = float(request.POST.get('longitude'))
        except (TypeError, ValueError):
            cervejarias_ordenadas = []

    context = {
        'cervejarias_ordenadas': cervejarias_ordenadas,
        'cervejarias' : cervejarias
    }
    return render(request, 'home.html', context)



@login_required
def cervejaria(request, slug):
    cervejaria = get_object_or_404(Cervejaria, slug=slug)

    if request.method == 'POST':
        nota = request.POST.get('nota')
        comentario = request.POST.get('comentario')

        try:
            nota_int = int(nota)
            if nota_int not in range(1, 6):
                raise ValueError("Nota fora do intervalo permitido")

            # Cria a avaliação e salva no banco
            Avaliacao.objects.create(
                cervejaria=cervejaria,
                usuario=request.user,
                nota=nota_int,
                comentario=comentario or ''
            )
            return redirect('cervejaria', slug=slug)

        except (TypeError, ValueError) as e:
            print("Erro ao processar a nota:", e)
        except Exception as e:
            print("Erro ao salvar avaliação:", e)
            
    avaliacoes = cervejaria.avaliacoes.select_related('usuario').all()
    media = Avaliacao.objects.filter(cervejaria=cervejaria).aggregate(media_nota=Avg('nota'))['media_nota']
    if media is not None:
        print(f'Média geral das avaliações: {media:.2f}')
    else:
        print('Ainda não há avaliações cadastradas.')

    return render(request, 'detail.html', {
        'cervejaria': cervejaria,
        'avaliacoes': avaliacoes,
        'media':media
    })


def salvarloc(request):
    if request.method == 'POST':

        loc = json.loads(request.body)
        latitude_usuario = loc.get('latitude')
        longitude_usuario = loc.get('longitude')

        print(f"Latitude recebida: {latitude_usuario}, Longitude recebida: {longitude_usuario}")

        distancias = []  # ✅ Inicializa antes do loop

        for cervejaria in Localizacao.objects.all():
            distancia = haversine(
                cervejaria.latitude, 
                cervejaria.longitude, 
                float(latitude_usuario), 
                float(longitude_usuario)
            )
            distancias.append({
                'id': cervejaria.id,
                'nome': cervejaria.cervejaria.nome,
                'distancia': distancia
            })

        response = {'status': 'ok', 'distancias': distancias}
        print("Resposta JSON que será enviada:", response)  # <<<<<<<<<<<<<<<<<

        return JsonResponse(response)
    else:
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    

def extrair_localizacao():
    cervejarias = Cervejaria.objects.all()
    total = cervejarias.count()
    atualizados = 0

    for c in cervejarias:
        if not c.mapa_embed:
            print(f"{c.nome} sem iframe, pulando...")
            continue

        src_match = re.search(r'src="([^"]+)"', c.mapa_embed)
        if not src_match:
            print(f"{c.nome}: iframe sem src válido, pulando...")
            continue

        src = src_match.group(1)

        lat_match = re.search(r'!3d(-?\d+\.\d+)', src)
        lon_match = re.search(r'!2d(-?\d+\.\d+)', src)

        if lat_match and lon_match:
            lat = float(lat_match.group(1))
            lon = float(lon_match.group(1))

            loc, created = Localizacao.objects.update_or_create(
                cervejaria=c,
                defaults={'latitude': lat, 'longitude': lon}
            )

            status = "Criado" if created else "Atualizado"
            print(f"{status} localização para {c.nome}: ({lat}, {lon})")
            atualizados += 1
        else:
            print(f"{c.nome}: não encontrou lat/lon no src")

    print(f"Processado {total} cervejarias, {atualizados} localizações atualizadas.")


@login_required
def editar_cervejaria(request, slug):
    cervejaria = get_object_or_404(Cervejaria, slug=slug)
    ContatoFormSet = modelformset_factory(Contato, form=ContatoForm, extra=1, can_delete=True)

    if request.method == 'POST':
        form = CervejariaForm(request.POST, request.FILES, instance=cervejaria, user=request.user)
        formset = ContatoFormSet(request.POST, queryset=Contato.objects.filter(cervejaria=cervejaria))
        if form.is_valid() and formset.is_valid():
            cervejaria = form.save(commit=False)
            user_id = request.user.id
            # Slug automático
            base_slug = slugify(cervejaria.nome)
            slug_unico = base_slug
            contador = 1
            while Cervejaria.objects.exclude(id=cervejaria.id).filter(slug=slug_unico).exists():
                slug_unico = f"{base_slug}-{contador}"
                contador += 1
            cervejaria.slug = slug_unico

            cervejaria.save()

            # salvar contatos
            contatos = formset.save(commit=False)
            for contato in contatos:
                contato.cervejaria = cervejaria
                contato.save()
            # deletar contatos marcados para remoção
            for contato in formset.deleted_objects:
                contato.delete()

            return redirect('home')

    else:
        form = CervejariaForm(instance=cervejaria, user=request.user)
        formset = ContatoFormSet(queryset=Contato.objects.filter(cervejaria=cervejaria))

    return render(request, 'editar_cervejaria.html', {'form': form, 'formset': formset})