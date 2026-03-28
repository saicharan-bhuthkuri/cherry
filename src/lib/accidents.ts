export interface AccidentRecord {
  id: number;
  year: number;
  mandal: string;
  accident_prone_area: string;
  latitude: number;
  longitude: number;
  road_type: string;
  vehicles: number;
  fatalities: number;
  injuries: number;
  accident_type: string;
  weather: string;
  cause: string;
  time_of_day: string;
  risk: number;
}

let _cache: AccidentRecord[] | null = null;

export async function loadAccidents(): Promise<AccidentRecord[]> {
  if (_cache) return _cache;
  const res = await fetch('/accidents.json');
  if (!res.ok) throw new Error('Failed to load accident data');
  _cache = await res.json();
  return _cache!;
}
