# coding: UTF-8
import psycopg2
from pg_connexion import get_pgc
import urllib,urllib2
import os
import xml.etree.ElementTree as ET

class Dicts:
	def __init__(self):
		self.lettre_a_lettre = {}
		self.fantoir = {}
		self.osm_insee = {}
		self.abrev_type_voie = {}
		self.abrev_titres = {}
		self.chiffres = []
		self.chiffres_romains = []
		self.mot_a_blanc = []
		self.abrev_titres = {}
		self.noms_voies = {}
	def load_lettre_a_lettre(self):
		self.lettre_a_lettre = {'A':[u'Â',u'À'],
						'C':[u'Ç'],
						'E':[u'È',u'Ê',u'É',u'Ë'],
						'I':[u'Ï',u'Î'],
						'O':[u'Ö',u'Ô'],
						'U':[u'Û',u'Ü']}
	def load_fantoir(self,insee):
		fndep = insee[0:2]+'0.txt'
		h = open(fndep,'r')
		dictFantoir = {}
		insee_com = insee[2:5]
		for l in h:
		# hors commune
			if l[3:6] != insee_com:
				continue
		# enregistrement != Voie
			if l[108:109] == ' ':
				continue
		# voie annulée
			if l[73:74] != ' ':
				continue
			cle = ' '.join((l[11:15].rstrip().lstrip()+' '+l[15:41].rstrip().lstrip()).replace('-',' ').lstrip().split())
			cle = normalize(cle)
			self.fantoir[cle] = l[0:2]+l[3:11]
			self.add_voie('fantoir',cle)
		h.close()
	def load_chiffres(self):
		self.chiffres = [	['0','ZERO'],
							['1','UN'],
							['2','DEUX'],
							['3','TROIS'],
							['4','QUATRE'],
							['5','CINQ'],
							['6','SIX'],
							['7','SEPT'],
							['8','HUIT'],
							['9','NEUF'],
							[' DIX ',' UNZERO '],
							[' ONZE ',' UNUN '],
							[' DOUZE ',' UNDEUX ']]
	def load_mot_a_blanc(self):
		self.mot_a_blanc = ['DE LA',
							'DU',
							'DES',
							'LE',
							'LA',
							'LES',
							'DE',
							'D']
	def load_abrev_titres(self):
		self.abrev_titres = [['MARECHAL','MAL'],
							['PRESIDENT','PDT'],
							['GENERAL','GAL'],
							['COMMANDANT','CDT'],
							['CAPITAINE','CAP'],
							['REGIMENT','REGT'],
							['SAINTE','STE'],
							['SAINT','ST']]
	def load_chiffres_romains(self):
		self.chiffres_romains = {	'XXIII':'DEUXTROIS',
									'XXII' :'DEUXDEUX',
									'XXI'  :'DEUXUN',
									'XX'   :'DEUXZERO',
									'XIX'  :'UNNEUF',
									'XVIII':'UNHUIT',
									'XVII' :'UNSEPT',
									'XVI'  :'UNSIX',
									'XV'   :'UNCINQ',
									'XIV'  :'UNQUATRE',
									'XIII' :'UNTROIS',
									'XII'  :'UNDEUX',
									'XI'   :'UNUN',
									'X'    :'UNZERO',
									'IX'   :'NEUF',
									'VIII' :'HUIT',
									'VII'  :'SEPT',
									'VI'   :'SIX',
									'V'    :'CINQ',
									'IV'   :'QUATRE',
									'III'  :'TROIS',
									'II'   :'DEUX',
									'I'    :'UN'}
	def load_abrev_type_voie(self):
		fn = 'abrev_type_voie.txt'
		f = open(fn)
		for l in f:
			c = (l.splitlines()[0]).split('\t')
			self.abrev_type_voie[c[0]] = c[1]
		f.close()
	def load_osm_insee(self):
		finsee = open('osm_id_ref_insee.csv','r')
		for e in finsee:
			c = (e.splitlines()[0]).split(',')
			self.osm_insee[str(c[1])] = int(c[0])
		finsee.close()
	def load_all(self,code_insee_commune):
		self.load_lettre_a_lettre()
		self.load_abrev_type_voie()
		self.load_abrev_titres()
		self.load_chiffres()
		self.load_chiffres_romains()
		self.load_mot_a_blanc()
		self.load_osm_insee()
		self.load_fantoir(code_insee_commune)
	def add_voie(self,origine,nom):
		cle = normalize(nom)
		if not cle in self.noms_voies:
			self.noms_voies[cle] = {}
		self.noms_voies[cle][origine] = nom
		
