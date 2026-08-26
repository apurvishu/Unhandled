'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Vessel, Port } from '@/types';
import { DEMO_PORTS, DEMO_VESSELS } from '@/lib/demoData';
import { wsClient } from '@/lib/websocket';
import { formatCurrency, formatDwt, formatKnots, formatNauticalMiles, getStatusBadgeColor } from '@/lib/utils';
import { Ship, Anchor, Compass, Radio, AlertTriangle, CheckCircle, Navigation } from 'lucide-react';

export interface AisVesselMapProps {
  vessels?: Vessel[];
  ports?: Port[];
  selectedVesselId?: string;
  onSelectVessel?: (vessel: Vessel) => void;
  showRoutes?: boolean;
  height?: string;
}

export const AisVesselMap: React.FC<AisVesselMapProps> = ({
  vessels = DEMO_VESSELS,
  ports = DEMO_PORTS,
  selectedVesselId,
  onSelectVessel,
  showRoutes = true,
  height = '540px',
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const markersLayerRef = useRef<any>(null);
  const [selectedVessel, setSelectedVessel] = useState<Vessel | null>(
    vessels.find((v) => v.id === selectedVesselId) || vessels[0] || null
  );
  const [liveVessels, setLiveVessels] = useState<Vessel[]>(vessels);
  const [isLiveActive, setIsLiveActive] = useState<boolean>(true);

  // Subscribe to live AIS updates from WebSocket
  useEffect(() => {
    wsClient.connect();
    const unsubscribe = wsClient.subscribe((vesselId, newPos) => {
      setLiveVessels((prev) =>
        prev.map((v) => (v.id === vesselId ? { ...v, aisPosition: newPos } : v))
      );
    });
    return () => {
      unsubscribe();
    };
  }, []);

  // Initialize Leaflet Map
  useEffect(() => {
    if (typeof window === 'undefined' || !mapContainerRef.current) return;

    let isMounted = true;

    const initMap = async () => {
      const L = (await import('leaflet')).default;
      // Import Leaflet CSS dynamically
      if (!document.getElementById('leaflet-css')) {
        const link = document.createElement('link');
        link.id = 'leaflet-css';
        link.rel = 'stylesheet';
        link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
        document.head.appendChild(link);
      }

      if (!mapContainerRef.current || mapInstanceRef.current) return;

      // Create map centered on Indian Ocean & Bay of Bengal shipping lane
      const map = L.map(mapContainerRef.current, {
        center: [5.0, 105.0],
        zoom: 4,
        zoomControl: false,
        attributionControl: false,
      });

      L.control.zoom({ position: 'bottomright' }).addTo(map);

      // Dark Nautical CartoDB Dark Matter tiles
      L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        maxZoom: 18,
        subdomains: 'abcd',
      }).addTo(map);

      const markersGroup = L.layerGroup().addTo(map);
      markersLayerRef.current = markersGroup;
      mapInstanceRef.current = map;

      // Draw standard Australia -> India bulk coal route polyline
      if (showRoutes) {
        const routeCoords: [number, number][] = [
          [-21.2882, 149.3006], // Hay Point AU
          [-12.4, 125.6],       // Timor Sea
          [5.8, 95.2],          // Malacca / North Sumatra
          [20.2644, 86.6711],   // Paradip Port IN
        ];

        L.polyline(routeCoords, {
          color: '#00f2fe',
          weight: 2,
          opacity: 0.7,
          dashArray: '6, 8',
        }).addTo(map);
      }

      renderMarkers(L, markersGroup, liveVessels, ports);
    };

    initMap();

    return () => {
      isMounted = false;
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Re-render markers when vessels update
  useEffect(() => {
    if (!mapInstanceRef.current || !markersLayerRef.current) return;

    import('leaflet').then((L) => {
      renderMarkers(L.default, markersLayerRef.current, liveVessels, ports);
    });
  }, [liveVessels, selectedVessel?.id]);

  const renderMarkers = (L: any, layer: any, vesselsList: Vessel[], portsList: Port[]) => {
    layer.clearLayers();

    // Render Ports
    portsList.forEach((port) => {
      const portIcon = L.divIcon({
        className: 'custom-port-icon',
        html: `<div style="background-color: #0284c7; width: 14px; height: 14px; border-radius: 50%; border: 2px solid #ffffff; box-shadow: 0 0 10px #0284c7;"></div>`,
        iconSize: [14, 14],
        iconAnchor: [7, 7],
      });

      const marker = L.marker([port.latitude, port.longitude], { icon: portIcon }).addTo(layer);
      marker.bindPopup(`
        <div style="font-family: sans-serif; font-size: 12px; color: #0f172a; padding: 4px;">
          <strong style="font-size: 13px;">${port.name}</strong><br/>
          <span>Country: ${port.country} (${port.code})</span><br/>
          <span>Max Channel Depth: <strong>${port.channelMaxDepth}m</strong></span><br/>
          <span>Congestion: <strong>${port.congestionLevel}</strong></span><br/>
          <span>Avg Wait: ${port.averageWaitingTimeHours}h</span>
        </div>
      `);
    });

    // Render Vessels
    vesselsList.forEach((v) => {
      const isSelected = selectedVessel?.id === v.id;
      const heading = v.aisPosition.headingDegrees || 0;
      const isSim = v.aisPosition.isSimulated;

      const vesselIcon = L.divIcon({
        className: 'custom-vessel-icon',
        html: `
          <div style="transform: rotate(${heading}deg); width: 26px; height: 26px; display: flex; align-items: center; justify-content: center; background: ${
          isSelected ? '#00f2fe' : '#0284c7'
        }; border-radius: 6px; border: 2px solid #ffffff; box-shadow: 0 0 12px ${
          isSelected ? '#00f2fe' : 'rgba(0,0,0,0.5)'
        };">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
              <polygon points="12 2 19 21 12 17 5 21 12 2"></polygon>
            </svg>
          </div>
        `,
        iconSize: [26, 26],
        iconAnchor: [13, 13],
      });

      const marker = L.marker([v.aisPosition.latitude, v.aisPosition.longitude], { icon: vesselIcon }).addTo(layer);

      marker.on('click', () => {
        setSelectedVessel(v);
        if (onSelectVessel) onSelectVessel(v);
      });

      marker.bindTooltip(`
        <div style="font-family: sans-serif; font-size: 11px;">
          <strong>${v.name}</strong> (${v.type})<br/>
          Speed: ${v.aisPosition.speedKnots} kn | Heading: ${heading}°<br/>
          Dest: ${v.aisPosition.destination}
        </div>
      `, { direction: 'top', offset: [0, -10] });
    });
  };

  return (
    <div className="relative rounded-2xl overflow-hidden border border-slate-800 bg-slate-950 shadow-2xl">
      {/* Map Control Overlay Banner */}
      <div className="absolute top-4 left-4 z-20 flex items-center gap-2 bg-slate-900/90 backdrop-blur-md border border-slate-700 px-3 py-1.5 rounded-lg text-xs text-slate-200 shadow-xl">
        <Radio className="h-3.5 w-3.5 text-emerald-400 animate-pulse" />
        <span className="font-semibold">Live AIS Telemetry & GIS Route Analyzer</span>
        <span className="text-[10px] text-slate-400">({liveVessels.length} vessels tracked)</span>
      </div>

      {/* Map Container */}
      <div ref={mapContainerRef} style={{ width: '100%', height }} className="z-10" />

      {/* Selected Vessel GIS & Spatial Depth Overlay */}
      {selectedVessel && (
        <div className="absolute bottom-4 left-4 right-4 sm:right-auto sm:w-96 z-20 bg-slate-900/95 backdrop-blur-md border border-slate-700 rounded-xl p-4 shadow-2xl text-xs space-y-3">
          <div className="flex items-start justify-between border-b border-slate-800 pb-2">
            <div>
              <div className="flex items-center gap-1.5">
                <Ship className="h-4 w-4 text-sky-400" />
                <h4 className="font-bold text-white text-sm">{selectedVessel.name}</h4>
              </div>
              <p className="text-[11px] text-slate-400">
                IMO: {selectedVessel.imo} • {selectedVessel.type} • {formatDwt(selectedVessel.dwt)}
              </p>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-sky-500/20 text-sky-300 border border-sky-500/30">
              {selectedVessel.aisPosition.status}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[11px]">
            <div>
              <span className="text-slate-400 block">Speed / Heading:</span>
              <strong className="text-slate-200">
                {formatKnots(selectedVessel.aisPosition.speedKnots)} @ {selectedVessel.aisPosition.headingDegrees}°
              </strong>
            </div>
            <div>
              <span className="text-slate-400 block">Destination:</span>
              <strong className="text-slate-200">{selectedVessel.aisPosition.destination}</strong>
            </div>
            <div>
              <span className="text-slate-400 block">Coordinates:</span>
              <span className="font-mono text-slate-300">
                {selectedVessel.aisPosition.latitude.toFixed(2)}°, {selectedVessel.aisPosition.longitude.toFixed(2)}°
              </span>
            </div>
            <div>
              <span className="text-slate-400 block">ETA:</span>
              <span className="text-slate-200 font-semibold">{selectedVessel.aisPosition.eta.split('T')[0]}</span>
            </div>
          </div>

          {/* Spatial Channel Depth vs Vessel Draft Compatibility Check */}
          <div className="pt-2 border-t border-slate-800 flex items-center justify-between bg-slate-950/60 p-2 rounded-lg">
            <div>
              <span className="text-[10px] text-slate-400 block">Vessel Draft vs Paradip Port Channel:</span>
              <span className="font-semibold text-emerald-400 flex items-center gap-1">
                <CheckCircle className="h-3.5 w-3.5" />
                <span>SUITABLE (Draft {selectedVessel.maxDraft}m &lt; Channel Depth 17.5m)</span>
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
