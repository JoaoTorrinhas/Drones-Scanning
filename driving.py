from datetime import datetime
import json
from geographiclib.geodesic import Geodesic
import time
from obu_db import *
from zone_db import check_zones_not_occupied as obu1_check_zones_not_occupied, return_zone_associated_to_OBU as obu1_return_zone_associated_to_OBU
from zones_obu2_db import check_zones_not_occupied as obu2_check_zones_not_occupied, return_zone_associated_to_OBU as obu2_return_zone_associated_to_OBU
from zones_obu3_db import check_zones_not_occupied as obu3_check_zones_not_occupied, return_zone_associated_to_OBU as obu3_return_zone_associated_to_OBU
from script_obu1 import listen_cams as obu1_listen_cams, update_zones_db_with_actualCoordinatesOfOBU1, check_if_zone_occupied as obu1_check_if_zone_occupied, listen_denms as obu1_listen_denms
from script_obu2 import listen_cams as obu2_listen_cams, update_zones_db_with_actualCoordinatesOfOBU2, check_if_zone_occupied as obu2_check_if_zone_occupied, listen_denms as obu2_listen_denms
from script_obu3 import listen_cams as obu3_listen_cams, update_zones_db_with_actualCoordinatesOfOBU3, check_if_zone_occupied as obu3_check_if_zone_occupied, listen_denms as obu3_listen_denms


