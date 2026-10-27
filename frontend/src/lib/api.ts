const API_BASE = "http://127.0.0.1:8000/api/v1";
const TOKEN_KEY = "nexus_access_token";

export const SESSION_EXPIRED_EVENT = "nexus:session-expired";

export function getAccessToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function saveAccessToken(token: string): void {
  sessionStorage.setItem(TOKEN_KEY, token);
}

export function clearAccessToken(): void {
  sessionStorage.removeItem(TOKEN_KEY);
}

type ApiOptions = Omit<RequestInit, "body"> & {
  json?: unknown;
};

function errorMessage(data: unknown, status: number): string {
  if (typeof data === "object" && data !== null && "detail" in data) {
    const detail = (data as { detail: unknown }).detail;

    if (typeof detail === "string") {
      return detail;
    }

    if (Array.isArray(detail)) {
      return detail
        .map((item: { msg?: string }) => item.msg || "Invalid request")
        .join("; ");
    }
  }

  return `Request failed with status ${status}.`;
}

export async function api<T>(
  path: string,
  options: ApiOptions = {},
): Promise<T> {
  const { json, ...requestOptions } = options;
  const headers = new Headers(requestOptions.headers);
  const token = getAccessToken();

  headers.set("Accept", "application/json");

  if (json !== undefined) {
    headers.set("Content-Type", "application/json");
  }

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...requestOptions,
    headers,
    body: json === undefined ? undefined : JSON.stringify(json),
  });

  const text = await response.text();
  let data: unknown;

  try {
    data = text ? JSON.parse(text) : undefined;
  } catch {
    throw new Error("The server returned an unexpected response.");
  }

  if (!response.ok) {
    if (response.status === 401 && path !== "/auth/token") {
      clearAccessToken();
      window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT));
    }

    throw new Error(errorMessage(data, response.status));
  }

  return data as T;
}