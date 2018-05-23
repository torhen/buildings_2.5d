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
		self.legend_dict = {}

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
		""" add all markers one by one to the dictionary"""

		self.slider_marker_dict[layer_name] = []

		S.getJSON(url,  lambda json: call_back(json) )

		def call_back(json):
			# add data of markers to slider_marker_dict, create time defines the order!!!
			i=0
			self.slider_marker_dict[layer_name] = []
			for feat in json.features:
				i = i + 1
				lon, lat = feat.geometry.coordinates


				opt = {}
				opt['radius'] = 4
				opt['color'] = color
				opt['time'] = feat.properties.time

				marker_data = {
					'lon' : lon,
					'lat' : lat,
					'color' : color,
					'time' : feat.properties.time,
					'info' : feat.properties.info,
					'opt' : opt
				}

				self.slider_marker_dict[layer_name].append(marker_data)

			self.redraw_slider_layer()

		self.legend_dict[layer_name] = color
		self.draw_legend()
			
	def redraw_slider_layer(self):
		# empty the slider_layer_group
		#self.slider_layer_group.clearLayers()

		self.map.removeLayer(self.slider_layer_group)
		self.slider_layer_group = window.L.layerGroup()
		self.slider_layer_group.addTo(self.map)


		# add the marker to the slider_layer_group, in the right order
		sorted_keys = self.slider_marker_dict.keys()
		sorted_keys.sort()
		i = 0
		for key in sorted_keys:
			marker_list = self.slider_marker_dict[key]
			for marker_data in marker_list:
				i = i + 1
				marker = window.L.circleMarker([marker_data.lat, marker_data.lon], marker_data.opt).bindPopup(marker_data.info)
				marker.addTo(self.slider_layer_group)

		self.refresh_slider()


	def remove_slider_marker(self, layer_name):
		self.slider_marker_dict[layer_name] = []
		self.redraw_slider_layer()
		del self.legend_dict[layer_name]
		self.draw_legend()

	def empty_slider_layer(self):
		self.slider_marker_dict = {}
		self.redraw_slider_layer()
		self.legend_dict = {}
		self.draw_legend()

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


	def draw_legend(self):
		S('#legend').empty()
		for key in sorted(self.legend_dict.keys()):
			color = self.legend_dict[key]
			s = f"<font color='{color}'>&#x26AB;</font> {key} "  # mediuum circle &#x26AB; full moon &#x1F311;

			s += f'<a href="http://network/track/P3/csv/{key}.csv">csv</a> '
			s += f'<a href="http://network/track/P3/ge/{key}.kml">kml</a> '
			s += f'<a href="http://network/track/P3/tab/{key}.zip">tab</a><br>'


			S('#legend').append(s)
			#console.log(s)

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

class Listbox:
	def __init__(self, dest, id, options, fkt_change):
		self.id = id
		self.fkt_change = fkt_change
		s = f'<select id="{id}" size="1" style="width:200px">'
		for option in options:
			s = s + f"<option>{option}</option>"
		s = s + "</select><br>"
		S(dest).append(s)
		S('#' + self.id).change(self.onchange)
		# trigger initial event
		S('#' + self.id).trigger( "change")

	def onchange(self, e):
		selected = e.target.value
		self.fkt_change(selected)
		#self.fkt_change()



def make_all_overlay_checkbox(map, def_layers):

	def make_cb(map, layer_name, url, color):
		style = {
			'color':color,
			'fillColor':color,
			'fillOpacity':0.1,
			'stroke': True,
			'fill': True,
		}
		Checkbox(
			dest = '#overlays', 
			id = 'cb_' + layer_name, 
			title = f'<font color="{color}">&#x25C4;</font>{layer_name}', 
			
			fkt_check = lambda : map.add_vectorgrid_file(layer_name, url, style), 
			fkt_uncheck = lambda : map.remove_layer(layer_name)
			)

	for key in def_layers.keys():
		layer_name = key
		url = def_layers[key][0]
		color = def_layers[key][1]
		make_cb(map, layer_name, url, color)


def make_all_track_checkbox(map, folder, json):

	def make_cb(title, folder, file_base, color):
		Checkbox(
			dest = '#tracks', 
			id = f'cb_{file_base}', 
			title = title, 
			
			fkt_check =  lambda : map.add_to_slider_layer(f'{file_base}',f'track_data/{folder}/geojson/{file_base}.geo.json', color=color),
			fkt_uncheck = lambda : map.remove_slider_marker(f'{file_base}')
			)
	# folder = 'P3'
	for item in json:
		file_base = item.base

		weekday = int(item.weekday)

		lcolors = ['red',  'crimson', 'green', 'blue', 'purple', 'lime', 'cyan']
		color = lcolors[weekday]

		if int(item.weekday) >= 5:
			title = f"<b>{item.base} ({item.call_count})</b>"
		else:
			title = f"{item.base} ({item.call_count})"			

		make_cb(title, folder, file_base, color)

def make_group_select(map):

	def update_list(folder):
		S('#tracks').empty()
		S.getJSON(f'track_data/{folder}/geojson/_index.json', lambda json: make_all_track_checkbox(map, folder, json))
		map.empty_slider_layer()

	Listbox(dest='#overlays', 
	id='id_chooser', 
	options=['P3', 'test', 'chip'], 
	fkt_change = lambda selected: update_list(selected)
	)




def main():

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

	map = Leaflet('map')
	map.set_view(8.23425, 46.81886, 8)
	map.add_tile_layer('off', 'data/empty.png', gray=False)
	map.add_tile_layer('toner', 'http://{s}.tile.stamen.com/toner/{z}/{x}/{y}.png', gray=False, style={'opacity':0.5})
	map.add_tile_layer('osm', 'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',  gray=False)
	map.add_tile_layer('osm-gray', 'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', gray=True)
	map.add_geojson_file('Sites', 'data/sites.json', {'color':'#d77d00'}, True)

	make_all_overlay_checkbox(map, def_layers)
	make_group_select(map)



main()



