#__pragma__ ('alias', 'S', '$')
#__pragma__ ('kwargs')

# -------- Needed Includes ------------
# <script src="jquery/jquery.min.js"></script>
# <script src="leaflet/leaflet.js"></script>
# <script src="grayscale/TileLayer.Grayscale.js"></script>
# <script src="https://unpkg.com/leaflet.vectorgrid@latest/dist/Leaflet.VectorGrid.bundled.js"></script>
# <link rel="stylesheet" href="leaflet-search/src/leaflet-search.css" />
# <script src="leaflet-search/src/leaflet-search.js"></script>


class Leaflet:
	def __init__(self, div_name):
		if not hasattr(window, 'L'):
			console.log('ERROR: include leaflet.css, leaflet.js')

		self.map = L.map('map');
		self.map.setView([0, 0], 0)
		self.base_layers = {}
		self.overlay_layers = {}
		self.layer_control = window.L.control.layers({}, {}).addTo(self.map)
		self.slider_layer_group = window.L.layerGroup()
		self.slider_layer_group.addTo(self.map)
		self.slider_marker_dict = {}

	def add_tile_layer(self, name, url, gray=False, style={}):

		if gray:
			layer = window.L.tileLayer.grayscale(url, style)
		else:
			layer = window.L.tileLayer(url, style)
			

		self.base_layers[name] = layer
		layer.addTo(self.map)
		self.layer_control.addBaseLayer(layer, name)

	def set_view(self, lon, lat, zoom):
		self.map.setView([lat, lon], zoom);

	def add_geojson_file(self, layer_name, url, style, add_search_control=False, add_to_slider=False):
		S.getJSON(url,  
		lambda json: self.add_geojson_file_callback(json , layer_name, style, add_search_control)
	    )

	def add_geojson_file_callback(self, json, layer_name, style, add_search_control, add_to_slider):
		on_each_feature = lambda feature, layer : layer.bindPopup(feature.properties.info)
		layer = window.L.geoJSON(json, {'style': style, 'onEachFeature' : on_each_feature})

		layer.addTo(self.map)
		self.overlay_layers[layer_name] = layer

		if add_search_control:
			self.layer_control.addOverlay(layer, layer_name)
			self.add_search_control(layer)
		
	def add_vectorgrid_file(self, layer_name, url, style={}):
		console.log('loading', layer_name)
		layer = S.getJSON(url, lambda json: self.add_vectorgrid_file_callback(json, layer_name, style))


	def add_vectorgrid_file_callback(self, json,  layer_name, style):
		tileOptions = {
            'maxZoom': 20,  # max zoom to preserve detail on
            'tolerance': 5, # simplification tolerance (higher means simpler)
            'extent': 4096, # tile extent (both width and height)
            'buffer': 64,   # tile buffer on each side
            'debug': 0,      # logging level (0 to disable, 1 or 2)
            'indexMaxZoom': 0,        # max zoom in the initial tile index
            'indexMaxPoints': 100000, # max number of points per tile in the index
			'interactive': True,
			'vectorTileLayerStyles' : {
					'sliced': style
			}
		}

		layer = window.L.vectorGrid.slicer(json, tileOptions)
		layer.addTo(self.map) 
		self.layer_control.addOverlay(layer, layer_name)
		self.overlay_layers[layer_name] = layer
		layer.on('click', self.on_object_click)

	def remove_layer(self, layer_name):
		layer = self.overlay_layers[layer_name]
		self.map.removeLayer(layer)
		self.layer_control.removeLayer(layer)

	@staticmethod
	def on_object_click(e):
			properties = e.layer.properties
			window.L.popup().setContent(properties.info).setLatLng(e.latlng).openOn(map.map)


	def add_search_control(self, layer):
		# run if layer is fully loaded
		para = {
		'position':'topright',		
		'layer': layer,
		'initial': False,
		'zoom': 17,
		'marker': False,
		'propertyName': 'info'
		}

		controlSearch = window.L.control.search(para)
		self.map.addControl( controlSearch )

	def add_to_slider_layer(self, layer_name, url, color):
		""" add all markers one by one to the slider_layer_group"""

		self.slider_marker_dict[layer_name] = []

		S.getJSON(url,  lambda json: my_callback(json) )

		def my_callback(json):
			# add markes to slider_marker_dict
			i=0
			self.slider_marker_dict[layer_name] = []
			for feat in json.features:
				i = i + 1
				lon, lat = feat.geometry.coordinates

				opt = {}
				opt['radius'] = 4
				opt['color'] = color
				opt['time'] = f'marker #{i}'

				marker = window.L.circleMarker([lat, lon], opt).bindPopup('text')
				#marker.addTo(self.slider_layer_group)

				# save them in dictionary so we can remove the markers
				self.slider_marker_dict[layer_name].append(marker)

			self.redraw_slider_layer()
			
	def redraw_slider_layer(self):
		# empty the slider_layer_group
		self.slider_layer_group.clearLayers()

		# add the marker to the slider_layer_group, in the right order
		sorted_keys = sorted(self.slider_marker_dict.keys())
		i = 0
		for key in sorted_keys:
			marker_list = self.slider_marker_dict[key]
			for marker in marker_list:
				i = i + 1
				marker.addTo(self.slider_layer_group)

		self.refresh_slider()
	


	def remove_slider_marker(self, layer_name):
		self.slider_marker_dict[layer_name] = []
		self.redraw_slider_layer()

	def refresh_slider(self):
		""" delete slider if exists and buitd new from scratch"""
		para = {
			'position' : "topleft",
			'layer' : self.slider_layer_group,
			'range' : True,
			'showAllOnStart': True

		}


		sliderControl = window.L.control.sliderControl(para)
		self.map.addControl(sliderControl)
		sliderControl.startSlider()