def iterate_drone_to_zone(start_lat, start_lon, data, obu, id, zone, ip, initial_lat, initial_lon):
    reached_zone = False
    occupied = False

    # Calculate the initial bearing and distance between the two coordinates
    geod = Geodesic.WGS84
    result = geod.Inverse(start_lat, start_lon, zone[0], zone[1])
    total_distance = result['s12']
    bearing = result['azi1']

    #print('Initial distance: {:.2f} meters for OBU with ID: {}'.format(total_distance, id))
    #print('Initial bearing: {:.2f} degrees for OBU with ID: {}'.format(bearing, id))

    # Navigate towards the end coordinate
    current_coordinates = [start_lat, start_lon]
    distance_increment = 4  # Incremental distance to move in each iteration
    
    while total_distance > 0:
        # Move the drone by the distance increment towards the destination
        move_distance = min(distance_increment, total_distance)  # Limit move distance to remaining distance
        result = geod.Direct(current_coordinates[0], current_coordinates[1], bearing, move_distance)
        new_coordinates = [result['lat2'], result['lon2']]

        print("OBU with ID {} is going to coordinate: {}".format(id, new_coordinates))
        update_obu_db(new_coordinates[0], new_coordinates[1], ip)
        time.sleep(1)
        data['longitude'] = new_coordinates[1]
        data['latitude'] = new_coordinates[0]
        data['timestamp'] = datetime.timestamp(datetime.now())
        (rc, mid) = obu.publish("vanetza/in/cam", json.dumps(data))
        if rc == 0:
            print("Message published successfully with message ID", mid)
        else:
            print("Error publishing message with return code", rc)
            
        #obu.subscribe("vanetza/out/cam")    #Obu enquanto segue para o destino, fica atenta a mensagens publicadas

        # Calculate the new distance and bearing between the current and end coordinates
        result = geod.Inverse(new_coordinates[0], new_coordinates[1], zone[0], zone[1])
        total_distance = result['s12']
        bearing = result['azi1']

        #print('Current distance: {:.2f} meters for OBU with ID: {}'.format(total_distance, id))
        #print('Current bearing: {:.2f} degrees for OBU with ID: {}'.format(bearing, id))

        # Update the current coordinates
        current_coordinates = new_coordinates
        
        #obu.subscribe("vanetza/out/cam")    #Obu enquanto segue para o destino, fica atenta a mensagens publicadas
        if ip == "192.168.98.20":
            update_zones_db_with_actualCoordinatesOfOBU1(current_coordinates[0],current_coordinates[1], ip, "obu1") #Atualizar na BD se a OBU atual estiver perto de uma zona
            obu1_listen_cams(obu) #Ouvir as mensagens publicadas pelas outra OBUS
            obu1_listen_denms(obu)
            # TODO: Verifica se a OBU está perto de alguma zona já ocupada por outra OBU
            occupied = obu1_check_if_zone_occupied(ip, zone, initial_lat, initial_lon)
            
        elif ip == "192.168.98.30":
            update_zones_db_with_actualCoordinatesOfOBU2(current_coordinates[0],current_coordinates[1], ip, "obu2") #Atualizar na BD se a OBU atual estiver perto de uma zona
            obu2_listen_cams(obu) #Ouvir as mensagens publicadas pelas outra OBUS
            obu2_listen_denms(obu)
            # TODO: Verifica se a OBU está perto de alguma zona já ocupada por outra OBU
            occupied = obu2_check_if_zone_occupied(ip, zone, initial_lat, initial_lon)
            
        elif ip == "192.168.98.40":
            update_zones_db_with_actualCoordinatesOfOBU3(current_coordinates[0],current_coordinates[1], ip, "obu3") #Atualizar na BD se a OBU atual estiver perto de uma zona
            obu3_listen_cams(obu) #Ouvir as mensagens publicadas pelas outra OBUS
            obu3_listen_denms(obu)
            # TODO: Verifica se a OBU está perto de alguma zona já ocupada por outra OBU
            occupied = obu3_check_if_zone_occupied(ip, zone, initial_lat, initial_lon)
                    
        if occupied == True:
            break    
            
        # clear = False
        # if ip == "192.168.98.20":   #OBU1
        #     zones_clear = obu1_check_zones_not_occupied() # json object with the zones that are not occupied
        #     zones_clear = json.loads(zones_clear)
        #     #clear = False
        #     #print('ZONES NOT OCCUPIED!!!!!!!: {} | OBU WITH IP {}'.format(zones_clear, ip))
        #     for info_zone_clear in zones_clear:
        #         zone_clear = [info_zone_clear["latitudeZone"], info_zone_clear["longitudeZone"]]
        #         #print('ZONE {} == ZONE CLEAR {} FOR OBU1'.format(zone, zone_clear))
        #         if zone == zone_clear:
        #             clear = True
        #             break
                    
        # elif ip == "192.168.98.30": #OBU2
        #     zones_clear = obu2_check_zones_not_occupied()
        #     zones_clear = json.loads(zones_clear)
        #     print('ZONES NOT OCCUPIED!!!!!!!: {} | OBU WITH IP {}'.format(zones_clear, ip))
        #     for info_zone_clear in zones_clear:
        #         zone_clear = [info_zone_clear["latitudeZone"], info_zone_clear["longitudeZone"]]
        #         #print('ZONE {} == ZONE CLEAR {} FOR OBU2'.format(zone, zone_clear))
        #         if zone == zone_clear:
        #             clear = True
        #             break  
                
        # elif ip == "192.168.98.40": #OBU3
        #     zones_clear = obu3_check_zones_not_occupied()
        #     zones_clear = json.loads(zones_clear)
        #     #print('ZONES NOT OCCUPIED!!!!!!!: {} | OBU WITH IP {}'.format(zones_clear, ip))
        #     for info_zone_clear in zones_clear:
        #         zone_clear = [info_zone_clear["latitudeZone"], info_zone_clear["longitudeZone"]]
        #         #print('ZONE {} == ZONE CLEAR {} FOR OBU3'.format(zone, zone_clear))
        #         if zone == zone_clear:
        #             clear = True
        #             break  
        
        # zones_clear = check_zones_not_occupied()    #Return a json object with the zones that are not occupied
        # zones_clear = json.loads(zones_clear)
        
        # clear = False
        # print('ZONES NOT OCCUPIED!!!!!!!: {} | OBU WITH IP {}'.format(zones_clear, ip))
        # for info_zone_clear in zones_clear:
        #     zone_clear = [info_zone_clear["latitudeZone"], info_zone_clear["longitudeZone"]]
        #     if zone == zone_clear:
        #         clear = True
        #         break
        
        #Se a zona não for as coordenadas iniciais de uma das OBUs, retornamos a zona associada à OBU atual
        # if zone != [initial_lat, initial_lon]:  
        #     associated_zone_to_this_obu = {}
            
        #     if ip == "192.168.98.20":   #OBU1
        #         associated_zone_to_this_obu = obu1_return_zone_associated_to_OBU(zone) 
        #         associated_zone_to_this_obu = json.loads(associated_zone_to_this_obu)   
        #     elif ip == "192.168.98.30": #OBU2
        #         associated_zone_to_this_obu = obu2_return_zone_associated_to_OBU(zone) 
        #         associated_zone_to_this_obu = json.loads(associated_zone_to_this_obu)  
        #     elif ip == "192.168.98.40": #OBU3
        #         associated_zone_to_this_obu = obu3_return_zone_associated_to_OBU(zone) 
        #         associated_zone_to_this_obu = json.loads(associated_zone_to_this_obu)  
            
        #     #associated_zone_to_this_obu = return_zone_associated_to_OBU(zone) 
        #     #associated_zone_to_this_obu = json.loads(associated_zone_to_this_obu)
        
        #     #print("OBU {} IS ASSOCIATED TO ZONE(INFO): {}".format(ip, associated_zone_to_this_obu))
        #     #print("CLEAR: {} FOR OBU {}".format(clear,ip))
            
        #     #Se a zona estiver ocupada e a OBU atual não está associada a essa zona, então occupied = True
        #     #print('IP ADDRESS OF ACTUAL OBU: {}'.format(ip))
        #     #print('IP ADDRESS OF OBU ASSOCIATED TO THIS ZONE: {}'.format(associated_zone_to_this_obu["ip"]))
        #     if clear == False and associated_zone_to_this_obu["ip"] != ip:
        #         occupied = True
        #         break
        
    if occupied != True:
        reached_zone = True
            
    print('OBU with ID {} reached the end coordinate: {}'.format(id, current_coordinates))

    return reached_zone, current_coordinates[0], current_coordinates[1]
    

   
#Ponto de partida
#Latitude: 40.63145592814154, Longitude: -8.661712310994494
