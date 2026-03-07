# 3rd party
import folium
from coincidence.regressions import AdvancedFileRegressionFixture
from folium.template import Template

# this package
from folium_zoom_state import ZoomStateJS, ZoomStateMap, set_branca_random_seed


def test_default_map(advanced_file_regression: AdvancedFileRegressionFixture):
	set_branca_random_seed("ZOOM")

	m = ZoomStateMap(location=(45.5236, -122.6750))
	ZoomStateJS().add_to(m)

	root = m.get_root()
	html = root.render()
	advanced_file_regression.check(html, extension=".html")


class Map(folium.Map):  # noqa: D101
	_template = Template(
			"""
{% macro header(this, kwargs) %}

    <style>
        #{{ this.get_name() }} {
            position: {{this.position}};
            width: {{this.width[0]}}{{this.width[1]}};
            height: {{this.height[0]}}{{this.height[1]}};
            left: {{this.left[0]}}{{this.left[1]}};
            top: {{this.top[0]}}{{this.top[1]}};
        }
        .leaflet-container { font-size: {{this.font_size}}; }
    </style>

    <script>
        L_NO_TOUCH = {{ this.global_switches.no_touch |tojson}};
        L_DISABLE_3D = {{ this.global_switches.disable_3d|tojson }};
    </script>

{% endmacro %}

{% macro html(this, kwargs) %}
    <div class="folium-map sidebar-map" id={{ this.get_name() |tojson }}>
    </div>
{% endmacro %}

{% macro script(this, kwargs) %}
    const canvasRenderer = L.canvas({
        tolerance: 2
    });

    var mapOptions = {{this.options|tojavascript}};
    var defaultZoom = mapOptions["zoom"] ?? 0;
    var urlZoomState = zoomStateFromURL(defaultZoom, L.latLng({{ this.location|tojson }}));
    mapOptions["zoom"] = urlZoomState["zoomLvl"]

    var {{ this.get_name() }} = L.map(
        {{ this.get_name()|tojson }},
        {
            center: urlZoomState["centre"],
            crs: L.CRS.{{ this.crs }},
            renderer: canvasRenderer,
            closePopupOnClick: true,
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
        document.addEventListener("DOMContentLoaded", objects_in_front, false);
    {%- endif %}

{% endmacro %}

""",
			)


def test_custom_map(advanced_file_regression: AdvancedFileRegressionFixture):
	set_branca_random_seed("ZOOM")

	m = Map(location=(45.5236, -122.6750))
	ZoomStateJS().add_to(m)

	root = m.get_root()
	html = root.render()
	advanced_file_regression.check(html, extension=".html")
