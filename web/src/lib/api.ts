const BASE_URL: string =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ExtractResponse {
  title: string;
  description: string;
  content: string;
  structured_data: Record<string, unknown>;
  actions: string[];
  metadata: Record<string, unknown>;
}

export interface PublishResponse {
  llms_url: string;
  site_id: string;
}

export interface SiteInfo {
  site_id: string;
  llms_url: string;
  url: string;
  content: string;
  site_name: string;
}

export interface ErrorResponse {
  error: string;
  detail: string;
}

export interface HealthResponse {
  status: string;
  version: string;
}

// ---------------------------------------------------------------------------
// Error class
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  status: number;
  body: ErrorResponse | null;

  constructor(status: number, body: ErrorResponse | null) {
    super(body?.detail ?? `Request failed with status ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function request<T>(
  method: string,
  path: string,
  apiKey?: string,
  body?: unknown,
): Promise<T> {
  const headers: Record<string, string> = {};
  if (apiKey) headers["X-API-Key"] = apiKey;
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  let data: unknown;
  const contentType = res.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    data = await res.json();
  } else {
    data = null;
  }

  if (!res.ok) {
    throw new ApiError(res.status, data as ErrorResponse | null);
  }

  return data as T;
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export function extract(
  url: string,
  apiKey: string,
): Promise<ExtractResponse> {
  return request<ExtractResponse>("POST", "/api/v1/extract", apiKey, { url });
}

export function publish(
  url: string,
  name: string,
  content: string,
  apiKey: string,
): Promise<PublishResponse> {
  return request<PublishResponse>("POST", "/api/v1/publish", apiKey, {
    url,
    site_name: name,
    content,
  });
}

export function getSite(
  id: string,
  apiKey: string,
): Promise<SiteInfo> {
  return request<SiteInfo>("GET", `/api/v1/sites/${id}`, apiKey);
}

export function health(): Promise<HealthResponse> {
  return request<HealthResponse>("GET", "/api/v1/health");
}
