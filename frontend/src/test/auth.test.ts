import { describe, it, expect, beforeEach } from 'vitest';

export type UserRole = 'VIEWER' | 'OPERATOR' | 'ENGINEER' | 'COMMANDER' | 'ADMIN';

export interface AuthSession {
  token: string;
  username: string;
  role: UserRole;
  station_id?: string | null;
}

export class AuthService {
  private static STORAGE_KEY = 'friday_auth_token';
  private static USER_KEY = 'friday_auth_user';

  static saveSession(session: AuthSession): void {
    localStorage.setItem(this.STORAGE_KEY, session.token);
    localStorage.setItem(this.USER_KEY, JSON.stringify(session));
  }

  static getSession(): AuthSession | null {
    const token = localStorage.getItem(this.STORAGE_KEY);
    const userStr = localStorage.getItem(this.USER_KEY);
    if (!token || !userStr) return null;
    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  }

  static clearSession(): void {
    localStorage.removeItem(this.STORAGE_KEY);
    localStorage.removeItem(this.USER_KEY);
  }

  static getAuthHeaders(): Record<string, string> {
    const token = localStorage.getItem(this.STORAGE_KEY);
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  static hasRole(requiredRole: UserRole, userRole: UserRole): boolean {
    const hierarchy: Record<UserRole, number> = {
      VIEWER: 1,
      OPERATOR: 2,
      ENGINEER: 3,
      COMMANDER: 4,
      ADMIN: 5,
    };
    return (hierarchy[userRole] || 0) >= (hierarchy[requiredRole] || 0);
  }
}

describe('AuthService and RBAC', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('stores and retrieves session token and user details', () => {
    const session: AuthSession = {
      token: 'jwt.mock.token.123',
      username: 'commander',
      role: 'COMMANDER',
      station_id: 'bharati',
    };
    AuthService.saveSession(session);

    const retrieved = AuthService.getSession();
    expect(retrieved).not.toBeNull();
    expect(retrieved?.username).toBe('commander');
    expect(retrieved?.role).toBe('COMMANDER');
  });

  it('generates proper Authorization Bearer headers', () => {
    expect(AuthService.getAuthHeaders()).toEqual({});

    AuthService.saveSession({
      token: 'valid-secret-token',
      username: 'engineer',
      role: 'ENGINEER',
    });
    expect(AuthService.getAuthHeaders()).toEqual({
      Authorization: 'Bearer valid-secret-token',
    });
  });

  it('enforces RBAC hierarchy correctly', () => {
    expect(AuthService.hasRole('OPERATOR', 'VIEWER')).toBe(false);
    expect(AuthService.hasRole('OPERATOR', 'OPERATOR')).toBe(true);
    expect(AuthService.hasRole('OPERATOR', 'ENGINEER')).toBe(true);
    expect(AuthService.hasRole('COMMANDER', 'ENGINEER')).toBe(false);
    expect(AuthService.hasRole('COMMANDER', 'COMMANDER')).toBe(true);
    expect(AuthService.hasRole('COMMANDER', 'ADMIN')).toBe(true);
  });

  it('clears session on logout', () => {
    AuthService.saveSession({
      token: 'test',
      username: 'viewer',
      role: 'VIEWER',
    });
    AuthService.clearSession();
    expect(AuthService.getSession()).toBeNull();
  });
});
