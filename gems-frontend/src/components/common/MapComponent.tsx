import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, GeoJSON, useMap } from 'react-leaflet';
import { Icon, GeoJSON as LeafletGeoJSON } from 'leaflet';
import { Box, Typography, Paper, useTheme } from '@mui/material';
import RiskLevelBadge from './RiskLevelBadge';
import { MapAsset, RiskLevel, GeoJSONFeatureCollection } from '../../types';
import 'leaflet/dist/leaflet.css';

interface MapComponentProps {
  assets: MapAsset[];
  countries?: GeoJSONFeatureCollection;
  selectedCountry?: string;
  height?: string | number;
  onAssetClick?: (assetId: number) => void;
  onCountryClick?: (countryCode: string) => void;
  initialCenter?: [number, number];
  initialZoom?: number;
  autoBounds?: boolean;
}

// Default center coordinates (0°N 0°E - null island)
const DEFAULT_CENTER: [number, number] = [0, 0];
const DEFAULT_ZOOM = 2;

// Custom marker icon based on risk level
const createMarkerIcon = (riskLevel: RiskLevel, theme: any) => {
  const colors = {
    CRITICAL: theme.palette.error.main,
    HIGH: theme.palette.warning.main,
    MEDIUM: theme.palette.info.main,
    LOW: theme.palette.success.main,
  };

  return new Icon({
    iconUrl: `data:image/svg+xml;base64,${btoa(`
      <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="16" cy="16" r="12" fill="${colors[riskLevel]}" fill-opacity="0.2"/>
        <circle cx="16" cy="16" r="8" fill="${colors[riskLevel]}"/>
      </svg>
    `)}`,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -16],
  });
};

// Component to handle auto-fitting bounds
const BoundsHandler: React.FC<{ assets: MapAsset[] }> = ({ assets }) => {
  const map = useMap();

  useEffect(() => {
    if (assets.length > 0) {
      try {
        const bounds = assets.reduce((acc, asset) => {
          acc.extend([asset.latitude, asset.longitude]);
          return acc;
        }, map.getBounds());
        map.fitBounds(bounds, { padding: [50, 50], animate: true });
      } catch (error) {
        console.error('Error fitting bounds:', error);
      }
    }
  }, [assets, map]);

  return null;
};

const MapComponent: React.FC<MapComponentProps> = ({
  assets,
  countries,
  selectedCountry,
  height = '400px',
  onAssetClick,
  onCountryClick,
  initialCenter,
  initialZoom,
  autoBounds = true,
}) => {
  const theme = useTheme();
  const [hoveredCountry, setHoveredCountry] = useState<string | null>(null);
  const [processedGeoJSON, setProcessedGeoJSON] = useState<GeoJSONFeatureCollection | null>(null);

  // Use provided coordinates or fall back to defaults
  const center = initialCenter && !isNaN(initialCenter[0]) && !isNaN(initialCenter[1])
    ? initialCenter
    : DEFAULT_CENTER;
  
  const zoom = initialZoom || DEFAULT_ZOOM;

  const getRiskColor = (score: number): string => {
    if (score >= 8) return theme.palette.error.main;
    if (score >= 6) return theme.palette.warning.main;
    if (score >= 4) return theme.palette.info.main;
    return theme.palette.success.main;
  };

  const countryStyle = (feature: any) => {
    const isSelected = selectedCountry === feature.properties?.code;
    const isHovered = hoveredCountry === feature.properties?.code;
    const riskScore = feature.properties?.avg_bta_score || 5;
    const baseColor = getRiskColor(riskScore);

    return {
      fillColor: baseColor,
      weight: isSelected || isHovered ? 2 : 1,
      opacity: 1,
      color: theme.palette.primary.main,
      fillOpacity: isSelected ? 0.4 : isHovered ? 0.3 : 0.2,
    };
  };

  const onEachCountry = (feature: any, layer: any) => {
    if (!feature.properties) return;

    const countryName = feature.properties.name || 'Unknown Country';
    const riskScore = feature.properties.avg_bta_score;
    const btaScores = feature.properties.bta_scores || [];

    // Create popup content
    const popupContent = `
      <div style="min-width: 200px;">
        <h4 style="margin: 0 0 8px 0;">${countryName}</h4>
        <p style="margin: 0 0 8px 0;">Average Risk Score: ${riskScore?.toFixed(1) || 'N/A'}</p>
        ${btaScores.map((score: any) => `
          <div style="margin: 4px 0;">
            <strong>${score.risk_group}:</strong> ${score.bta_score.toFixed(1)}
          </div>
        `).join('')}
      </div>
    `;

    layer.bindPopup(popupContent);

    layer.on({
      mouseover: () => setHoveredCountry(feature.properties.code),
      mouseout: () => setHoveredCountry(null),
      click: () => onCountryClick && feature.properties.code && 
        onCountryClick(feature.properties.code),
    });
  };

  // Process GeoJSON data when it changes
  useEffect(() => {
    if (!countries) {
      setProcessedGeoJSON(null);
      return;
    }

    try {
      // Create a deep copy to avoid mutating props
      const processedData = JSON.parse(JSON.stringify(countries));

      // Ensure each feature has the correct structure
      processedData.features = processedData.features.map((feature: any) => {
        // If the feature is just a geometry (no type/properties), wrap it
        if (!feature.type && feature.coordinates) {
          return {
            type: 'Feature',
            geometry: {
              type: feature.type || 'MultiPolygon',
              coordinates: feature.coordinates
            },
            properties: feature.properties || {}
          };
        }
        return feature;
      });

      setProcessedGeoJSON(processedData);
    } catch (error) {
      console.error('Error processing GeoJSON:', error);
      setProcessedGeoJSON(null);
    }
  }, [countries]);

  return (
    <Paper
      sx={{
        height,
        width: '100%',
        overflow: 'hidden',
        borderRadius: 3,
        boxShadow: theme.shadows[4],
      }}
    >
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height: '100%', width: '100%' }}
        zoomControl={false}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        
        {processedGeoJSON && (
          <GeoJSON
            key={`geojson-${selectedCountry || 'all'}-${hoveredCountry || 'none'}`}
            data={processedGeoJSON}
            style={countryStyle}
            onEachFeature={onEachCountry}
          />
        )}

        {assets.map((asset) => (
          <Marker
            key={asset.id}
            position={[asset.latitude, asset.longitude]}
            icon={createMarkerIcon(asset.riskLevel, theme)}
            eventHandlers={{
              click: () => onAssetClick && onAssetClick(asset.id),
            }}
          >
            <Popup>
              <Box sx={{ minWidth: 200, p: 1 }}>
                <Typography variant="h6" gutterBottom>
                  {asset.name}
                </Typography>
                {asset.description && (
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    {asset.description}
                  </Typography>
                )}
                <Box sx={{ mt: 1, display: 'flex', gap: 1, alignItems: 'center' }}>
                  <RiskLevelBadge 
                    level={asset.riskLevel} 
                    score={asset.riskScore}
                    showScore={true}
                  />
                </Box>
              </Box>
            </Popup>
          </Marker>
        ))}

        {autoBounds && assets.length > 0 && <BoundsHandler assets={assets} />}
      </MapContainer>
    </Paper>
  );
};

export default MapComponent;
