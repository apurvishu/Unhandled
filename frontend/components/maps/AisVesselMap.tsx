'use client';

import React, { useEffect, useRef } from 'react';
import { Vessel } from '@/types';
import { DEMO_VESSELS } from '@/lib/demoData';
import { formatKnots, formatDwt } from '@/lib/utils';
import 'leaflet/dist/leaflet.css';

interface AisVesselMapProps {
  vessels?: Vessel[];
  selectedVesselId?: string;
  height?: string;
  showRoutes?: boolean;
}

export const AisVesselMap: React.FC<AisVesselMapProps> = ({
  vessels = DEMO_VESSELS,
  selectedVesselId,
  height = '420px',
  showRoutes = true,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);

  useEffect(() => {
    if (typeof window === 'undefined' || !mapContainerRef.current) return;

    let map: any = null;

    import('leaflet').then((L) => {
      // If map already initialized on this container, clean up first
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }

      const selectedVessel = vessels.find((v) => v.id === selectedVesselId);
      const center: [number, number] = selectedVessel
        ? [selectedVessel.aisPosition.latitude, selectedVessel.aisPosition.longitude]
        : [14.0, 86.0]; // Bay of Bengal & Indian Ocean

      map = L.map(mapContainerRef.current!, {
        center,
        zoom: selectedVessel ? 5 : 4,
        zoomControl: true,
      });

      mapInstanceRef.current = map;

      // CartoDB Positron Light Tiles
      L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; CARTO',
        maxZoom: 18,
      }).addTo(map);

      // Add vessel markers
      vessels.forEach((v) => {
        const isSelected = v.id === selectedVesselId;
        const bgColor = isSelected ? '#ea580c' : '#18181b';

        const icon = L.divIcon({
          className: 'custom-vessel-marker',
          html: `
            <div style="
              width: 22px; 
              height: 22px; 
              background: ${bgColor}; 
              border: 1.5px solid #ffffff; 
              border-radius: 3px; 
              display: flex; 
              align-items: center; 
              justify-content: center; 
              transform: rotate(${v.aisPosition.headingDegrees}deg);
              box-shadow: 0 1px 3px rgba(0,0,0,0.3);
            ">
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="12 2 19 21 12 17 5 21 12 2"></polygon>
              </svg>
            </div>
          `,
          iconSize: [22, 22],
          iconAnchor: [11, 11],
        });

        const popupHtml = `
          <div style="font-family: monospace; font-size: 11px; line-height: 1.4; color: #18181b;">
            <div style="border-bottom: 1px solid #e4e4e7; padding-bottom: 4px; margin-bottom: 4px; font-weight: bold;">
              ${v.name} <span style="color: #71717a; font-weight: normal;">(IMO ${v.imo})</span>
            </div>
            <div>Class: <strong>${v.type}</strong> (${formatDwt(v.dwt)})</div>
            <div>Speed: <strong>${formatKnots(v.aisPosition.speedKnots)}</strong> @ ${v.aisPosition.headingDegrees}°</div>
            <div>Max Draft: <strong>${v.maxDraft}m</strong></div>
            <div>Destination: <strong>${v.aisPosition.destination}</strong></div>
            <div>ETA: <strong>${v.aisPosition.eta.split('T')[0]}</strong></div>
            <div style="margin-top: 6px; padding-top: 4px; border-top: 1px solid #f4f4f5;">
              <a href="/vessels/${v.id}" style="font-family: sans-serif; font-weight: 600; color: #000000; text-decoration: underline;">
                View Vessel Telemetry &rarr;
              </a>
            </div>
          </div>
        `;

        L.marker([v.aisPosition.latitude, v.aisPosition.longitude], { icon })
          .addTo(map)
          .bindPopup(popupHtml);
      });

      // Add navigation route line if selected
      if (showRoutes && selectedVessel) {
        L.polyline(
          [
            [selectedVessel.aisPosition.latitude, selectedVessel.aisPosition.longitude],
            [20.2644, 86.6698], // Paradip Port
          ],
          {
            color: '#18181b',
            weight: 2,
            dashArray: '4, 4',
          }
        ).addTo(map);
      }
    });

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [vessels, selectedVesselId, showRoutes]);

  return (
    <div className="relative w-full border border-zinc-200 rounded overflow-hidden shadow-sm" style={{ height }}>
      {/* Top Map Status Overlay */}
      <div className="absolute top-2.5 right-2.5 z-[1000] bg-white/95 border border-zinc-300 rounded px-2.5 py-1 text-[11px] font-mono text-zinc-800 shadow-sm flex items-center gap-2">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-600 animate-pulse" />
        <span>AIS LIVE FEED • {vessels.length} VESSELS</span>
      </div>

      <div ref={mapContainerRef} style={{ width: '100%', height: '100%' }} />
    </div>
  );
};
