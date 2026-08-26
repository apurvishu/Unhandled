import { CommodityType, User, UserRole, VesselType } from '@/types';

export const APP_CONFIG = {
  name: 'SIH26006 Maritime Intelligence Platform',
  version: '2.0.0',
  apiBaseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  wsBaseUrl: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/api/v1/ws',
  defaultMapCenter: [15.0, 95.0] as [number, number], // Bay of Bengal / Indian Ocean region
  defaultZoom: 4,
};

export const COMMODITIES: CommodityType[] = [
  'Coking Coal',
  'Thermal Coal',
  'Iron Ore',
  'Bauxite',
  'Grain / Wheat',
  'Fertilizer',
  'Limestone',
  'Alumina',
];

export const VESSEL_TYPES: VesselType[] = [
  'Capesize',
  'Panamax',
  'Supramax',
  'Handymax',
  'Handysize',
  'VLCC',
  'Suezmax',
  'Aframax',
];

export const DEMO_USERS: Record<UserRole, User> = {
  PROCUREMENT_OFFICER: {
    id: 'usr-proc-01',
    name: 'Capt. Rajesh Sharma',
    email: 'procurement@steelcorp.com',
    role: 'PROCUREMENT_OFFICER',
    companyName: 'National Steel & Power Authority',
    companyType: 'Bulk Cargo Procurement Agency',
    createdAt: '2026-01-15T00:00:00Z',
  },
  SHIP_OWNER: {
    id: 'usr-ship-01',
    name: 'Elena Rostova',
    email: 'chartering@oceanicfreight.com',
    role: 'SHIP_OWNER',
    companyName: 'Oceanic Bulk Carrier Fleet Ltd',
    companyType: 'Ship Management & Carrier',
    createdAt: '2026-01-10T00:00:00Z',
  },
  PORT_OWNER: {
    id: 'usr-port-01',
    name: 'K. V. Ramakrishnan',
    email: 'operations@paradipport.gov.in',
    role: 'PORT_OWNER',
    companyName: 'Paradip Port Terminal Trust',
    companyType: 'Major Port Authority',
    createdAt: '2026-01-05T00:00:00Z',
  },
  ADMIN: {
    id: 'usr-admin-01',
    name: 'Platform Administrator',
    email: 'admin@maritime.ai',
    role: 'ADMIN',
    companyName: 'SIH26006 Maritime Control Center',
    companyType: 'System Administrator',
    createdAt: '2026-01-01T00:00:00Z',
  },
};

export const MAJOR_PORTS = [
  { id: 'port-paradip', name: 'Paradip Port', code: 'IN PRT', country: 'India', lat: 20.2644, lng: 86.6711, maxDepth: 17.5, maxDwt: 125000 },
  { id: 'port-visakhapatnam', name: 'Visakhapatnam Port', code: 'IN VTZ', country: 'India', lat: 17.6868, lng: 83.2185, maxDepth: 18.1, maxDwt: 200000 },
  { id: 'port-dhamra', name: 'Dhamra Port', code: 'IN DHA', country: 'India', lat: 20.8286, lng: 86.9747, maxDepth: 18.0, maxDwt: 180000 },
  { id: 'port-haypoint', name: 'Hay Point Coal Terminal', code: 'AU HPY', country: 'Australia', lat: -21.2882, lng: 149.3006, maxDepth: 19.5, maxDwt: 220000 },
  { id: 'port-newcastle', name: 'Port of Newcastle', code: 'AU NCL', country: 'Australia', lat: -32.9167, lng: 151.7833, maxDepth: 15.2, maxDwt: 110000 },
  { id: 'port-gladstone', name: 'Port of Gladstone', code: 'AU GLT', country: 'Australia', lat: -23.8431, lng: 151.2684, maxDepth: 16.3, maxDwt: 150000 },
  { id: 'port-singapore', name: 'Port of Singapore', code: 'SG SIN', country: 'Singapore', lat: 1.29027, lng: 103.851959, maxDepth: 20.0, maxDwt: 300000 },
  { id: 'port-rotterdam', name: 'Port of Rotterdam', code: 'NL RTM', country: 'Netherlands', lat: 51.9244, lng: 4.4777, maxDepth: 24.0, maxDwt: 350000 },
  { id: 'port-hedland', name: 'Port Hedland', code: 'AU PHE', country: 'Australia', lat: -20.3167, lng: 118.5833, maxDepth: 19.2, maxDwt: 260000 },
];
