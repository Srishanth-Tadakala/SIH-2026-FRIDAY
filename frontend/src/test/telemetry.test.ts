import { describe, it, expect } from 'vitest';

export interface StationVitals {
  totalGenerationKw: number;
  totalLoadKw: number;
  indoorTempC: number;
  ambientTempC: number;
  windSpeedMps: number;
  fuelReserveLiters: number;
  fuelBurnRateLph: number;
}

export function computeStationStatus(vitals: StationVitals) {
  const reserveMarginKw = vitals.totalGenerationKw - vitals.totalLoadKw;
  const isPowerDeficit = reserveMarginKw < 0;
  const fuelAutonomyDays = vitals.fuelBurnRateLph > 0
    ? (vitals.fuelReserveLiters / (vitals.fuelBurnRateLph * 24))
    : 999;
  const isSevereWeather = vitals.windSpeedMps > 20.0 || vitals.ambientTempC < -30.0;
  const isThermalAlert = vitals.indoorTempC < 16.0;

  return {
    reserveMarginKw,
    isPowerDeficit,
    fuelAutonomyDays: Math.round(fuelAutonomyDays * 10) / 10,
    isSevereWeather,
    isThermalAlert,
    operationalHealth: (isPowerDeficit || isThermalAlert) ? 'CRITICAL' : (isSevereWeather ? 'WARNING' : 'NOMINAL'),
  };
}

export function computeSatcomDeltaSavings(uncompressedBytes: number, deltaCompressedBytes: number): number {
  if (uncompressedBytes <= 0) return 0.0;
  const saved = (uncompressedBytes - deltaCompressedBytes) / uncompressedBytes;
  return Math.round(saved * 1000) / 10;
}

describe('Antarctic Station Telemetry and Vitals Logic', () => {
  it('correctly calculates nominal operational status', () => {
    const vitals: StationVitals = {
      totalGenerationKw: 150.0,
      totalLoadKw: 85.0,
      indoorTempC: 21.0,
      ambientTempC: -15.0,
      windSpeedMps: 12.0,
      fuelReserveLiters: 120000,
      fuelBurnRateLph: 25.0,
    };
    const status = computeStationStatus(vitals);
    expect(status.operationalHealth).toBe('NOMINAL');
    expect(status.isPowerDeficit).toBe(false);
    expect(status.reserveMarginKw).toBe(65.0);
    expect(status.fuelAutonomyDays).toBe(200.0);
  });

  it('triggers CRITICAL on life-support thermal violation below 16 C', () => {
    const vitals: StationVitals = {
      totalGenerationKw: 100.0,
      totalLoadKw: 70.0,
      indoorTempC: 14.5, // Thermal drop
      ambientTempC: -25.0,
      windSpeedMps: 15.0,
      fuelReserveLiters: 50000,
      fuelBurnRateLph: 20.0,
    };
    const status = computeStationStatus(vitals);
    expect(status.isThermalAlert).toBe(true);
    expect(status.operationalHealth).toBe('CRITICAL');
  });

  it('triggers WARNING on Katabatic blizzard weather lockout', () => {
    const vitals: StationVitals = {
      totalGenerationKw: 150.0,
      totalLoadKw: 90.0,
      indoorTempC: 20.0,
      ambientTempC: -35.0, // Severe cold
      windSpeedMps: 28.5,  // Severe wind
      fuelReserveLiters: 80000,
      fuelBurnRateLph: 30.0,
    };
    const status = computeStationStatus(vitals);
    expect(status.isSevereWeather).toBe(true);
    expect(status.operationalHealth).toBe('WARNING');
  });

  it('computes satcom delta compression bandwidth savings above 85%', () => {
    // 505 sensors uncompressed JSON ~45,000 bytes, delta frame ~4,200 bytes
    const savingsPct = computeSatcomDeltaSavings(45000, 4200);
    expect(savingsPct).toBeGreaterThanOrEqual(85.0);
    expect(savingsPct).toBe(90.7);
  });
});
