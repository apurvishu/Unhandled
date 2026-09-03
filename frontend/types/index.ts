// SIH26006 Intelligent Maritime Logistics Platform Types

export type UserRole = 'PORT_OWNER' | 'SHIP_OWNER' | 'PROCUREMENT_OFFICER' | 'ADMIN';

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  companyName?: string;
  companyType?: string;
  avatarUrl?: string;
  createdAt: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  expiresIn: number;
}

export interface AuthResponse {
  user: User;
  tokens: AuthTokens;
}

// Vessel Specifications & AIS
export type VesselType = 'Capesize' | 'Panamax' | 'Supramax' | 'Handymax' | 'Handysize' | 'VLCC' | 'Suezmax' | 'Aframax';
export type VesselStatus = 'Underway' | 'At Anchor' | 'Moored' | 'Awaiting Berth' | 'Loading' | 'Discharging' | 'Maintenance';

export interface AisPosition {
  latitude: number;
  longitude: number;
  speedKnots: number;
  headingDegrees: number;
  status: VesselStatus;
  destination: string;
  eta: string;
  lastUpdated: string;
  isSimulated?: boolean;
}

export interface Vessel {
  id: string;
  name: string;
  imo: string;
  mmsi: string;
  type: VesselType;
  dwt: number; // Deadweight Tonnage
  loa: number; // Length Overall (m)
  beam: number; // Beam Width (m)
  maxDraft: number; // Max Draft (m)
  currentDraft: number; // Current Draft (m)
  yearBuilt: number;
  flag: string;
  ownerId: string;
  ownerName: string;
  isAvailable: boolean;
  availableFrom: string;
  currentPortId?: string;
  currentPortName?: string;
  aisPosition: AisPosition;
  dailyCharterRateUsd: number;
  fuelConsumptionMtPerDay: number;
}

// Port & Berth Infrastructure
export interface Berth {
  id: string;
  berthNumber: string;
  name: string;
  maxLoa: number;
  maxDraft: number;
  status: 'OCCUPIED' | 'AVAILABLE' | 'MAINTENANCE';
  currentVesselId?: string;
  currentVesselName?: string;
  cargoType?: string;
  cargoQuantityMt?: number;
  expectedDeparture?: string;
  occupancyPercent: number;
}

export interface Port {
  id: string;
  name: string;
  code: string; // UN/LOCODE
  country: string;
  latitude: number;
  longitude: number;
  channelMaxDepth: number; // Depth in meters
  maxVesselDwt: number;
  berthsCount: number;
  berths: Berth[];
  currentVesselsInPort: number;
  vesselsInQueue: number;
  averageWaitingTimeHours: number;
  congestionLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  berthUtilizationPercent: number;
}

// Bulk Cargo Requirements
export type CommodityType = 
  | 'Coking Coal' 
  | 'Thermal Coal' 
  | 'Iron Ore' 
  | 'Bauxite' 
  | 'Grain / Wheat' 
  | 'Fertilizer' 
  | 'Limestone' 
  | 'Alumina';

export interface CargoRequirement {
  id: string;
  procurementOfficerId: string;
  procurementOfficerName: string;
  commodity: CommodityType;
  quantityMt: number;
  originPortId: string;
  originPortName: string;
  destinationPortId: string;
  destinationPortName: string;
  requiredArrivalDate: string;
  preferredVesselType: VesselType;
  minDwt: number;
  maxDraft: number;
  laycanStart: string;
  laycanEnd: string;
  targetFreightRateUsdPerMt?: number;
  status: 'OPEN' | 'MATCHING' | 'OFFERS_RECEIVED' | 'CHARTERED' | 'CANCELLED';
  createdAt: string;
}

export interface ProcurementKpis {
  activeCargoRequirements: number;
  matchedVesselsAvailable: number;
  currentMarketSpotRateUsdPerMt: number;
  projectedSavingsUsd: number;
  averageLaycanWindowDays: number;
  totalVolumeUnderTenderMt: number;
}

