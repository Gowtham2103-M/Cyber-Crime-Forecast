import React, { useMemo, useEffect, useRef, useState } from 'react';
import Map, { Source, Layer, Marker, Popup } from 'react-map-gl/maplibre';
import type { MapRef } from 'react-map-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import type { PredictionResult, Hotspot } from './App';

interface MapComponentProps {
  heatmapData: any;
  predictionResult: PredictionResult | null;
}

const MAPTILER_KEY = import.meta.env.VITE_MAPTILER_KEY;

const MapComponent: React.FC<MapComponentProps> = ({ heatmapData, predictionResult }) => {
  const mapRef = useRef<MapRef>(null);
  const [selectedHotspot, setSelectedHotspot] = useState<Hotspot | null>(null);

  // Data-driven styling for the heatmap
  const heatmapLayerStyle: any = useMemo(() => ({
    id: 'risk-heatmap',
    type: 'heatmap',
    paint: {
      // Increase weight based on risk_intensity
      'heatmap-weight': [
        'interpolate',
        ['linear'],
        ['get', 'risk_intensity'],
        0, 0,
        1, 1
      ],
      // Color ramp: cool to warm (red for high risk)
      'heatmap-color': [
        'interpolate',
        ['linear'],
        ['heatmap-density'],
        0, 'rgba(33,102,172,0)',
        0.2, 'rgb(103,169,207)',
        0.4, 'rgb(209,229,240)',
        0.6, 'rgb(253,219,199)',
        0.8, 'rgb(239,138,98)',
        1, 'rgb(178,24,43)'
      ],
      'heatmap-radius': [
        'interpolate',
        ['linear'],
        ['zoom'],
        0, 2,
        9, 20
      ],
      'heatmap-opacity': 0.8
    }
  }), []);

  // When a prediction is made, fly to the first hotspot
  useEffect(() => {
    if (predictionResult && predictionResult.predicted_hotspots.length > 0 && mapRef.current) {
      const topHotspot = predictionResult.predicted_hotspots[0];
      mapRef.current.flyTo({
        center: [topHotspot.longitude, topHotspot.latitude],
        zoom: 8,
        duration: 2000
      });
    }
  }, [predictionResult]);

  return (
    <Map
      ref={mapRef}
      initialViewState={{
        longitude: 78.9629,
        latitude: 20.5937,
        zoom: 4
      }}
      mapStyle={`https://api.maptiler.com/maps/streets-v2/style.json?key=${MAPTILER_KEY}`}
      style={{ width: '100%', height: '100%' }}
    >
      {heatmapData && (
        <Source type="geojson" data={heatmapData}>
          <Layer {...heatmapLayerStyle} />
        </Source>
      )}

      {/* Render Markers for Predicted Hotspots if available */}
      {predictionResult && predictionResult.predicted_hotspots.map((hotspot, idx) => (
        <Marker 
          key={hotspot.terminal_id} 
          longitude={hotspot.longitude} 
          latitude={hotspot.latitude}
          anchor="bottom"
          onClick={(e) => {
            e.originalEvent.stopPropagation();
            setSelectedHotspot(hotspot);
          }}
        >
          <div className="relative group cursor-pointer">
            {/* Pulsing effect for the top hotspot */}
            {idx === 0 && (
              <div className="absolute -inset-2 rounded-full bg-red-500 opacity-40 animate-ping"></div>
            )}
            <div className="w-6 h-6 bg-red-600 rounded-full border-2 border-white shadow-lg flex items-center justify-center text-xs font-bold relative z-10">
              {idx + 1}
            </div>
          </div>
        </Marker>
      ))}

      {selectedHotspot && (
        <Popup
          longitude={selectedHotspot.longitude}
          latitude={selectedHotspot.latitude}
          onClose={() => setSelectedHotspot(null)}
          closeOnClick={false}
          className="rounded-lg shadow-xl"
        >
          <div className="p-1">
            <h3 className="font-bold text-sm text-slate-900">{selectedHotspot.terminal_id}</h3>
            <div className="mt-2 pt-2 border-t border-slate-600/50">
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-400">Expected Loss:</span>
                <span className="text-red-400 font-medium">
                  ₹{selectedHotspot.expected_cashout_amount.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </span>
              </div>
            </div>

            {/* AI Explainability Panel */}
            {selectedHotspot.explanation && (
              <div className="mt-3 p-2 bg-slate-800/80 rounded border border-blue-500/30">
                <div className="text-[10px] uppercase tracking-wider text-blue-400 mb-1.5 font-semibold">AI Risk Breakdown</div>
                
                <div className="space-y-1.5 mb-2">
                  <div className="flex items-center text-xs">
                    <div className="w-20 text-slate-400">Network:</div>
                    <div className="flex-1 bg-slate-700 h-1.5 rounded-full overflow-hidden">
                      <div className="bg-purple-500 h-full" style={{width: `${selectedHotspot.explanation.network_link_pct}%`}}></div>
                    </div>
                    <div className="w-8 text-right text-slate-300 text-[10px]">{selectedHotspot.explanation.network_link_pct}%</div>
                  </div>
                  
                  <div className="flex items-center text-xs">
                    <div className="w-20 text-slate-400">Spatial KDE:</div>
                    <div className="flex-1 bg-slate-700 h-1.5 rounded-full overflow-hidden">
                      <div className="bg-blue-500 h-full" style={{width: `${selectedHotspot.explanation.baseline_spatial_pct}%`}}></div>
                    </div>
                    <div className="w-8 text-right text-slate-300 text-[10px]">{selectedHotspot.explanation.baseline_spatial_pct}%</div>
                  </div>
                  
                  <div className="flex items-center text-xs">
                    <div className="w-20 text-slate-400">Temporal:</div>
                    <div className="flex-1 bg-slate-700 h-1.5 rounded-full overflow-hidden">
                      <div className="bg-orange-500 h-full" style={{width: `${selectedHotspot.explanation.recent_activity_pct}%`}}></div>
                    </div>
                    <div className="w-8 text-right text-slate-300 text-[10px]">{selectedHotspot.explanation.recent_activity_pct}%</div>
                  </div>
                </div>

                <div className="space-y-1">
                  {selectedHotspot.explanation.details.map((detail: string, i: number) => (
                    <div key={i} className="text-[10px] text-slate-300 leading-tight flex items-start">
                      <span className="text-blue-400 mr-1.5">•</span>
                      <span>{detail}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Popup>
      )}
    </Map>
  );
};

export default MapComponent;
