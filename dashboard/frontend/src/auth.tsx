import { createContext, useContext, useMemo, useState, type PropsWithChildren } from "react";
import { MarketplaceApiClient, type LoginRequest, type LoginResponse } from "./api";

interface AuthState { token: string | null; login(request: LoginRequest): Promise<LoginResponse>; logout(): Promise<void>; client: MarketplaceApiClient; }
const tokenKey = "tkai.marketplace.bearer";
const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: PropsWithChildren) {
  const [token, setToken] = useState<string | null>(() => sessionStorage.getItem(tokenKey));
  const client = useMemo(() => new MarketplaceApiClient().withToken(token ?? undefined), [token]);
  const value = useMemo<AuthState>(() => ({
    token,
    client,
    async login(request) { const result = await new MarketplaceApiClient().login(request); sessionStorage.setItem(tokenKey, result.access_token); setToken(result.access_token); return result; },
    async logout() { if (token) await client.logout(); sessionStorage.removeItem(tokenKey); setToken(null); }
  }), [client, token]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState { const value = useContext(AuthContext); if (!value) throw new Error("AuthProvider is required."); return value; }
