'use strict';
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
function updateQueryStringParam (key, value) {
	const url = new URL(window.location.href);
	url.searchParams.set(key, value.toString()); // Add or update the parameter
	// window.history.pushState({}, null, url);
	window.history.replaceState({}, '', url);
}
// eslint-disable-next-line @typescript-eslint/no-unused-vars
function setupZoomState (map) {
	map.on('zoomend', function () {
		const zoomLvl = map.getZoom();
		updateQueryStringParam('zoom', zoomLvl);
	});
	map.on('moveend', function () {
		const centre = map.getCenter();
		updateQueryStringParam('lat', centre.lat);
		updateQueryStringParam('lng', centre.lng);
	});
}
// eslint-disable-next-line @typescript-eslint/no-unused-vars
function zoomStateFromURL (defaultZoom, defaultCentre) {
	const url = new URL(window.location.href);
	// let zoomLvl = map.getZoom();
	let zoomLvl = defaultZoom;
	if (url.searchParams.has('zoom')) {
		zoomLvl = parseInt(url.searchParams.get('zoom'));
	}
	// const centre = map.getCenter();
	const centre = defaultCentre;
	if (url.searchParams.has('lat')) {
		centre.lat = parseFloat(url.searchParams.get('lat'));
	}
	if (url.searchParams.has('lng')) {
		centre.lng = parseFloat(url.searchParams.get('lng'));
	}
	return { centre, zoomLvl };
}
// eslint-disable-next-line @typescript-eslint/no-unused-vars
function basemapFromURL (defaultBasemap, layerControl) {
	let _a;
	const url = new URL(window.location.href);
	const basemapLayers = Object.fromEntries(
		/* @ts-expect-error _layers does exist but is private */
		layerControl._layers.map((element) => [element.name, element.layer]));
	if (url.searchParams.has('basemap')) {
		const basemapName = (_a = url.searchParams.get('basemap')) !== null && _a !== void 0 ? _a : defaultBasemap;
		console.log(basemapName);
		if (basemapName in basemapLayers) {
			return basemapLayers[basemapName];
		}
	}
	return basemapLayers[defaultBasemap];
}
// eslint-disable-next-line @typescript-eslint/no-unused-vars
function setupBasemapState (map) {
	map.on('baselayerchange', (e) => updateQueryStringParam('basemap', e.name));
}
// eslint-disable-next-line @typescript-eslint/no-unused-vars
class OverlayState {
	constructor (map, layerControl) {
		this.map = map;
		this.layerControl = layerControl;
	}

	getOverlays () {
		const overlays = [];
		/* @ts-expect-error _layers does exist but is private */
		this.layerControl._layers.forEach((layer) => {
			if (layer.overlay) {
				overlays.push(layer.layer);
			}
		});
		return overlays;
	}

	updateOverlayParams () {
		const overlays = this.getOverlays();
		let bits = '';
		overlays.forEach((layer) => {
			if (this.map.hasLayer(layer)) {
				bits += '1';
			} else {
				bits += '0';
			}
		});
		console.log('Overlay bits:', bits);
		updateQueryStringParam('overlays', bits);
	}

	setup () {
		this.map.on('overlayadd', this.updateOverlayParams, this);
		this.map.on('overlayremove', this.updateOverlayParams, this);
	}

	fromURL (defaultOverlays) {
		let _a;
		const url = new URL(window.location.href);
		const bits = (_a = url.searchParams.get('overlays')) !== null && _a !== void 0 ? _a : defaultOverlays;
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
