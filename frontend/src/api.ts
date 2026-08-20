import { ServicesResponse } from './types';

export async function fetchServices(refresh = false): Promise<ServicesResponse> {
  const r = await fetch(`/api/services${refresh ? '?refresh=true' : ''}`);
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || `HTTP ${r.status}`);
  return r.json();
}