def get_part_debut(s,nb_parts):
	resp = ''
	if get_nb_parts(s) > nb_parts:
		resp = ' '.join(s.split()[0:nb_parts])
	return resp
def get_nb_parts(s):
	return len(s.split())
def replace_type_voie(s,nb):
	sp = s.split()
	spd = ' '.join(sp[0:nb])
	spf = ' '.join(sp[nb:len(sp)])
	s = dicts.abrev_type_voie[spd]+' '+spf
	return s
def normalize(s):
	s = s.upper()				# tout en majuscules
	s = s.replace('-',' ')		# separateur espace
	s = s.replace('\'',' ')		# separateur espace
	s = s.replace('/',' ')		# separateur espace
	s = ' '.join(s.split())		# separateur : 1 espace
	for l in iter(dicts.lettre_a_lettre):
		for ll in dicts.lettre_a_lettre[l]:
			s = s.replace(ll,l)
	
	# type de voie
	abrev_trouvee = False
	p = 0
	while (not abrev_trouvee) and p < 3:
		p+= 1
		if get_part_debut(s,p) in dicts.abrev_type_voie:
			s = replace_type_voie(s,p)
			abrev_trouvee = True

	# ordinal
	s = s.replace(' EME ','EME ')

	# chiffres
	for c in dicts.chiffres:
		s = s.replace(c[0],c[1])

	# articles
	for c in dicts.mot_a_blanc:
		s = s.replace(' '+c+' ',' ')

	# titres, etc.
	for r in dicts.abrev_titres:
		s = s.replace(' '+r[0]+' ',' '+r[1]+' ')

	# chiffres romains
	sp = s.split()

	if sp[-1] in dicts.chiffres_romains:
		sp[-1] = dicts.chiffres_romains[sp[-1]]
		s = ' '.join(sp)
			
	return s

def get_line_in_st_line_format(nodelist):
	s = 'ST_LineFromText(\'LINESTRING('
	l_coords = []
	for id in nodelist:
		l_coords.append(str(nodes.n[id].lon)+' '+str(nodes.n[id].lat))
	s = s+','.join(l_coords)+')\')'
	return s
class Node:
	def __init__(self,lon,lat,id,version,tags):
		self.lon = lon
		self.lat = lat
		self.id = id
		self.version = version
		self.tags = tags
	def get_geom_as_text(self):
		strp = 'ST_PointFromText(\'POINT('+str(self.lon)+' '+str(self.lat)+')\',4326)'
		return strp
	def get_as_osm_xml_node(self,is_closed,is_modified):
		s_modified = ""
		if is_modified:
			s_modified = " \"action\"=\"modified\" "
		s = "\t<node id=\""+str(self.id)+"\" "+s_modified+"lat=\""+str(self.lat)+"\" lon=\""+str(self.lon)+"\" version=\""+str(self.version)+"\""
		if len(self.tags) == 0 and is_closed:
			s = s+"/>\n"
		else:
			s = s+">\n"
			for k in sorted(self.tags.viewkeys()):
				s = s+"\t\t<tag k=\""+k+"\" v=\""+self.tags[k].encode('utf8')+"\"/>\n"
			if is_closed:
				s = s+"</node>\n"
		return s

class Nodes:
	def __init__(self):
		self.n = {}
		self.min_id = 0
	def load_xml_node(self,xml_node,tags):
		id = xml_node.get('id')
		self.n[id]= Node(xml_node.get('lon'),xml_node.get('lat'),id,xml_node.get('version'),tags)
		self.min_id = min(self.min_id,int(id))
	def load_new_node_from_xml(self,xml_node):
		n = self.add_new_node(xml_node.get('lon'),xml_node.get('lat'))
		return nodes.n[n]
	def add_new_node(self,lon,lat):
		id = str(self.min_id - 1)
		self.n[id] = Node(lon,lat,id,'0',{})
		self.min_id = min(self.min_id,int(id))
		return id
