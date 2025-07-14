import re
from django.core.management.base import BaseCommand
from cervejarias.models import Cervejaria, Localizacao

class Command(BaseCommand):
    help = 'Extrai latitude e longitude do iframe e salva na model Localizacao'

    def handle(self, *args, **kwargs):
        cervejarias = Cervejaria.objects.all()
        total = cervejarias.count()
        atualizados = 0

        for c in cervejarias:
            if not c.mapa_embed:
                self.stdout.write(f"{c.nome} sem iframe, pulando...")
                continue

            src_match = re.search(r'src="([^"]+)"', c.mapa_embed)
            if not src_match:
                self.stdout.write(f"{c.nome}: iframe sem src válido, pulando...")
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
                self.stdout.write(f"{status} localização para {c.nome}: ({lat}, {lon})")
                atualizados += 1
            else:
                self.stdout.write(f"{c.nome}: não encontrou lat/lon no src")

        self.stdout.write(self.style.SUCCESS(f"Processado {total} cervejarias, {atualizados} localizações atualizadas."))
