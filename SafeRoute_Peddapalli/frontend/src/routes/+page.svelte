<script lang="ts">
    import { onMount, tick } from 'svelte';
    import type { Map, Polyline } from 'leaflet';
  
    // Map State
    let mapElement: HTMLElement;
    let L: any;
    let mapInstance: Map;
    let accidentsList: any[] = $state([]);
    let accidentMarkers: any[] = [];
    let safestRoutePath: Polyline | null = null;
    let shortestRoutePath: Polyline | null = null;
    let startMarker: any = null;
    let endMarker: any = null;
  
    // UI Form State
    let startQuery = $state("");
    let endQuery = $state("");
    let startLat = $state<number | null>(null);
    let startLon = $state<number | null>(null);
    let endLat = $state<number | null>(null);
    let endLon = $state<number | null>(null);
    
    // Autocomplete State
    let startSuggestions: any[] = $state([]);
    let endSuggestions: any[] = $state([]);
    let isSearchingStart = $state(false);
    let isSearchingEnd = $state(false);

    // Selection Mode
    let mapSelectMode = $state<'start' | 'end' | null>(null);

    let routeResult: any = $state(null);
    let isLoading = $state(false);
    let debounceTimer: ReturnType<typeof setTimeout>;

    // Predefined Places
    const predefinedPlaces = [
        { name: "Peddapalli Center", lat: 18.6189, lon: 79.3855 },
        { name: "Sultanabad", lat: 18.5260, lon: 79.3170 },
        { name: "Ramagundam", lat: 18.7535, lon: 79.4860 },
        { name: "Manthani", lat: 18.6490, lon: 79.6720 },
        { name: "Godavarikhani", lat: 18.7645, lon: 79.4655 },
        { name: "Kamanpur", lat: 18.6110, lon: 79.3940 }
    ];

    let showStartDropdown = $state(false);
    let showEndDropdown = $state(false);

    onMount(async () => {
        L = await import('leaflet');
        // Initial center near Peddapalli
        mapInstance = L.map(mapElement, { zoomControl: false }).setView([18.6189, 79.3855], 11);
        
        L.control.zoom({ position: 'bottomright' }).addTo(mapInstance);

        // CartoDB Dark Matter tiles
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; CartoDB',
            subdomains: 'abcd',
            maxZoom: 19
        }).addTo(mapInstance);

        // Map Click Event for manual selection
        mapInstance.on('click', async (e: any) => {
            if (mapSelectMode === 'start') {
                const lat = e.latlng.lat;
                const lon = e.latlng.lng;
                startLat = lat;
                startLon = lon;
                startQuery = await reverseGeocode(lat, lon);
                updateMarker('start', lat, lon);
                mapSelectMode = null; // reset mode
            } else if (mapSelectMode === 'end') {
                const lat = e.latlng.lat;
                const lon = e.latlng.lng;
                endLat = lat;
                endLon = lon;
                endQuery = await reverseGeocode(lat, lon);
                updateMarker('end', lat, lon);
                mapSelectMode = null; // reset mode
            }
        });
  
        await loadAccidents();
    });
  
    async function loadAccidents() {
        try {
            const res = await fetch("http://127.0.0.1:8000/accidents");
            accidentsList = await res.json();
            plotHeatmapOrPoints();
        } catch (e) {
            console.error("Failed to load accidents:", e);
        }
    }
  
    function plotHeatmapOrPoints() {
        if (!L || !mapInstance) return;
        accidentsList.forEach(a => {
            const marker = L.circleMarker([a.latitude, a.longitude], {
                radius: 4,
                fillColor: '#ef4444',
                color: '#ef4444',
                weight: 0,
                opacity: 0.2,
                fillOpacity: 0.35
            }).bindTooltip(`
                <div class="font-sans">
                    <b class="text-slate-800">${a.accident_prone_area}</b><br/>
                    <span class="text-xs text-slate-500">Cause: ${a.cause}</span>
                </div>
            `).addTo(mapInstance);
            accidentMarkers.push(marker);
        });
    }

    async function reverseGeocode(lat: number, lon: number): Promise<string> {
        try {
            const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`);
            const data = await res.json();
            return data.display_name.split(',')[0] + " (Map Selection)";
        } catch (e) {
            return `Lat: ${lat.toFixed(4)}, Lon: ${lon.toFixed(4)}`;
        }
    }

    // Geocoding Search
    async function searchLocation(query: string, type: 'start' | 'end') {
        if (type === 'start') showStartDropdown = true;
        if (type === 'end') showEndDropdown = true;

        if (query.trim().length === 0) {
            if (type === 'start') startSuggestions = [];
            else endSuggestions = [];
            return;
        }

        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(async () => {
            if (type === 'start') isSearchingStart = true;
            else isSearchingEnd = true;

            try {
                // Ignore API call if it's perfectly matching a predefined place name
                const isPredefined = predefinedPlaces.some(p => p.name.toLowerCase() === query.toLowerCase());
                if(isPredefined) return;

                const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&viewbox=79.2,18.8,79.8,18.4&bounded=1&limit=5`);
                const data = await res.json();
                
                // Map the data to our suggestion format
                const mappedData = data.map((d: any) => ({
                    name: d.display_name.split(',')[0],
                    desc: d.display_name,
                    lat: parseFloat(d.lat),
                    lon: parseFloat(d.lon)
                }));

                if (type === 'start') startSuggestions = mappedData;
                else endSuggestions = mappedData;
            } catch (e) {
                console.error("Geocoding failed", e);
            } finally {
                if (type === 'start') isSearchingStart = false;
                else isSearchingEnd = false;
            }
        }, 500);
    }

    function selectLocation(suggestion: any, type: 'start' | 'end') {
        if (type === 'start') {
            startQuery = suggestion.name;
            startLat = suggestion.lat;
            startLon = suggestion.lon;
            startSuggestions = [];
            showStartDropdown = false;
            updateMarker('start', suggestion.lat, suggestion.lon);
        } else {
            endQuery = suggestion.name;
            endLat = suggestion.lat;
            endLon = suggestion.lon;
            endSuggestions = [];
            showEndDropdown = false;
            updateMarker('end', suggestion.lat, suggestion.lon);
        }

        if (startLat && endLat) {
            const bounds = L.latLngBounds([[startLat, startLon], [endLat, endLon]]);
            mapInstance.fitBounds(bounds, { padding: [50, 50] });
        } else {
            mapInstance.flyTo([suggestion.lat, suggestion.lon], 14, { duration: 1 });
        }
    }

    function updateMarker(type: 'start' | 'end', lat: number, lon: number) {
        if (!L || !mapInstance) return;

        const iconHtml = `<div class="w-6 h-6 rounded-full border-[3px] shadow-lg flex items-center justify-center ${type === 'start' ? 'border-cyan-400 bg-cyan-500/20' : 'border-purple-400 bg-purple-500/20'}">
            <div class="w-2 h-2 rounded-full ${type === 'start' ? 'bg-cyan-400' : 'bg-purple-400'}"></div>
        </div>`;

        const customIcon = L.divIcon({
            html: iconHtml,
            className: '',
            iconSize: [24, 24],
            iconAnchor: [12, 12]
        });

        if (type === 'start') {
            if (startMarker) mapInstance.removeLayer(startMarker);
            startMarker = L.marker([lat, lon], { icon: customIcon }).addTo(mapInstance);
        } else {
            if (endMarker) mapInstance.removeLayer(endMarker);
            endMarker = L.marker([lat, lon], { icon: customIcon }).addTo(mapInstance);
        }
    }
  
    async function getRoute() {
        if (!startLat || !startLon || !endLat || !endLon) return;

        isLoading = true;
        routeResult = null;
        try {
            const res = await fetch("http://127.0.0.1:8000/get-route", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({
                    start_lat: startLat, start_lon: startLon,
                    end_lat: endLat, end_lon: endLon
                })
            });
            if (!res.ok) throw new Error("API Route Failure");
            const data = await res.json();
            routeResult = data;
            drawRoutes(data);
        } catch (e) {
            console.error(e);
            alert("Error computing route. Network or backend offline.");
        } finally {
            isLoading = false;
        }
    }
  
    function drawRoutes(data: any) {
        if (!L || !mapInstance) return;
        if (safestRoutePath) mapInstance.removeLayer(safestRoutePath);
        if (shortestRoutePath) mapInstance.removeLayer(shortestRoutePath);
  
        const safestCoords = data.safest_route.map((n: any) => [n.lat, n.lon]);
        const shortestCoords = data.shortest_route.map((n: any) => [n.lat, n.lon]);
  
        safestRoutePath = L.polyline(safestCoords, { 
            color: '#10b981', 
            weight: 6, 
            opacity: 0.9,
            className: 'animate-pulse' 
        }).addTo(mapInstance);

        shortestRoutePath = L.polyline(shortestCoords, { 
            color: '#64748b', 
            weight: 3, 
            dashArray: '8, 8',
            opacity: 0.6
        }).addTo(mapInstance);
  
        if (safestCoords.length > 1) {
            const bounds = L.latLngBounds(safestCoords);
            mapInstance.fitBounds(bounds, { padding: [100, 100] });
        }
    }

    function toggleMode(mode: 'start' | 'end') {
        if (mapSelectMode === mode) {
            mapSelectMode = null;
        } else {
            mapSelectMode = mode;
        }
    }
