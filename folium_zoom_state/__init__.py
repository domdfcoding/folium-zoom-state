#!/usr/bin/env python3
#
#  __init__.py
"""
Folium plugin to preserve zoom level and map position when reloading or sharing URLs.
"""
#
#  Copyright © 2026 Dominic Davis-Foster <dominic@davis-foster.co.uk>
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#  DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#  OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
#  OR OTHER DEALINGS IN THE SOFTWARE.
#

__author__: str = "Dominic Davis-Foster"
__copyright__: str = "2026 Dominic Davis-Foster"
__license__: str = "MIT License"
__version__: str = "0.1.0b4"
__email__: str = "dominic@davis-foster.co.uk"

# 3rd party
import folium
from domdf_folium_tools.template import SubclassingTemplate
from domdf_python_tools.compat import importlib_resources
from folium.elements import JSCSSMixin
from folium.map import Layer
from folium.template import Template

__all__ = [
		"BasemapFromURL",
		"BasemapState",
		"OverlayState",
		"StateBase",
		"ZoomStateJS",
		"ZoomStateJSEmbedded",
		"ZoomStateJSExternal",
		"ZoomStateMap",
		"get_js_script",
		]


def get_js_script() -> str:
	"""
	Get the zoom state script as a string.
	"""

	script = importlib_resources.read_text("folium_zoom_state", "zoom_state.js")
	script = script.replace("\nexport function", "\nfunction")
	return '\n'.join([line for line in script.splitlines() if not line.startswith("//")])


class ZoomStateJS(JSCSSMixin, folium.MacroElement):
	"""
	Update URL with current zoom/position.

	Javascript code is loaded from the jsdelivr cdn.

	:param setup_basemap_state: If :py:obj:`True` will also update URL with current basemap name.
	:param basemap_state_param_name: The URL query parameter to use for tracking basemap state.
	"""

	_template = Template(
			"""
		{% macro script(this, kwargs) %}
			{{ this.js_script }}
			setupZoomState({{this._parent.get_name()}});
			{% if this.setup_basemap_state %}
			setupBasemapState({{this._parent.get_name()}}, {{this.basemap_state_param_name|tojson}});
			{% endif %}
		{% endmacro %}
		""",
			)

	def __init__(self, setup_basemap_state: bool = False, basemap_state_param_name: str = "basemap"):
		super().__init__()
		self._name = "ZoomStateJS"
		self.js_script = ''
		self.setup_basemap_state = setup_basemap_state
		self.basemap_state_param_name = basemap_state_param_name

	default_js = [
			(
					"zoom_state_js",
					f"https://cdn.jsdelivr.net/gh/domdfcoding/folium-zoom-state@v{__version__}/folium_zoom_state/zoom_state.min.js",
					),
			]


class ZoomStateJSExternal(ZoomStateJS):
	"""
	Update URL with current zoom/position.

	Javascript code is not embedded, to allow loading it from an external file.
	Obtain the code with :func:`~.get_js_script` or copy the bundled ``zoom_state.js`` file.

	:param setup_basemap_state: If :py:obj:`True` will also update URL with current basemap name.
	"""

	default_js = []


class ZoomStateJSEmbedded(ZoomStateJSExternal):
	"""
	Update URL with current zoom/position.

	:param setup_basemap_state: If :py:obj:`True` will also update URL with current basemap name.
	"""

	def __init__(self, setup_basemap_state: bool = False):
		super().__init__(setup_basemap_state)
		self.js_script = get_js_script()


class StateBase(folium.MacroElement):
	"""
	Base class for basemap and overlay state tracking.

	Add to map after adding the layer control.

	:param layer_control: The layer control element.
	:param param_name: The URL query parameter to use.
	"""

	def __init__(self, layer_control: folium.LayerControl, param_name: str):
		super().__init__()
		self._name = "StateBase"
		self.layer_control = layer_control
		self.param_name = param_name


