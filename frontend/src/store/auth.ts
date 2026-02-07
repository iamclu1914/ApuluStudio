"use client";

import { api } from "@/lib/api";

export interface AuthUser {
  id: string;
  email: string;
  name: string | null;
  avatar_url: string | null;
  is_active: boolean;
  created_at: string;
  last_login: string | null;
}

interface TokenPair {
  access_token: string;
  refresh_token: string;
}

const ACCESS_TOKEN_KEY = "apulu_access_token";
const REFRESH_TOKEN_KEY = "apulu_refresh_token";

// --- Token storage helpers ---

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

function saveTokens(tokens: TokenPair) {
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
}

function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

// --- Auth API calls ---

export async function login(email: string, password: string): Promise<AuthUser> {
  const { data: tokens } = await api.post<TokenPair & { token_type: string }>(
    "/auth/login",
    { email, password }
  );
  saveTokens(tokens);
  const { data: user } = await api.get<AuthUser>("/auth/me");
  return user;
}

export async function register(
  email: string,
  password: string,
  name?: string
): Promise<AuthUser> {
  const { data: tokens } = await api.post<TokenPair & { token_type: string }>(
    "/auth/register",
    { email, password, name: name || null }
  );
  saveTokens(tokens);
  const { data: user } = await api.get<AuthUser>("/auth/me");
  return user;
}

export async function refreshAccessToken(): Promise<string | null> {
  const refresh = getRefreshToken();
  if (!refresh) return null;

  try {
    const { data } = await api.post<TokenPair & { token_type: string }>(
      "/auth/refresh",
      { refresh_token: refresh }
    );
    saveTokens(data);
    return data.access_token;
  } catch {
    clearTokens();
    return null;
  }
}

export async function fetchCurrentUser(): Promise<AuthUser | null> {
  const token = getAccessToken();
  if (!token) return null;

  try {
    const { data } = await api.get<AuthUser>("/auth/me");
    return data;
  } catch {
    return null;
  }
}

export function logout() {
  clearTokens();
  window.location.href = "/login";
}