class PolyGeom:
	def __init__(self):
		self.a_nodes = []
	
	def add_geom(self,a_nodes):
		self.a_nodes = a_nodes
		
	def get_geom_as_linestring_text(self):
		res = '\'LINESTRING('
		a_n = []
		for ni in self.a_nodes:
			a_n.append(str(nodes.n[ni].lon)+' '+str(nodes.n[ni].lat))
		res = res+','.join(a_n)+')\''
		return res	
class Building:
	def __init__(self,geom,tags):
		self.geom = geom
		self.tags = tags
		if len(self.geom.a_nodes) > 2 and self.geom.a_nodes[0] == self.geom.a_nodes[-1]:
			self.is_valid_geom = True
		else:
			self.is_valid_geom = False
			print('******** Polygone invalide : a reparer ou supprimer, en lien avec le node http://www.osm.org/node/'+self.geom.a_nodes[0])
class Buildings:
	def __init__(self):
		self.b = {}
	def add_building(self,b,id):
		self.b[id] = b
class Parcelle:
	def __init__(self,geom,numero,voie):
		self.geom = geom
		self.numero = numero
		self.voie = voie
class Parcelles:
	def __init__(self):
		self.p = {}
	def add_parcelle(self,p,id):
		if id in self.p:
			self.p[id]=self.p[id]+[p]
		else:
			self.p[id]=[p]
class Adresse:
	def __init__(self,node,num,voie):
		self.node = node
		self.numero = num
		self.voie = voie
		self.buildings_id = []

	def add_building(self,b_id):
		self.buildings_id = self.buildings_id+[b_id]	
class Adresses:
	def __init__(self):
		self.a = {}
	def add_adresse(self,ad):
		cle = normalize(ad.voie)
		if not cle in self.a:
			self.a[cle] = {}
		self.a[cle][ad.numero] = ad

def get_as_osm_xml_way(node_list,tags,id,is_closed,is_modified):
	s_modified = ""
	if is_modified:
		s_modified = " \"action\"=\"modified\" "
		s = "\t<way id=\""+str(id)+"\" "+s_modified+"\" version=\""+str(self.version)+"\">\n"
		for nl in node_list:
			s = s+"\t\t<nd ref=\""+str(nl)+"\" />\n"
		for k in sorted(tags.viewkeys()):
			s = s+"\t\t<tag k=\""+k+"\" v=\""+self.tags[k].encode('utf8')+"\"/>\n"
		if is_closed:
			s = s+"</way>\n"
	return s
code_insee = raw_input('Code INSEE : ')

dicts = Dicts()
dicts.load_all(code_insee)
pgc = get_pgc('adresses')

fnparcelles = raw_input('fichier parcelles : ')
fnadresses = raw_input('fichier adresses : ')
dirout = 'fichiers_'+fnadresses.replace('.osm','')
if not os.path.exists(dirout):
	os.mkdir(dirout)
	
building_rep = 'cache_buildings'
if not os.path.exists(building_rep):
	os.mkdir(building_rep)

fnbuilding = building_rep+'/buildings_'+code_insee+'.osm'
if not os.path.exists(fnbuilding):
	building_url = urllib.quote('http://overpass-api.de/api/interpreter?data=node(area:'+str(3600000000+dicts.osm_insee[code_insee])+');way(bn);(way._["building"];node(w););out meta;',':/?=')
	building_url = building_url.replace('way._','way%2E%5F').replace('area:','area%3A')
	print("téléchargement des buildings OSM...")
	try:
		resp = urllib2.urlopen(building_url)
		fbuilding = open(fnbuilding,'wb')
		fbuilding.write(resp.read())
		fbuilding.close()
		print("ok")
	except urllib2.HTTPError:
		print('\n******* récupération KO ********')
		print('Abandon')
		os._exit(0)
		
nodes = Nodes()
buildings = Buildings()
print('mise en cache des buildings...')
print('nodes...')
xmlbuldings = ET.parse(fnbuilding)
for n in xmlbuldings.iter('node'):
	dtags = {}
	for tg in n.iter('tag'):
		dtags[tg.get('k')] = tg.get('v')
	nodes.load_xml_node(n,dtags)