class BasemapState(StateBase):
	"""
	Inject JavaScript to track and set basemaps from URL parameter.

	Add to map after adding the layer control.

	:param default_basemap: The name of the basemap to use by default.
	:param layer_control: The layer control element.
	:param param_name: The URL query parameter to use.
	"""

	_template = Template(
			"""
		{% macro script(this, kwargs) %}
			const basemapState = new BasemapState({{this._parent.get_name()}}, {{this.layer_control.get_name()}}, {{this.param_name|tojson}})
			basemapState.fromURL({{this.default_basemap|tojson}}).addTo({{this._parent.get_name()}})
			basemapState.setup();
		{% endmacro %}
		""".replace('\t', "    "),
			)

	def __init__(self, default_basemap: str, layer_control: folium.LayerControl, param_name: str = "basemap"):
		super().__init__(layer_control=layer_control, param_name=param_name)
		self._name = "BasemapState"
		self.default_basemap = default_basemap


class BasemapFromURL(BasemapState):
	"""
	Inject JavaScript to set basemap from URL parameter.

	Add to map after adding the layer control.

	:param default_basemap: The name of the basemap to use by default.
	:param layer_control: The layer control element.
	:param param_name: The URL query parameter to use.
	"""

	_template = Template(
			"""
		{% macro script(this, kwargs) %}
			basemapFromURL("{{this.default_basemap}}", {{this.layer_control.get_name()}}, {{this.param_name|tojson}}).addTo({{this._parent.get_name()}});
		{% endmacro %}
		""",
			)

	def __init__(self, default_basemap: str, layer_control: folium.LayerControl, param_name: str = "basemap"):
		super().__init__(default_basemap=default_basemap, layer_control=layer_control, param_name=param_name)
		self._name = "BasemapFromURL"


class OverlayState(StateBase):
	"""
	Inject JavaScript to track and set overlay layers from URL parameter.

	Add to map after adding the layer control.

	:param layer_control: The layer control element.
	:param param_name: The URL query parameter to use.
	"""

	_template = Template(
			"""
		{% macro script(this, kwargs) %}
			const overlayState = new OverlayState({{this._parent.get_name()}}, {{this.layer_control.get_name()}}, {{this.param_name|tojson}})
			overlayState.fromURL({{this._default_overlays_bits|tojson}})
			overlayState.setup();
		{% endmacro %}
		""".replace('\t', "    "),
			)

	def __init__(self, layer_control: folium.LayerControl, param_name: str = "overlays"):
		super().__init__(layer_control=layer_control, param_name=param_name)
		self._name = "OverlayState"

	def render(self, **kwargs) -> None:  # type: ignore[override]  # False positive  # noqa: D102

		bits = ''

		assert self.layer_control._parent is not None

		for item in self.layer_control._parent._children.values():
			if not isinstance(item, Layer) or not item.control or not item.overlay:
				continue

			if item.show:
				bits += '1'
			else:
				bits += '0'

		self._default_overlays_bits = bits

		super().render(**kwargs)


class ZoomStateMap(folium.Map):
	"""
	Custom folium map that restores zoom level and map position from URL parameters.
	"""

	_template = SubclassingTemplate(
			"""
        {% macro script(this, kwargs) %}
            var mapOptions = {{this.options|tojavascript}};
            var defaultZoom = mapOptions["zoom"] ?? 0;
            var urlZoomState = zoomStateFromURL(defaultZoom, L.latLng({{ this.location|tojson }}));
            mapOptions["zoom"] = urlZoomState["zoomLvl"]

            var {{ this.get_name() }} = L.map(
                {{ this.get_name()|tojson }},
                {
                    center: urlZoomState["centre"],
                    crs: L.CRS.{{ this.crs }},
                    ...mapOptions

                }
            );

            {%- if this.control_scale %}
            L.control.scale().addTo({{ this.get_name() }});
            {%- endif %}

            {%- if this.zoom_control_position %}
            L.control.zoom( { position: {{ this.zoom_control|tojson }} } ).addTo({{ this.get_name() }});
            {%- endif %}

            {% if this.objects_to_stay_in_front %}
            function objects_in_front() {
                {%- for obj in this.objects_to_stay_in_front %}
                    {{ obj.get_name() }}.bringToFront();
                {%- endfor %}
            };
            {{ this.get_name() }}.on("overlayadd", objects_in_front);
            $(document).ready(objects_in_front);
            {%- endif %}

        {% endmacro %}
        """,
			base_template=folium.Map._template,
			)