class Button:
	def __init__(self, dest, id, title, fkt_click):
		s = '<button id="{id}">{title}</button><br>'.format(id=id, title=title)
		S(dest).append(s)
		S('#'+id).click(fkt_click)


class Checkbox:
	def __init__(self, dest, id, title, fkt_check, fkt_uncheck):
		self.id = id
		s = f'<input type="checkbox" id="{id}">{title}</input><br>'

		self.fkt_check = fkt_check
		self.fkt_uncheck = fkt_uncheck

		S(dest).append(s)
		S('#' + self.id).click(self.onclick)

	def onclick(self):
		status = S('#' + self.id).prop('checked')

		if status:
			self.fkt_check()
		else:
			self.fkt_uncheck()


map = Leaflet('map')
map.set_view(8.23425, 46.81886, 8)
map.add_tile_layer('off', 'data/empty.png', gray=False)
map.add_tile_layer('toner', 'http://{s}.tile.stamen.com/toner/{z}/{x}/{y}.png', gray=False, style={'opacity':0.5})
map.add_tile_layer('osm', 'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',  gray=False)
map.add_tile_layer('osm-gray', 'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', gray=True)
map.add_geojson_file('Sites', 'data/sites.json', {'color':'#d77d00'}, True)


def_layers = {
	#'Sites'     : ['sites/sites.json', '#ff7800'],
	'G0900'     : ['data/sectors_G0900.json', '#ff0000'],
	'G1800'     : ['data/sectors_G1800.json', '#ff00ff'], 
	'U0900'     : ['data/sectors_U0900.json', '#0000ff'], 
	'U2100'     : ['data/sectors_U2100.json', '#00ffff'], 
	'L0800'     : ['data/sectors_L0800.json', '#008000'], 
	'L0900'     : ['data/sectors_L0900.json', '#009000'], 
	'L1800'     : ['data/sectors_L1800.json', '#ff00ff'],
	'L2100'     : ['data/sectors_L2100.json', '#99ff33'], 
	'L2600'     : ['data/sectors_L2600.json', '#ffff00'],
	'Community' : ['data/Community.json'    , '#000000'],
	'Builtouts' : ['data/builtouts.json'    , '#ff0000']
}

def create_checkbox(layer_name, url, color):

	style = {
		'color':color,
		'fillColor':color,
		'fillOpacity':0.1,
		'stroke': True,
		'fill': True,
	}
	Checkbox(
		dest = '#nav', 
		id = 'cb_' + layer_name, 
		title = f'<font color="{color}">&#x25C4;</font>{layer_name}', 
		
		fkt_check = lambda : map.add_vectorgrid_file(layer_name, url, style), 
		fkt_uncheck = lambda : map.remove_layer(layer_name)
		)



for key in def_layers.keys():
	layer_name = key
	url = def_layers[key][0]
	color = def_layers[key][1]
	create_checkbox(layer_name, url, color)

def make_cb(layer_name, color):
	Checkbox(
		dest = '#nav', 
		id = f'cb_{layer_name}', 
		title = f'{layer_name}', 
		
		fkt_check =  lambda : map.add_to_slider_layer(f'{layer_name}',f'track_data/P3/geojson/{layer_name}.geo.json', color=color),
		fkt_uncheck = lambda : map.remove_slider_marker(f'{layer_name}')
		)


make_cb('2018-05-17_P3', '#ff0000')
make_cb('2018-05-16_P3', '#00ff00')
make_cb('2018-05-15_P3', '#0000ff')

Button('#nav', 'btn1', 'slider', lambda : map.refresh_slider())