print('buildings...')
for b in xmlbuldings.iter('way'):
	a_n = []
	for bn in b.iter('nd'):
		a_n.append(bn.get('ref'))
	g = PolyGeom()
	g.add_geom(a_n)
	dtags = {}
	for tg in b.iter('tag'):
		dtags[tg.get('k')] = tg.get('v')
	buildings.add_building(Building(g,dtags),b.get('id'))

print('chargement des polygones...')
cur_buildings = pgc.cursor()
str_query = '''DROP TABLE IF EXISTS tmp_building CASCADE;
				CREATE TABLE tmp_building
				(geometrie geometry,
				id double precision);
				COMMIT;'''
cur_buildings.execute(str_query)

str_query = ""
for idx,id in enumerate(buildings.b):
	if not buildings.b[id].is_valid_geom:
		continue
	str_query = str_query+'''INSERT INTO tmp_building 
						(SELECT ST_Transform(ST_SetSRID(ST_MakePolygon(ST_GeomFromText('''+(buildings.b[id].geom.get_geom_as_linestring_text())+''')),4326),2154),
						'''+id+''');'''
	if idx%100 == 0 and str_query != "":
		cur_buildings.execute(str_query+"COMMIT;")
		str_query = ""
if str_query != "":
	cur_buildings.execute(str_query+"COMMIT;")

print('chargement des segments...')
str_query = '''DROP TABLE IF EXISTS tmp_building_segments CASCADE;
				CREATE TABLE tmp_building_segments
				(geometrie geometry,
				id_building double precision,
				id_node1 double precision,
				id_node2 double precision,
				indice_node_1 integer);
				COMMIT;'''
cur_buildings.execute(str_query)

str_query = ""
for idx,id in enumerate(buildings.b):
	if not buildings.b[id].is_valid_geom:
		continue
	for nn in range(0,len(buildings.b[id].geom.a_nodes)-1):
		s_stline = get_line_in_st_line_format([buildings.b[id].geom.a_nodes[nn],buildings.b[id].geom.a_nodes[nn+1]])
		str_query = str_query+'''INSERT INTO tmp_building_segments 
						(SELECT ST_Transform(ST_SetSRID('''+s_stline+''',4326),2154),
						'''+id+''',
						'''+buildings.b[id].geom.a_nodes[nn]+''',
						'''+buildings.b[id].geom.a_nodes[nn+1]+''',
						'''+str(nn)+''');'''
		if idx%100 == 0 and str_query != "":
			cur_buildings.execute(str_query+"COMMIT;")
			str_query = ""
if str_query != "":
	cur_buildings.execute(str_query+"COMMIT;")

parcelles = Parcelles()
print('mise en cache des parcelles...')
print('nodes...')
xmlparcelles = ET.parse(fnparcelles)
for n in xmlparcelles.iter('node'):
	nodes.load_xml_node(n,{})
print('parcelles...')
for p in xmlparcelles.iter('way'):
	a_n = []
	for pn in p.iter('nd'):
		a_n.append(pn.get('ref'))
	pg = PolyGeom()
	pg.add_geom(a_n)
	addrs = {}
	for t in p.iter('tag'):
		if t.get('k')[0:4] == 'addr':
			num_addr = t.get('k').split(':')[0][4:]
			if not num_addr in addrs:
				addrs[num_addr] = {}
			addrs[num_addr][t.get('k').split(':')[1]] = t.get('v')
	for sa in addrs:
		if len(addrs[sa]) == 2:
			par = Parcelle(pg,addrs[sa]['housenumber'],normalize(addrs[sa]['street']))
			parcelles.add_parcelle(par,p.get('id'))

print('chargement...')
cur_parcelles = pgc.cursor()
str_query = '''DROP TABLE IF EXISTS tmp_parcelles CASCADE;
				CREATE TABLE tmp_parcelles
				(geometrie geometry,
				id double precision,
				numero character varying(50),
				voie character varying (250));
				COMMIT;'''
cur_parcelles.execute(str_query)

str_query = ""
for idx,id in enumerate(parcelles.p):
	for pe in parcelles.p[id]:
		str_query = str_query+'''INSERT INTO tmp_parcelles 
						(SELECT ST_Transform(ST_SetSRID(ST_MakePolygon(ST_GeomFromText('''+(pe.geom.get_geom_as_linestring_text())+''')),4326),2154),
						'''+id+''',\''''+pe.numero+'''\',\''''+pe.voie+'''\');'''

	if idx%100 == 0:
		cur_parcelles.execute(str_query+"COMMIT;")
		str_query = ""
