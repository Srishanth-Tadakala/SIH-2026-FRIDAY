/**
 * Authenticated API Client for F.R.I.D.A.Y. Polar Twin Platform.
 * 
 * Part of SIH 2026 Project SIH26060.
 * Injects cryptographic Bearer tokens, handles structured error payloads,
 * and standardizes JSON requests and responses.
 */

const API_BASE = '/api';
const TOKEN_STORAGE_KEY = 'friday_access_token';

export function getStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
}

export function setStoredToken(token: string | null): void {
  try {
    if (token) {
      localStorage.setItem(TOKEN_STORAGE_KEY, token);
    } else {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
    }
  } catch {}
}

export interface ApiErrorDetails {
  status: number;
  message: string;
  detail?: any;
}

export class ApiError extends Error {
  status: number;
  detail?: any;

  constructor(status: number, message: string, detail?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

export async function requestJson<T>(
  url: string, 
  options: RequestInit = {}
): Promise<T> {
  const headers = new Headers(options.headers || {});
  
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  // Inject Bearer Token if present
  const token = getStoredToken();
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const finalUrl = url.startsWith('/') ? url : `${API_BASE}/${url}`;
  const response = await fetch(finalUrl, { ...options, headers });

  if (!response.ok) {
    let detailMessage = response.statusText;
    let detailData: any = null;
    try {
      const errJson = await response.json();
      detailData = errJson;
      if (errJson?.detail) {
        detailMessage = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      } else if (errJson?.error) {
        detailMessage = typeof errJson.error === 'string' ? errJson.error : JSON.stringify(errJson.error);
      }
    } catch {}

    throw new ApiError(
      response.status,
      `[${response.status}] ${detailMessage}`,
      detailData
    );
  }

  // Return empty object for 204 No Content
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}
