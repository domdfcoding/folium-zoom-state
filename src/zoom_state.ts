//
//  zoom_state.js
/*
Preserve zoom level and map position when reloading or sharing URLs
*/
//
//  Copyright © 2026 Dominic Davis-Foster <dominic@davis-foster.co.uk>
//
//  Permission is hereby granted, free of charge, to any person obtaining a copy
//  of this software and associated documentation files (the "Software"), to deal
//  in the Software without restriction, including without limitation the rights
//  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
//  copies of the Software, and to permit persons to whom the Software is
//  furnished to do so, subject to the following conditions:
//
//  The above copyright notice and this permission notice shall be included in all
//  copies or substantial portions of the Software.
//
//  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
//  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
//  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
//  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
//  DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
//  OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
//  OR OTHER DEALINGS IN THE SOFTWARE.
//

function updateQueryStringParam (key: string, value: number|string): void {
	const url = new URL(window.location.href);
	url.searchParams.set(key, value.toString()); // Add or update the parameter
	// window.history.pushState({}, null, url);
	window.history.replaceState({}, '', url);
}

interface IZoomState {
	centre: L.LatLng;
	zoomLvl: number;
 }

// eslint-disable-next-line @typescript-eslint/no-unused-vars
class ZoomState {
	map: L.Map;

	constructor (map: L.Map) {
		this.map = map;
	}

	onZoomEnd () {
		const zoomLvl: number = this.map.getZoom();
		updateQueryStringParam('zoom', zoomLvl);
	}

	onMoveEnd () {
		const centre = this.map.getCenter();
		updateQueryStringParam('lat', centre.lat);
		updateQueryStringParam('lng', centre.lng);
	}

	setup () {
		this.map.on('zoomend', this.onZoomEnd, this);
		this.map.on('moveend', this.onMoveEnd, this);
	}

	fromURL (defaultZoom: number, defaultCentre: L.LatLng): IZoomState {
		return zoomStateFromURL(defaultZoom, defaultCentre);
	}
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function setupZoomState (map: L.Map): void {
	new ZoomState(map).setup();
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function zoomStateFromURL (defaultZoom: number, defaultCentre: L.LatLng): IZoomState {
	const url = new URL(window.location.href);

	// let zoomLvl = map.getZoom();
	let zoomLvl = defaultZoom;
	if (url.searchParams.has('zoom')) {
		zoomLvl = parseInt(url.searchParams.get('zoom')!);
	}

	// const centre = map.getCenter();
	const centre = defaultCentre;
	if (url.searchParams.has('lat')) {
		centre.lat = parseFloat(url.searchParams.get('lat')!);
	}
	if (url.searchParams.has('lng')) {
		centre.lng = parseFloat(url.searchParams.get('lng')!);
	}

	return { centre, zoomLvl };
}

interface layer {
	layer: L.Layer
	name: string
	overlay?: boolean | undefined
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
class BasemapState {
	map: L.Map;
	layerControl: L.Control.Layers;
	paramName: string;

	constructor (map: L.Map, layerControl: L.Control.Layers, paramName: string = 'basemap') {
		this.map = map;
		this.layerControl = layerControl;
		this.paramName = paramName;
	}

	fromURL (defaultBasemap: string): L.TileLayer {
		return basemapFromURL(defaultBasemap, this.layerControl, this.paramName);
	}

	setup (): void {
		setupBasemapState(this.map, this.paramName);
	}
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function basemapFromURL (
	defaultBasemap: string,
	layerControl: L.Control.Layers,
	paramName: string = 'basemap'
): L.TileLayer {
	const url = new URL(window.location.href);

	const basemapLayers = Object.fromEntries(
		/* @ts-expect-error _layers does exist but is private */
		layerControl._layers.map(
			(element: layer) => [element.name, element.layer]
		)
	);

	if (url.searchParams.has(paramName)) {
		const basemapName = url.searchParams.get(paramName) ?? defaultBasemap;
		console.log(basemapName);

		if (basemapName in basemapLayers) {
			return basemapLayers[basemapName];
		}
	}

	return basemapLayers[defaultBasemap];
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function setupBasemapState (map: L.Map, paramName: string = 'basemap'): void {
	map.on('baselayerchange', (e: L.LayersControlEvent) => updateQueryStringParam(paramName, e.name));
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
class OverlayState {
	map: L.Map;
	layerControl: L.Control.Layers;
	paramName: string;

	constructor (map: L.Map, layerControl: L.Control.Layers, paramName: string = 'overlays') {
		this.map = map;
		this.layerControl = layerControl;
		this.paramName = paramName;
	}

	getOverlays (): L.Layer[] {
		const overlays: L.Layer[] = [];

		/* @ts-expect-error _layers does exist but is private */
		this.layerControl._layers.forEach((layer: layer) => {
			if (layer.overlay) {
				overlays.push(layer.layer);
			}
		});

		return overlays;
	}

	updateOverlayParams (): void {
		const overlays = this.getOverlays();

		let bits: string = '';
		overlays.forEach((layer) => {
			if (this.map.hasLayer(layer)) {
				bits += '1';
			} else {
				bits += '0';
			}
		});

		console.log('Overlay bits:', bits);
		updateQueryStringParam(this.paramName, bits);
	}

	setup (): void {
		this.map.on('overlayadd', this.updateOverlayParams, this);
		this.map.on('overlayremove', this.updateOverlayParams, this);
	}

	fromURL (defaultOverlays: string): void {
		const url = new URL(window.location.href);
		const bits = url.searchParams.get(this.paramName) ?? defaultOverlays;
		console.log('Overlay bits from URL:', bits);

		const overlays = this.getOverlays();

		overlays.forEach((layer, index) => {
			console.log(bits.charAt(index));
			if ((bits.charAt(index) || '1') === '1') {
				layer.addTo(this.map);
			} else {
				layer.removeFrom(this.map);
				// TODO: assert this.map.hasLayer(layer) False
			}
		});
	}
}
