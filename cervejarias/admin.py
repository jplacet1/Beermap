from django.contrib import admin
from .models import Cervejaria
from .models import CervejariaImagem
from .models import Avaliacao
from .models import Localizacao
from.models import Contato


admin.site.register(Cervejaria)
admin.site.register(CervejariaImagem)
admin.site.register(Avaliacao)
admin.site.register(Localizacao)
admin.site.register(Contato)