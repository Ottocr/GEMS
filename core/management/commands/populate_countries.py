import json
import requests
from django.core.management.base import BaseCommand
from core.models.geo_models import Country, Continent

class Command(BaseCommand):
    help = 'Populate countries with geo data from Natural Earth'

    def handle(self, *args, **kwargs):
        # URL to the Natural Earth GeoJSON data
        url = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson'
        response = requests.get(url)
        data = response.json()

        for feature in data['features']:
            properties = feature['properties']
            country_name = properties['NAME']
            country_code = properties['ISO_A3']
            geo_data = feature['geometry']

            try:
                # Get or create the continent
                continent_name = properties['CONTINENT']
                continent, _ = Continent.objects.get_or_create(name=continent_name)

                # Create or update the country using the name as the unique identifier
                country, created = Country.objects.update_or_create(
                    name=country_name,  # Using country_name as the identifier
                    defaults={
                        'code': country_code,  # Still storing the country code
                        'geo_data': geo_data,  # Store as JSON
                        'continent': continent,
                    }
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f'Successfully created country: {country_name}'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'Successfully updated country: {country_name}'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to create/update country: {country_name}'))
                self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
