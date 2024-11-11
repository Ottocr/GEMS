from django.core.management.base import BaseCommand
from django.db import transaction
from core.models.geo_models import Country
from core.models.asset_models import Asset, AssetType

class Command(BaseCommand):
    help = 'Populate test assets in UK, France, and Italy'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        # Create security-focused asset types
        asset_types = {
            'Critical Infrastructure': 'High-security facilities requiring advanced physical and cyber protection',
            'Corporate Office': 'Business facilities with comprehensive security measures',
            'Data Center': 'IT infrastructure requiring advanced security controls',
            'Manufacturing Plant': 'Industrial facilities with perimeter and access control',
            'R&D Facility': 'Research centers with enhanced security for IP protection',
            'Distribution Hub': 'Logistics centers with secure storage and shipping'
        }

        created_types = {}
        for name, desc in asset_types.items():
            asset_type, created = AssetType.objects.get_or_create(
                name=name,
                defaults={'description': desc}
            )
            created_types[name] = asset_type
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created asset type: {name}'))

        # Test assets data with real coordinates
        test_assets = [
            # UK Assets
            {
                'name': 'London HQ',
                'type': 'Corporate Office',
                'country': 'United Kingdom',
                'description': 'Main corporate headquarters with executive offices and sensitive data processing',
                'latitude': 51.5074,
                'longitude': -0.1278
            },
            {
                'name': 'Manchester Data Center',
                'type': 'Data Center',
                'country': 'United Kingdom',
                'description': 'Primary data center for UK operations with critical data storage',
                'latitude': 53.4808,
                'longitude': -2.2426
            },
            {
                'name': 'Birmingham Manufacturing',
                'type': 'Manufacturing Plant',
                'country': 'United Kingdom',
                'description': 'Key manufacturing facility with sensitive industrial processes',
                'latitude': 52.4862,
                'longitude': -1.8904
            },
            # France Assets
            {
                'name': 'Paris Office Complex',
                'type': 'Corporate Office',
                'country': 'France',
                'description': 'Main European administrative center with secure meeting facilities',
                'latitude': 48.8566,
                'longitude': 2.3522
            },
            {
                'name': 'Lyon Research Center',
                'type': 'R&D Facility',
                'country': 'France',
                'description': 'Advanced research facility with secure laboratories',
                'latitude': 45.7640,
                'longitude': 4.8357
            },
            {
                'name': 'Marseille Port Facility',
                'type': 'Distribution Hub',
                'country': 'France',
                'description': 'Maritime logistics hub with secure cargo handling',
                'latitude': 43.2965,
                'longitude': 5.3698
            },
            # Italy Assets
            {
                'name': 'Milan Tech Center',
                'type': 'Critical Infrastructure',
                'country': 'Italy',
                'description': 'Critical technology infrastructure and operations center',
                'latitude': 45.4642,
                'longitude': 9.1900
            },
            {
                'name': 'Rome Data Operations',
                'type': 'Data Center',
                'country': 'Italy',
                'description': 'Secondary data center for Southern European operations',
                'latitude': 41.9028,
                'longitude': 12.4964
            },
            {
                'name': 'Turin Industrial Complex',
                'type': 'Manufacturing Plant',
                'country': 'Italy',
                'description': 'Advanced manufacturing facility with high-security requirements',
                'latitude': 45.0703,
                'longitude': 7.6869
            }
        ]

        # Set countries as company operated
        for country_name in ['United Kingdom', 'France', 'Italy']:
            try:
                country = Country.objects.get(name=country_name)
                country.company_operated = True
                country.save()
                self.stdout.write(self.style.SUCCESS(f'Updated {country_name} as company operated'))
            except Country.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Country not found: {country_name}. Please run populate_countries first.')
                )
                return

        # Create assets
        for asset_data in test_assets:
            try:
                country = Country.objects.get(name=asset_data['country'])
                asset_type = created_types[asset_data['type']]

                asset, created = Asset.objects.get_or_create(
                    name=asset_data['name'],
                    defaults={
                        'description': asset_data['description'],
                        'latitude': asset_data['latitude'],
                        'longitude': asset_data['longitude'],
                        'asset_type': asset_type,
                        'country': country,
                        'criticality_score': 5,  # Default mid-range score
                        'vulnerability_score': 5  # Default mid-range score
                    }
                )

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Created asset: {asset.name} in {country.name}')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'Asset already exists: {asset.name}')
                    )

            except Country.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Failed to create asset: {asset_data["name"]} - Country not found')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to create asset: {asset_data["name"]} - {str(e)}')
                )

        self.stdout.write(self.style.SUCCESS('Successfully populated test assets'))
