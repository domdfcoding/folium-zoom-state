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
__version__: str = "0.0.0"
__email__: str = "dominic@davis-foster.co.uk"

# stdlib
from typing import TYPE_CHECKING

# 3rd party
import folium
from domdf_python_tools.compat import importlib_resources
from folium.template import Template

if TYPE_CHECKING:
	# 3rd party
	from jinja2.environment import TemplateModule

__all__ = ["ZoomStateJS"]


def get_js_script() -> str:
	script = importlib_resources.read_text("folium_zoom_state", "zoom_state.js")
	script = script.replace("\nexport function", "\nfunction")
	return '\n'.join([line for line in script.splitlines() if not line.startswith("//")])


class ZoomStateJS(folium.MacroElement):
	"""
	Update URL with current zoom/position.
	"""

	_template = Template(
			"""
		{% macro script(this, kwargs) %}
			{{ this.js_script }}
			setupZoomState({{this._parent.get_name()}});
		{% endmacro %}
		""",
			)

	def __init__(self):
		super().__init__()
		self._name = "ZoomStateJS"
		self.js_script = get_js_script()


class SubclassingTemplate(Template):
	base_template: Template

	def __new__(cls, source: str, base_template: Template):
		self = super().__new__(cls, source)
		self.base_template = base_template
		return self

	@property
	def module(self) -> "TemplateModule":
		template_module = super().module
		module_dict = template_module.__dict__

		for macro in {"html", "header", "script"}:
			if module_dict.get(macro, None) is None:
				module_dict[macro] = self.base_template.module.__dict__.get(macro, None)

		return template_module


class ZoomStateMap(folium.Map):
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