export interface OptimizationRecommendation {
  cargoRequirementId: string;
  recommendationType: 'WAIT_TO_CHARTER' | 'BOOK_IMMEDIATELY';
  optimalCharterWindowStart: string;
  optimalCharterWindowEnd: string;
  confidenceScorePercent: number;
  bestVesselMatch: VesselMatch;
  freightForecastSummary: {
    currentRateUsdPerMt: number;
    forecastedRateUsdPerMt: number;
    expectedDeclineUsdPerMt: number;
    percentageDecline: number;
    forecastHorizonDays: number;
  };
  costSummary: {
    freightRateUsdPerMt: number;
    cargoQuantityMt: number;
    baseFreightCostUsd: number;
    bunkerFuelCostUsd: number;
    portDuesAndHandlingUsd: number;
    canalAndTollsUsd: number;
    demurrageRiskCostUsd: number;
    totalOutlayUsd: number;
    potentialSavingsUsd: number;
  };
  rationale: string[];
  targetPortBathymetryStatus: string;
}


// ML Freight Rate Forecast
export interface ForecastDataPoint {
  date: string;
  actualRate?: number;
  forecastRate: number;
  lowerConfidenceBound: number;
  upperConfidenceBound: number;
}

export interface FreightForecastResponse {
  originPort: string;
  destinationPort: string;
  vesselType: VesselType;
  horizonDays: number;
  currentRateUsdPerMt: number;
  predictedRateUsdPerMt: number;
  expectedChangePercent: number;
  confidenceScore: number; // 0.0 to 1.0 (e.g. 0.87 -> 87%)
  trend: 'DECREASING' | 'INCREASING' | 'STABLE';
  recommendation: 'WAIT' | 'BOOK_NOW';
  recommendationDaysToWait?: number;
  reasons: string[];
  estimatedPotentialSavingsUsd: number;
  timeSeries: ForecastDataPoint[];
  modelMetadata: {
    modelName: string;
    version: string;
    mae: number;
    rmse: number;
    trainingDate: string;
  };
}

// Port Congestion ML Prediction
export interface CongestionPoint {
  date: string;
  congestionLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  waitingTimeHours: number;
  berthUtilizationPercent: number;
}

export interface PortCongestionResponse {
  portId: string;
  portName: string;
  currentCongestion: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  predictedCongestionIn3Days: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  currentWaitingTimeHours: number;
  predictedWaitingTimeHours: number;
  berthUtilizationPercent: number;
  riskScore: number; // 0-100
  timeSeries: CongestionPoint[];
  queueVessels: {
    vesselName: string;
    imo: string;
    arrivalDate: string;
    expectedBerthDate: string;
    cargo: string;
    quantityMt: number;
  }[];
}

// Vessel Matching & Optimization
export interface VesselMatch {
  vessel: Vessel;
  matchScorePercent: number;
  freightRateUsdPerMt: number;
  estimatedTotalCostUsd: number;
  eta: string;
  distanceNauticalMiles: number;
  congestionRisk: 'LOW' | 'MEDIUM' | 'HIGH';
  draftFit: boolean;
  channelDepthFit: boolean;
  availabilityFit: boolean;
  laycanCompatibility: boolean;
  riskCategory: 'LOW' | 'MEDIUM' | 'HIGH';
  costBreakdown: {
    freightCost: number;
    bunkerFuelCost: number;
    portCosts: number;
    demurrageWaitingRiskCost: number;
    otherVoyageCost: number;
  };
  recommendationBadge?: 'BEST_MATCH' | 'MOST_ECONOMICAL' | 'FASTEST_ARRIVAL';
}

export interface OptimizationResponse {
  cargoRequirement: CargoRequirement;
  recommendedVessel: VesselMatch;
  alternativeVessels: VesselMatch[];
  aiRecommendation: {
    action: 'BOOK_NOW' | 'WAIT';
    waitDays?: number;
    headline: string;
    summary: string;
    confidencePercent: number;
    expectedRateDeltaPercent: number;
    potentialSavingsUsd: number;
    explainableReasons: string[];
    urgencyLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  };
}

// Charter Marketplace & Negotiation
export type CharterStatus = 
  | 'REQUESTED' 
  | 'OFFERED' 
  | 'NEGOTIATING' 
  | 'SELECTED' 
  | 'CONTRACTED' 
  | 'IN_PROGRESS' 
  | 'COMPLETED' 
  | 'CANCELLED';