</script>
  
<div class="relative w-full h-screen overflow-hidden font-['Inter'] text-slate-100 flex">
    
    <!-- Notification Overlay if picking from map -->
    {#if mapSelectMode}
        <div class="absolute top-6 left-1/2 -translate-x-1/2 z-50 bg-indigo-500/90 text-white px-6 py-3 rounded-full font-semibold shadow-xl shadow-indigo-500/30 flex items-center gap-2 animate-bounce">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122"></path></svg>
            Click anywhere on the map to select {mapSelectMode === 'start' ? 'Origin' : 'Destination'}
            <button class="ml-4 bg-white/20 hover:bg-white/30 rounded-full px-3 py-1 text-sm font-bold transition-colors" onclick={() => mapSelectMode = null}>Cancel</button>
        </div>
    {/if}

    <!-- Leaflet Map -->
    <div bind:this={mapElement} class="absolute inset-0 z-0 bg-[#020617] {mapSelectMode ? 'cursor-crosshair' : ''}"></div>
    
    <!-- Modern Floating Left Panel -->
    <div class="relative z-10 m-6 w-[420px] bg-slate-900/60 backdrop-blur-2xl border border-white/5 shadow-[0_8px_32px_rgba(0,0,0,0.5)] rounded-3xl flex flex-col pointer-events-auto overflow-hidden h-fit max-h-[calc(100vh-48px)]">
        
        <!-- Header -->
        <div class="p-8 pb-6 bg-gradient-to-b from-white/[0.03] to-transparent">
            <h1 class="text-3xl font-extrabold tracking-tight mb-2 flex items-center gap-2">
                <div class="w-8 h-8 rounded-xl bg-gradient-to-br from-emerald-400 to-cyan-500 flex items-center justify-center shadow-lg shadow-cyan-500/20">
                    <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"></path></svg>
                </div>
                SafeRoute
            </h1>
            <p class="text-sm font-medium text-slate-400">Intelligent Risk Mitigation Routing for Peddapalli</p>
        </div>
        
        <!-- Inputs Body -->
        <div class="px-8 pb-8 flex-1 overflow-y-auto custom-scrollbar">
            
            <div class="relative flex flex-col gap-6">
                <!-- Decorative Timeline Line -->
                <div class="absolute left-3 top-8 bottom-8 w-px bg-slate-700/50 z-0"></div>

                <!-- Source Input Group -->
                <div class="relative z-10">
                    <div class="flex items-center justify-between mb-2">
                        <label for="origin-input" class="text-xs font-bold text-slate-400 uppercase tracking-widest pl-8 block">Origin</label>
                        <button onclick={() => toggleMode('start')} class="text-xs text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1 transition-colors {mapSelectMode === 'start' ? 'text-cyan-300 drop-shadow-[0_0_5px_rgba(34,211,238,0.8)]' : ''}">
                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                            {mapSelectMode === 'start' ? 'Picking...' : 'Pick on Map'}
                        </button>
                    </div>

                    <div class="relative flex items-center">
                        <div class="w-6 h-6 rounded-full border-2 border-cyan-400 bg-slate-900 flex items-center justify-center absolute left-0 z-10 shadow-[0_0_10px_rgba(34,211,238,0.3)]">
                            <div class="w-2 h-2 rounded-full bg-cyan-400"></div>
                        </div>
                        <input 
                            id="origin-input"
                            type="text" 
                            bind:value={startQuery}
                            onfocus={() => showStartDropdown = true}
                            oninput={() => searchLocation(startQuery, 'start')}
                            placeholder="Search or pick predefined..." 
                            class="w-full ml-4 bg-slate-800/40 outline-none border border-slate-700/60 rounded-xl pl-6 pr-4 py-3 text-sm focus:border-cyan-500/50 focus:bg-slate-800/80 transition-all placeholder:text-slate-500 shadow-inner" 
                        />
                        {#if isSearchingStart}
                            <div class="absolute right-4 w-4 h-4 border-2 border-slate-500 border-t-cyan-400 rounded-full animate-spin"></div>
                        {:else}
                            <button aria-label="Toggle Origin Dropdown" class="absolute right-3 p-1.5 text-slate-500 hover:text-slate-300 transition-colors" onclick={() => showStartDropdown = !showStartDropdown}>
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                            </button>
                        {/if}
                    </div>
                    
                    {#if showStartDropdown}
                        <div class="absolute w-[calc(100%-1rem)] ml-4 mt-2 bg-slate-800 border border-slate-700 rounded-xl shadow-2xl overflow-hidden z-20 max-h-[220px] overflow-y-auto custom-scrollbar">
                            <!-- Predefined list merges with search results -->
                            {#if startSuggestions.length === 0 && startQuery.length < 3}
                                <div class="px-3 py-2 text-xs font-bold text-slate-500 uppercase tracking-wider bg-slate-800/80 backdrop-blur sticky top-0">Quick Picks</div>
                                {#each predefinedPlaces as sug}
                                    <button class="w-full text-left px-4 py-3 hover:bg-slate-700/50 border-b border-slate-700/50 last:border-0 transition-colors flex items-center gap-2 group" onclick={() => selectLocation(sug, 'start')}>
                                        <svg class="w-4 h-4 text-slate-500 group-hover:text-cyan-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                                        <span class="text-sm font-medium text-slate-200">{sug.name}</span>
                                    </button>
                                {/each}
                            {/if}

                            {#each startSuggestions as sug}
                                <button class="w-full text-left px-4 py-3 text-sm hover:bg-slate-700/50 border-b border-slate-700/50 last:border-0 transition-colors" onclick={() => selectLocation(sug, 'start')}>
                                    <div class="text-slate-200 truncate font-medium">{sug.name}</div>
                                    <div class="text-slate-500 text-xs truncate">{sug.desc}</div>
                                </button>
                            {/each}
                        </div>
                    {/if}
                </div>
      
                <!-- Dest Input Group -->
                <div class="relative z-10">
                    <div class="flex items-center justify-between mb-2">
                        <label for="dest-input" class="text-xs font-bold text-slate-400 uppercase tracking-widest pl-8 block">Destination</label>
                        <button onclick={() => toggleMode('end')} class="text-xs text-purple-400 hover:text-purple-300 font-semibold flex items-center gap-1 transition-colors {mapSelectMode === 'end' ? 'text-purple-300 drop-shadow-[0_0_5px_rgba(192,132,252,0.8)]' : ''}">
                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                            {mapSelectMode === 'end' ? 'Picking...' : 'Pick on Map'}
                        </button>
                    </div>

                    <div class="relative flex items-center">
                        <div class="w-6 h-6 rounded-full border-2 border-purple-400 bg-slate-900 flex items-center justify-center absolute left-0 z-10 shadow-[0_0_10px_rgba(192,132,252,0.3)]">
                            <div class="w-2 h-2 rounded-full bg-purple-400"></div>
                        </div>
                        <input 
                            id="dest-input"
                            type="text" 
                            bind:value={endQuery}
                            onfocus={() => showEndDropdown = true}
                            oninput={() => searchLocation(endQuery, 'end')}
                            placeholder="Search or pick predefined..." 
                            class="w-full ml-4 bg-slate-800/40 outline-none border border-slate-700/60 rounded-xl pl-6 pr-4 py-3 text-sm focus:border-purple-500/50 focus:bg-slate-800/80 transition-all placeholder:text-slate-500 shadow-inner" 
                        />
                        {#if isSearchingEnd}
                            <div class="absolute right-4 w-4 h-4 border-2 border-slate-500 border-t-purple-400 rounded-full animate-spin"></div>
                        {:else}
                             <button aria-label="Toggle Destination Dropdown" class="absolute right-3 p-1.5 text-slate-500 hover:text-slate-300 transition-colors" onclick={() => showEndDropdown = !showEndDropdown}>
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                            </button>
                        {/if}
                    </div>

                    {#if showEndDropdown}
                        <div class="absolute w-[calc(100%-1rem)] ml-4 mt-2 bg-slate-800 border border-slate-700 rounded-xl shadow-2xl overflow-hidden z-20 max-h-[220px] overflow-y-auto custom-scrollbar">
                            {#if endSuggestions.length === 0 && endQuery.length < 3}
                                <div class="px-3 py-2 text-xs font-bold text-slate-500 uppercase tracking-wider bg-slate-800/80 backdrop-blur sticky top-0">Quick Picks</div>
                                {#each predefinedPlaces as sug}
                                    <button class="w-full text-left px-4 py-3 hover:bg-slate-700/50 border-b border-slate-700/50 last:border-0 transition-colors flex items-center gap-2 group" onclick={() => selectLocation(sug, 'end')}>
                                        <svg class="w-4 h-4 text-slate-500 group-hover:text-purple-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                                        <span class="text-sm font-medium text-slate-200">{sug.name}</span>
                                    </button>
                                {/each}
                            {/if}

                            {#each endSuggestions as sug}
                                <button class="w-full text-left px-4 py-3 text-sm hover:bg-slate-700/50 border-b border-slate-700/50 last:border-0 transition-colors" onclick={() => selectLocation(sug, 'end')}>
                                    <div class="text-slate-200 truncate font-medium">{sug.name}</div>
                                    <div class="text-slate-500 text-xs truncate">{sug.desc}</div>
                                </button>
                            {/each}
                        </div>
                    {/if}
                </div>
            </div>
  
            <button 
                onclick={getRoute} 
                disabled={!startLat || !endLat || isLoading}
                class="mt-8 w-full bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 disabled:opacity-50 disabled:grayscale text-white font-bold tracking-wide rounded-xl py-4 shadow-[0_0_25px_rgba(16,185,129,0.25)] hover:shadow-[0_0_35px_rgba(16,185,129,0.4)] transition-all flex justify-center items-center gap-2 group"
            >
                {#if isLoading}
                    <div class="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                    <span>Analyzing Risks...</span>
                {:else}
                    Calculate Safe Route
                    <svg class="w-5 h-5 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
                {/if}
            </button>
            
            <!-- Analysis Results -->
            {#if routeResult}
            <div class="mt-8 pt-8 border-t border-slate-700/50 animate-fade-in">
                <div class="flex items-center justify-between mb-6">
                    <h3 class="text-xs uppercase font-extrabold text-slate-400 tracking-widest">Analysis Results</h3>
                    <div class="px-2 py-1 rounded-md bg-emerald-500/10 text-emerald-400 text-xs font-bold border border-emerald-500/20">Optimal Path Found</div>
                </div>
                
                <div class="grid grid-cols-2 gap-4">
                    <div class="bg-gradient-to-br from-emerald-500/10 to-transparent p-5 rounded-2xl flex flex-col border border-emerald-500/30 shadow-[inset_0_0_20px_rgba(16,185,129,0.05)] relative overflow-hidden">
                        <div class="absolute top-0 right-0 w-16 h-16 bg-emerald-500/10 blur-xl rounded-full translate-x-1/2 -translate-y-1/2"></div>
                        <span class="text-[0.65rem] text-emerald-400 font-bold tracking-widest uppercase mb-1 flex items-center gap-1">
                            <div class="w-1.5 h-1.5 rounded-full bg-emerald-400"></div> Safe Route
                        </span>
                        <div class="flex items-end gap-1 mt-1">
                            <span class="text-3xl font-black text-white">{routeResult.safe_score.toFixed(1)}</span>
                            <span class="text-sm text-slate-400 mb-1 font-medium">risk</span>
                        </div>
                    </div>
                    
                    <div class="bg-slate-800/30 p-5 rounded-2xl flex flex-col border border-slate-700/50">
                        <span class="text-[0.65rem] text-slate-400 font-bold tracking-widest uppercase mb-1 flex items-center gap-1">
                            <div class="w-1.5 h-1.5 rounded-full bg-slate-400/50"></div> Direct Route
                        </span>
                        <div class="flex items-end gap-1 mt-1">
                            <span class="text-3xl font-black text-slate-300">{routeResult.short_score.toFixed(1)}</span>
                            <span class="text-sm text-slate-500 mb-1 font-medium">risk</span>
                        </div>
                    </div>
                </div>
                
                <div class="mt-6 p-5 bg-gradient-to-r from-red-500/5 to-orange-500/5 border border-red-500/10 rounded-2xl flex gap-3">
                    <div class="text-red-400 mt-0.5 animate-pulse">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                    </div>
                    <div>
                        <span class="text-slate-300 font-semibold block mb-1 text-sm">Why this route?</span>
                        <p class="text-sm text-slate-400 leading-relaxed font-medium">
                            The direct path intersects <span class="text-red-400 font-bold">high-risk accident zones</span>. Taking the safe route avoids these nodes, reducing statistical likelihood of incidents.
                        </p>
                    </div>
                </div>
            </div>
            {/if}
        </div>
    </div>
    
</div>
  
<style>
    :global(.leaflet-container) {
        background: #020617;
        font-family: 'Inter', sans-serif;
    }
    :global(.leaflet-control-attribution) {
        background: transparent !important;
        color: rgba(255,255,255,0.2) !important;
    }
    :global(.leaflet-control-attribution a) {
        color: rgba(255,255,255,0.4) !important;
    }
    :global(.leaflet-control-zoom-in),
    :global(.leaflet-control-zoom-out) {
        background-color: rgba(15, 23, 42, 0.8) !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        backdrop-filter: blur(8px);
    }
    :global(.leaflet-control-zoom-in:hover),
    :global(.leaflet-control-zoom-out:hover) {
        background-color: rgba(30, 41, 59, 1) !important;
    }
    
    .custom-scrollbar::-webkit-scrollbar {
        width: 4px;
    }
    .custom-scrollbar::-webkit-scrollbar-track {
        background: transparent;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 4px;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.2);
    }

    /* Simple fade in animation for results */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .animate-fade-in {
        animation: fadeIn 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }
</style>
