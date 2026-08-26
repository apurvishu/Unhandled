import { APP_CONFIG } from '@/config/constants';
import { AisPosition } from '@/types';

type AisUpdateCallback = (vesselId: string, position: AisPosition) => void;

class MaritimeWebSocketClient {
  private socket: WebSocket | null = null;
  private listeners: Set<AisUpdateCallback> = new Set();
  private simulationInterval: NodeJS.Timeout | null = null;
  private isConnected = false;

  constructor() {
    // Initialized lazily
  }

  public connect(url: string = APP_CONFIG.wsBaseUrl) {
    if (typeof window === 'undefined') return;

    try {
      this.socket = new WebSocket(url);

      this.socket.onopen = () => {
        this.isConnected = true;
        console.log('[Maritime WS] Connected to live AIS telemetry channel');
        if (this.simulationInterval) {
          clearInterval(this.simulationInterval);
          this.simulationInterval = null;
        }
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'AIS_UPDATE') {
            this.notifyListeners(data.vesselId, data.position);
          }
        } catch (e) {
          console.error('[Maritime WS] Failed parsing message:', e);
        }
      };

      this.socket.onerror = () => {
        this.fallbackToSimulation();
      };

      this.socket.onclose = () => {
        this.isConnected = false;
        this.fallbackToSimulation();
      };
    } catch {
      this.fallbackToSimulation();
    }
  }

  private fallbackToSimulation() {
    if (this.simulationInterval) return;
    // Live simulation mode: updates vessel positions with tiny realistic drift every 4 seconds
    this.simulationInterval = setInterval(() => {
      const deltaLat = (Math.random() - 0.5) * 0.008;
      const deltaLng = (Math.random() - 0.5) * 0.008;
      const speed = 12.5 + (Math.random() - 0.5) * 1.5;

      const simUpdate: AisPosition = {
        latitude: -12.4 + deltaLat,
        longitude: 125.6 + deltaLng,
        speedKnots: Number(speed.toFixed(1)),
        headingDegrees: 298,
        status: 'Underway',
        destination: 'Paradip Port',
        eta: '2026-09-14T08:00:00Z',
        lastUpdated: new Date().toISOString(),
        isSimulated: true,
      };

      this.notifyListeners('vessel-02', simUpdate);
    }, 4000);
  }

  public subscribe(callback: AisUpdateCallback) {
    this.listeners.add(callback);
    return () => {
      this.listeners.delete(callback);
    };
  }

  private notifyListeners(vesselId: string, position: AisPosition) {
    this.listeners.forEach((cb) => cb(vesselId, position));
  }

  public disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    if (this.simulationInterval) {
      clearInterval(this.simulationInterval);
      this.simulationInterval = null;
    }
  }
}

export const wsClient = new MaritimeWebSocketClient();