if str_query != "":
	cur_parcelles.execute(str_query+"COMMIT;")

adresses = Adresses()
print('mise en cache des points adresses...')
print('nodes...')
xmladresses = ET.parse(fnadresses)
dict_node_relations = {}
for asso in xmladresses.iter('relation'):
	for t in asso.iter('tag'):
		if t.get('k') == 'name':
			for n in asso.iter('member'):
				dict_node_relations[n.get('ref')] = normalize(t.get('v'))
		dicts.add_voie('cadastre',t.get('v'))

for n in xmladresses.iter('node'):
	node_ad = nodes.load_new_node_from_xml(n)
	for t in n.iter('tag'):
		if t.get('k') == 'addr:housenumber' and n.get('id') in dict_node_relations:
			ad = Adresse(node_ad,t.get('v'),dict_node_relations[n.get('id')])
			adresses.add_adresse(ad)
			
print('chargement...')
cur_adresses = pgc.cursor()
str_query = '''DROP TABLE IF EXISTS tmp_adresses CASCADE;
				CREATE TABLE tmp_adresses
				(geometrie geometry,
				id double precision,
				numero character varying(50),
				voie character varying (250));
				COMMIT;'''
cur_adresses.execute(str_query)

str_query = ""
for idx,voie in enumerate(adresses.a):
	for num in adresses.a[voie]:
		ad = adresses.a[voie][num]
		str_query = str_query+'''INSERT INTO tmp_adresses 
						(SELECT ST_Transform('''+ad.node.get_geom_as_text()+''',
						2154),'''+str(ad.node.id)+''',\''''+num+'''\',\''''+voie+'''\');'''

	if idx%100 == 0:
		cur_adresses.execute(str_query+"COMMIT;")
		str_query = ""
if str_query != "":
	cur_adresses.execute(str_query+"COMMIT;")

highway_rep = 'cache_highways'
if not os.path.exists(highway_rep):
	os.mkdir(highway_rep)
fnhighway = highway_rep+'/highways_'+code_insee+'.osm'
if not os.path.exists(fnhighway):
	highway_url = "http://overpass-api.de/api/interpreter?data=way%0A%20%20(area%3A"+str(3600000000+dicts.osm_insee[code_insee])+")%0A%20%20%5B%22highway%22%5D%5B%22name%22%5D%3B%0Aout%20body%3B"
	print("téléchargement des ways OSM...")
	try:
		resp = urllib2.urlopen(highway_url)
		fhighway = open(fnhighway,'wb')
		fhighway.write(resp.read())
		fhighway.close()
		print("ok")
	except urllib2.HTTPError:
		print('\n******* récupération KO ********')
		print('Abandon')
		os._exit(0)
		
print('mise en cache des voies...')

dict_ways_osm = {}
xmlways = ET.parse(fnhighway)
for w in xmlways.iter('way'):
	for t in w.iter('tag'):
		if t.get('k') == 'name':
			name_osm = t.get('v')
			dicts.add_voie('OSM',name_osm)

	name_norm = normalize(name_osm)
	if name_norm not in dict_ways_osm:
		dict_ways_osm[name_norm] = {'name':name_osm,'ids':[]}
	dict_ways_osm[name_norm]['ids'].append(w.get('id'))

print('Traitements PostGIS...')
fnsql = 'adresses_buildings.sql'
fsql = open(fnsql,'rb')
str_query = fsql.read()
fsql.close()

cur_sql = pgc.cursor()
cur_sql.execute(str_query+'COMMIT;')

cur_addr_building = pgc.cursor()
str_query = '''SELECT id_building::integer,
						id_adresse::integer,
						numero,
						voie
				FROM lien_node_adresse_buildings;'''
cur_addr_building.execute(str_query)

print('Report des adresses sur les buildings...')
for c in cur_addr_building:
	adresses.a[c[3]][c[2]].add_building(str(c[0]))
	
	# for n in adresses.a[v]:
		# for b in adresses.a[v][n].buildings_id:
			# print(n+' '+v+' : '+str(b))

