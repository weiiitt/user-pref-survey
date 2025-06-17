import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, LayersControl, Polyline } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import styles from '../styles/MapDisplay.module.css'; // Import CSS module
import L from 'leaflet';

// Import marker images using ES Module syntax
import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png';
import iconUrl from 'leaflet/dist/images/marker-icon.png';
import shadowUrl from 'leaflet/dist/images/marker-shadow.png';
import type { RouteResponse } from '../types/APIResponses';

// Fix for default marker icon issue with webpack
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: iconRetinaUrl,
    iconUrl: iconUrl,
    shadowUrl: shadowUrl,
});

interface MapDisplayProps {
    routes: RouteResponse[];
    center?: [number, number];
    zoom?: number;
    hoveredRoute?: string | null;
}

const MapDisplay: React.FC<MapDisplayProps> = ({ routes, center = [40.008279, -105.268985], zoom = 16, hoveredRoute }) => {
    // BaseLayer references for Layers control
    const { BaseLayer } = LayersControl;
    
    // Create icons inside the component to ensure CSS modules are loaded
    const [sourceIcon, setSourceIcon] = useState<L.Icon.Default | null>(null);
    const [destinationIcon, setDestinationIcon] = useState<L.Icon.Default | null>(null);

    useEffect(() => {
        // Create icons after component mounts to ensure CSS modules are ready
        const source = new L.Icon.Default({ 
            className: `${styles.leafletMarkerIcon} ${styles.sourceMarker}` 
        });
        const destination = new L.Icon.Default({ 
            className: `${styles.leafletMarkerIcon} ${styles.destinationMarker}` 
        });
        
        setSourceIcon(source);
        setDestinationIcon(destination);
    }, []);

    return (
        <MapContainer center={center} zoom={zoom} className={styles.mapContainer}>
            <LayersControl position="topright">
                <BaseLayer checked name="Satellite">
                    <TileLayer
                        attribution='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
                        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                    />
                </BaseLayer>
                <BaseLayer name="OpenStreetMap">
                    <TileLayer
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />
                </BaseLayer>
            </LayersControl>

            {routes.map((route: RouteResponse, index: number) => {
                const routeIdentifier = index === 0 ? 'option1' : 'option2';
                const isOtherHovered = hoveredRoute !== null && hoveredRoute !== routeIdentifier;
                const targetOpacity = isOtherHovered ? 0.1 : 0.9;

                // Define styling directly in pathOptions for colors and weights
                const casingStyle = index === 0 
                    ? {
                        color: '#0435D9',
                        weight: 10,
                        opacity: targetOpacity,
                      }
                    : {
                        color: '#B6470C',
                        weight: 10,
                        opacity: targetOpacity,
                      };
                
                const lineStyle = index === 0 
                    ? {
                        color: '#5076F3',
                        weight: 6,
                        opacity: targetOpacity,
                      }
                    : {
                        color: '#F07939',
                        weight: 6,
                        opacity: targetOpacity,
                      };

                return (
                    <React.Fragment key={index}>
                        {/* Casing Polyline (outline) */}
                        <Polyline
                            pathOptions={casingStyle}
                            positions={route.route.coordinates as [number, number][]}
                        />
                        {/* Main Polyline */}
                        <Polyline
                            pathOptions={lineStyle}
                            positions={route.route.coordinates as [number, number][]}
                        />
                    </React.Fragment>
                );
            })}

            {routes.length > 0 && sourceIcon && destinationIcon && (
                <>
                    <Marker position={routes[0].source.coordinates as [number, number]} icon={sourceIcon}>
                        <Popup>Source</Popup>
                    </Marker>
                    <Marker position={routes[0].destination.coordinates as [number, number]} icon={destinationIcon}>
                        <Popup>Destination</Popup>
                    </Marker>
                </>
            )}
        </MapContainer>
    );
};

export default MapDisplay;