export interface CharterOffer {
  id: string;
  charterRequestId: string;
  shipOwnerId: string;
  shipOwnerName: string;
  vesselId: string;
  vesselName: string;
  vesselType: VesselType;
  vesselDwt: number;
  offeredFreightRateUsdPerMt: number;
  totalOfferedCostUsd: number;
  laycanStartOffered: string;
  laycanEndOffered: string;
  demurrageRatePerDayUsd: number;
  despatchRatePerDayUsd: number;
  terms: string;
  status: 'PENDING' | 'ACCEPTED' | 'REJECTED' | 'COUNTERED';
  submittedAt: string;
}

export interface CharterContract {
  id: string;
  cargoRequirementId: string;
  cargoSummary: {
    commodity: CommodityType;
    quantityMt: number;
    origin: string;
    destination: string;
  };
  vesselId: string;
  vesselName: string;
  vesselImo: string;
  procurementOfficerName: string;
  shipOwnerName: string;
  freightRateUsdPerMt: number;
  totalContractValueUsd: number;
  status: CharterStatus;
  eta: string;
  etd: string;
  laycanStart: string;
  laycanEnd: string;
  createdAt: string;
  updatedAt: string;
  offers: CharterOffer[];
}

// Voyage Tracking & Timeline
export interface PortCall {
  portId: string;
  portName: string;
  operation: 'LOADING' | 'DISCHARGE' | 'BUNKERING' | 'ANCHORAGE';
  eta: string;
  ata?: string; // Actual Time of Arrival
  etd: string;
  atd?: string; // Actual Time of Departure
  waitingTimeHours: number;
  turnaroundTimeHours: number;
  status: 'SCHEDULED' | 'ARRIVED' | 'BERTHED' | 'DEPARTED';
}

export interface WeatherCondition {
  location: string;
  windSpeedKnots: number;
  windDirection: string;
  waveHeightMeters: number;
  visibilityNauticalMiles: number;
  condition: 'Clear' | 'Moderate Sea' | 'Rough Sea' | 'Storm Warning' | 'Dense Fog';
  isRiskCondition: boolean;
  warningMessage?: string;
}

export interface Voyage {
  id: string;
  vesselId: string;
  vesselName: string;
  imo: string;
  charterContractId: string;
  cargoType: CommodityType;
  quantityMt: number;
  originPort: string;
  destinationPort: string;
  departureDate: string;
  eta: string;
  currentCoordinates: [number, number]; // [lat, lng]
  speedKnots: number;
  headingDegrees: number;
  currentMilestone: 'LOADING_PORT' | 'DEPARTURE' | 'AT_SEA' | 'ARRIVAL' | 'BERTH' | 'DISCHARGE' | 'DELIVERED';
  milestonesProgressPercent: number;
  weather: WeatherCondition;
  portCalls: PortCall[];
  historicalPositions: [number, number][];
  totalNauticalMiles: number;
  remainingNauticalMiles: number;
}

// Market Intel
export interface MarketData {
  balticDryIndex: {
    current: number;
    change: number;
    changePercent: number;
    trend: 'UP' | 'DOWN';
  };
  balticPanamaxIndex: {
    current: number;
    change: number;
    changePercent: number;
    trend: 'UP' | 'DOWN';
  };
  bunkerFuelVlsfoUsdPerMt: {
    singapore: number;
    rotterdam: number;
    fujairah: number;
    trend: 'UP' | 'DOWN';
  };
  commoditiesUsdPerMt: {
    cokingCoal: number;
    thermalCoal: number;
    ironOre62Percent: number;
  };
  lastUpdated: string;
}

// Notifications
export type NotificationType = 
  | 'FREIGHT_ALERT' 
  | 'CONGESTION_ALERT' 
  | 'VESSEL_ETA_CHANGE' 
  | 'CHARTER_OFFER' 
  | 'VESSEL_MATCH' 
  | 'CONTRACT_UPDATE' 
  | 'WEATHER_WARNING';

export interface AppNotification {
  id: string;
  title: string;
  message: string;
  type: NotificationType;
  severity: 'INFO' | 'SUCCESS' | 'WARNING' | 'CRITICAL';
  createdAt: string;
  isRead: boolean;
  linkUrl?: string;
}