nb_voies_total = 0
nb_voies_fantoir = 0
nb_voies_osm = 0

print('Fichier "cles_noms_de_voies.txt" pour controle...')
fntmpkeys = 'cles_noms_de_voies.txt'
ftmpkeys = open(fntmpkeys,'w')
ftmpkeys.write('--noms de voies OSM normalisés (noms en base OSM)--\n')
for v in sorted(dict_ways_osm):
	ftmpkeys.write(v.encode('utf8')+' ('+dict_ways_osm[v]['name'].encode('utf8')+')\n')
ftmpkeys.write('---------------------\n')

nb_voies_total = 0
nb_voies_fantoir = 0
nb_voies_osm = 0

print('Fichiers associatedStreet...')
for v in adresses.a:
	fout = open(dirout+'/'+dicts.noms_voies[v]['cadastre'].replace(' ','_')+'.osm','w')
	fout.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
	fout.write("<osm version=\"0.6\" upload=\"false\" generator=\"addr_fantoir_building.py\">\n")
# nodes
	for num in adresses.a[v]:
		numadresse = adresses.a[v][num]
		if len(numadresse.buildings_id) == 0:
			fout.write(numadresse.node.get_as_osm_xml_node(False,True))
			fout.write('		<tag k="addr:housenumber" v="'+num+'"/>\n')
			fout.write("	</node>\n")
		else:
			for eb in numadresse.buildings_id:
				for ebn in buildings.b[eb].geom.a_nodes:
					fout.write(nodes.n[ebn].get_as_osm_xml_node(True,False))
# ways
	for num in adresses.a[v]:
		numadresse = adresses.a[v][num]
		if len(numadresse.buildings_id) > 0:
			for eb in numadresse.buildings_id:
				fout.write(get_as_osm_xml_way(buildings.b[eb].geom.a_nodes,buildings.b[eb].tags,eb,True,False))

# relations	
	fout.write("\t<relation id=\""+str(nodes.min_id - 1)+"\" action=\"modify\" visible=\"true\">\n")
	for num in adresses.a[v]:
		numadresse = adresses.a[v][num]
		if len(numadresse.buildings_id) == 0:
			fout.write("		<member type=\"node\" ref=\""+str(numadresse.node.id)+"\" role=\"house\"/>\n")
		else:
			for eb in numadresse.buildings_id:
				fout.write("		<member type=\"way\" ref=\""+str(eb)+"\" role=\"house\"/>\n")
				
	street_name = dicts.noms_voies[v]['cadastre'].title()
	if 'OSM' in dicts.noms_voies[v]:
		street_name =  dicts.noms_voies[v]['OSM'].encode('utf8')
		for m in dict_ways_osm[v]['ids']:
			fout.write("		<member type=\"way\" ref=\""+m+"\" role=\"street\"/>\n")
		nb_voies_osm += 1
	else:
		ftmpkeys.write('Pas OSM     : '+dicts.noms_voies[v]['cadastre']+'\n')
	fout.write("		<tag k=\"type\" v=\"associatedStreet\"/>\n")
	fout.write("		<tag k=\"name\" v=\""+street_name+"\"/>\n")
	if v in dicts.fantoir:
		fout.write("		<tag k=\"ref:FR:FANTOIR\" v=\""+dicts.fantoir[v]+"\"/>\n")
		nb_voies_fantoir += 1
	else:
		ftmpkeys.write('Pas FANTOIR : '+dicts.noms_voies[v]['cadastre']+'\n')
	fout.write("	</relation>\n")
	nb_voies_total +=1
	fout.write("</osm>")
	fout.close()

ftmpkeys.close()

print("Nombre de relations creees  : "+str(nb_voies_total))
print("     avec code FANTOIR      : "+str(nb_voies_fantoir)+" ("+str(int(nb_voies_fantoir*100/nb_voies_total))+"%)")
print("     avec rapprochement OSM : "+str(nb_voies_osm)+" ("+str(int(nb_voies_osm*100/nb_voies_total))+"%)")

# mode 1 : addr:housenumber comme tag du building
#			sinon point adresse seul à la place fournie en entree
# mode 2 : addr:housenumber comme point à mi-longueur du plus proche coté du point initial
#			sinon point adresse seul à la place fournie en entree