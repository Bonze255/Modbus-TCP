#!/usr/bin/env python3
####################################################################################################
#PLC MODBUS TCP
#This Plugin use MODBUS TCP for PLC Kommunication 
#it is based on the "pymodbus" lib  for Python 
#
#by  Manuel Holländer
####################################################################################################  



import socket
import time
import re
import struct
import string
import logging
import threading

from pprint import pprint
from array import array
from datetime import datetime, timedelta

from pymodbus.client.sync import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder
from . import dpts

class ModbusException(Exception):
    pass

logger = logging.getLogger('')

class modbus():
####################################################################################################
#
#
#
#
#
####################################################################################################  
    def __init__(self, smarthome, device='', timeout=None, port=502, cycle=5, pe_adress = 0, pe_length= 0, pa_adress= 0, pa_length= 0):
        ##Initialdaten aus Plugin.conf
        self._sh = smarthome
        self._items = {}
        self.timeout = float(timeout)
        self.device = str(device)
        self.port = int(port)
        self.cycle = int(cycle)
        #Inputs
        self.pe_adress = int(pe_adress)
        self.pe_lenght = int(pe_length)
        #Outputs
        self.pa_adress = int(pa_adress)
        self.pa_lenght = int(pa_length)
        ######################################
        self._db = {}##ausgangsbytes
        self._db['in'] = {}
        self._db['out'] = {}
        #1: 	bool						0...1
        #5: 	8-bit signed value			0...255
        #5.001: 8-bit unsigned value		0...100
        #6: 	8-bit signed value			-128...127
        #7: 	16-bit unsigned value		0...65535
        #8: 	16-bit signed value			-32768...32767
        #9: 	floating point 				-671088,64 - 670760,96
        self._db['dpt'] = {1:1, 5:8, 5.001:8, 6:8, 7:16, 8:16}##dpt und länge in bits
        self.init_read = 0
        self._lock = threading.Lock()
        self.connected = False
        logger.info('Initialising Modbus TCP PLUGIN###############################################')
        smarthome.connections.monitor(self)
        
        
    def run(self):##plugin starten
        self.alive = True
        self._sh.scheduler.add('Modbus', self.refresh, cycle=self.cycle)
        logger.info('MODBUS: Started!')

    def stop(self):##plugin stoppen
        self.alive = False
        self._socket.close()
        logger.info('MODBUS: Stopped!')

    def parse_logic(self, logic):##nicht benoetigt
        pass

    def connect(self): #Verbinden/socket oeffnen
        self._lock.acquire()
        target = None
        try:
            if self.device is not None:
                self._modbuspy = ModbusTcpClient(self.device, self.port)
                self._modbuspy.connect()
        except Exception as e:
            logger.error('MODBUS: Could not connect to {}: {}'.format(self.device, e))
            self._lock.release()
            return
        else:
            
            logger.info('MODBUS: Connected to {}'.format(self.device))
            self.connected = True
            
            self._lock.release()

    def disconnect(self): #Verbindung trennen/socket schließen
        if self.connected:
            try:
                if self_socket is not None:
                   client.close()
            except:
                pass
            
            logger.info('MODBUS: Disconnected!')
            self.connected = False
            self._target = None
####################################################################################################
#HAUPTFUNKTION(main)
#Funktion wird zyklisch von Smarthome aufgerufen:
#
#
#
####################################################################################################    
    def refresh(self):
        logger.debug('MODBUS cycle started########################################################')
        if self.connected:
            if self.init_read == 0:                                                                       #beim 1 start auch die Ausgangsregister lesen das STeuerung und Smarthome auf gleichem Stand sind !
                #self.diag()
                self.read('out')
                self.init_read = 1
            
            start = time.time()
            werte = self.read()
            self.write()
            cycletime = time.time() - start
            logger.debug("Modbus cycle takes {0} seconds".format(cycletime))
        else:
            self.connect()#neu
            pass
####################################################################################################
#Items beim start überprüfen, auf modbus_on = 1
#Items Namen (gads) und Bytes werden peb und pab zugeordnet
#Bits werden in Bytes einsortiert
#Momentan sind nur boolische und byte Items möglich
#
####################################################################################################
    def parse_item(self, item):
        
        if 'modbus_on' in item.conf:
            byte = int(item.conf['modbus_byte'])
            ##daten prüfen
            if 'modbus_bit' in item.conf:
                bit = int(item.conf['modbus_bit'])
            else:
               bit = None  
            ##Daten zusammenstellen
            daten = []
            daten.append(bit)#0
            
            if 'modbus_dpt' in item.conf:
                #length = 8#dpt_dict[item.conf['modbus_dpt']]
                daten.append(item.conf['modbus_dpt'])#1
                daten.append(item())#2
            else:
                daten.append(1)#1
                daten.append(bool(item()))#2
                
            daten.append(item)#3
            
            pprint(daten)
            ##Unterscheidung in in/outputs
            if self.pe_adress <= byte <= (self.pe_adress+self.pe_lenght):                           ##INPUTS
                if not byte in self._db['in'].keys():
                    self._db['in'][byte] = []
                self._db['in'][byte].append(daten)
            elif self.pa_adress <= byte <= (self.pa_adress+self.pa_lenght):                         ##OUTPUTS
                if byte not in self._db['out'].keys():
                    self._db['out'][byte] = []
                self._db['out'][byte].append(daten)
        return None
####################################################################################################        
##Item hat sich verändert, wird von Smarthome aufgerufen, bei item(name, caller...)
##self._DB updaten!
#
#
#
####################################################################################################  
    def update_item(self, item, caller=None, source=None, dest=None):
        if caller == 'modbus':
            logger.info("Modbus: ITEM DB UPDATEN  sich was geändert hat")
            # if 'modbus_on' in item.conf:
                # byte = int(item.conf['modbus_byte'])
            # ##daten prüfen
            # if 'modbus_bit' in item.conf:
                # bit = int(item.conf['modbus_bit'])
            # value = item()
            
            # if self.pe_adress <= byte <= (self.pe_adress+self.pe_lenght):                           ##INPUTS
                # if bit in sorted(self._db['in'][byte]):  
                    # self._db['in'][byte][bit][2] = value
            # elif self.pa_adress <= byte <= (self.pa_adress+self.pa_lenght):                         ##OUTPUTS
                # if bit in sorted(self._db['out'][byte]):  
                    # self._db['out'][byte][bit][2] = value
        # else:
            # pass
####################################################################################################
#AusgangsWORTe an Steuerung schreiben
#Nur Daten an Steuerung senden
#
#
#
####################################################################################################  
    def write(self):
        #print("BYTES SENDEN#####################################")        
        try: 
            lb = 00000000
            hb = 00000000
    #### byte besteht immer aus 16 bits
            for byte in self._db['out']:
                for bit in sorted(self._db['out'][byte]):  
                    if bit in self._db['out'][byte]:
                        bitpos =    bit[0]                                                          #startbit/bitposition des binärwertes
                        type =      bit[1]
                        value =     bit[2]
                        name =      bit[3]
                        bit[2] =    bit[3]()                                                           ##aktueller wert des items abrufen und value updaten!
                        builder = BinaryPayloadBuilder(endian=Endian.Little)

                        ##unterscheidung dateityp
                        if type == '5' or type == '5.001' or type == '6' :                                          ##8bit uint / int
                            length = 8
                            if bitpos < 8:  #lb
                                lb = value
                            else:           #hb
                                hb = value
                            if type == '5':
                                builder.add_8bit_uint(lb)
                                builder.add_8bit_uint(hb)
                                #logger.debug('MODBUS: 8bit uint {0} ; {1}'.format(lb,hb)) 
                            elif type == '6':
                                builder.add_8bit_int(lb)
                                builder.add_8bit_int(hb)
                                #logger.debug('MODBUS: 8bit int {0} ; {1}'.format(lb.hb)) 
                        elif type == '7' or type == '8':                                            #16bit uint / int
                            length = 16
                            if type == '7':                                                         #0...65535
                                builder.add_16bit_uint(value)
                                #logger.debug('MODBUS: 16bit uint {0} '.format(value)) 
                            else:                                                                   #-32768...32767
                                builder.add_16bit_int(value)   
                                #logger.debug('MODBUS: 16bit int {0}'.format(value)) 
                            
                        elif type == '1':
                            length = 1
                                                                                      #nur pro byte einmal die bits wandeln
                            if bitpos < 8:  #lb
                                lb  = lb | int(value) << bitpos
                                #logger.debug('MODBUS: 8bit int{0}'.format(lb)) 
                                
                            else:           #hb
                                hb  = hb | int(value) << bitpos
                                #logger.debug('MODBUS: 8bit int{0}'.format(hb)) 
                                
                            builder.add_8bit_uint(lb)
                            builder.add_8bit_uint(hb)
                            
                payload = builder.build()
                    #pprint(payload)
                logger.debug('MODBUS: write to PLC: WORD {0} set to {1} '.format(byte,payload)) 
                self._modbuspy.write_registers(byte, payload, skip_encode=True)
                builder.reset()        
        except Exception as e:
            logger.error('MODBUS: Could not write an OutWord, because {}'.format(e))
            self._lock.release()
            return None
####################################################################################################
#Liest komplett angegebenen Speicherbereich aus Steuerung aus und gibt sie in dict zurück!
#read = anfangswert, end= länge 
#Eingangsbereich von Steuerung lesen
#
#
####################################################################################################  
    def read(self, iO='in'):
        #print('DATEN VOM BUS LESEN')
        i = 0
        if iO !='in':
            x = 'out'
        else:
            x = 'in'
        try:
            for byte in self._db[x]:
                rr = self._modbuspy.read_holding_registers(byte,2)
                decodert2 = BinaryPayloadDecoder.fromRegisters(rr.registers, endian=Endian.Little)
                ##prüfen welcher dpt typ vorliegt und  dann das registerabfrage ergebnis aufdröseln:
                #->decode_16bit_uint()  -> 7 / 8
                #->decode_8bit_uint()   -> 5 | 5.001
                #->decode_8bit_int()    -> 6
                #->decode_bits()        -> 1
                for bit in self._db[x][byte]:                                                    ##eintraege in dict durchgehen
                    bitpos = bit[0]
                    type =  bit[1]
                    name =  bit[3]
                    
                    if type == '5' or type == '5.001' or type == '6':                                              ##8bit uint / int
                        length = 8
                        
                        if type == '6':
                            lb = decodert2.decode_8bit_int()
                            hb = decodert2.decode_8bit_int()
                            
                        elif type == '5' or type == '5.001':
                            lb = decodert2.decode_8bit_uint()
                            hb = decodert2.decode_8bit_uint()
                            
                        if bitpos < 8:#lb
                            value = hb
                            #logger.debug('MODBUS: 8bit int{0}'.format(value)) 
                        else:#hb
                            value = lb
                            #logger.debug('MODBUS: 8bit int{0}'.format(value)) 
                        
                        if type == '5.001':
                            #print('lb/hb Daten', value)
                            value = self.normiere(0,100, int(value))
                            #print (dpts.en5001(value))
                    elif type == '7' or type == '8':                                                #16bit uint / int
                        length = 16
                        if type == '7':                                                             #0...65535
                            value = decodert2.decode_16bit_uint()
                            #logger.debug('MODBUS: 16bit uint{0}'.format(value)) 
                        else:                                                                       #-32768...32767
                            value  = decodert2.decode_16bit_int()    
                            #logger.debug('MODBUS: 16bit int{0}'.format(value)) 
                        
                    elif type == '1':
                        length = 1
                        hb = decodert2.decode_bits()
                        lb = decodert2.decode_bits()
                        bits = lb+hb
                     
                        value = bits[bitpos]
                        #logger.debug('MODBUS: Bits{0}'.format(bits))   
                        
                    bit[2] = value                                                                  #zurückspeichern   
                    
                    decodert2.reset() 
            ##Debug#################################################################################
                    bit[3](value, caller='modbus')
                i = i+1
                lb = decodert2.decode_bits()
                hb = decodert2.decode_bits()
                bits = hb+lb
                decodert2.reset() 
                logger.debug('MODBUS: read from   PLC {0}-{1} {2}'.format(byte, bits, bytes))

        except Exception as e:
            logger.error('MODBUS: Could not read an InputWord, because {}'.format( e))
            self._lock.release()
            return None
        i = 0
        return None        
####################################################################################################
#wandelt str in binary ohne führendes 0b
#und invertiert auf wunsch das Ergebnis!
#
#
#
####################################################################################################  
    def diag(self):
        self.status()
        self.cnt_io()
        self.k_bus()
        self.diag_all()
        
    def cnt_io(self):
        rr = self._modbuspy.read_holding_registers(4114,2)# anzahl klemmen
        pprint(rr)
        decodert2 = BinaryPayloadDecoder.fromRegisters(rr.registers, endian=Endian.Little)
        x = decodert2.decode_16bit_uint()
        decodert2.reset()
        print('Anzahl IO`s' , x)
        return x
        
    def k_bus(self):#0x6102
    
        rr = self._modbuspy.read_holding_registers(24834,2)# K bus Fehler?
        decodert2 = BinaryPayloadDecoder.fromRegisters(rr.registers, endian=Endian.Little)
        x = decodert2.decode_8bit_uint()
        y = decodert2.decode_8bit_uint()
        decodert2.reset()
        
        if x == 1:#6105
            rr = self._modbuspy.read_holding_registers(24837,2)#Welcher Fehler?
            pprint(rr)
            decodert2 = BinaryPayloadDecoder.fromRegisters(rr.registers, endian=Endian.Little)
            x = decodert2.decode_16bit_uint()
            decodert2.reset()
            if x == "1": 
                print('KL_COMMAND_ERROR')
            elif x == "2":
                print('KL_INP_DATA_ERROR')
            elif x == "4": 
                print('KL_COMMAND_ERROR')
            elif x == "8":
                print('KL_TIMEOUT_ERROR')
            elif x == "6": 
                print('KL_HDR_ERROR ')
            elif x == "16":
                print('KL_RESET_ERROR')
        return None 
        
    def status(self):#0x100C 
        rr = self._modbuspy.read_holding_registers(4108,2)#Buskoppler status
        decodert2 = BinaryPayloadDecoder.fromRegisters(rr.registers, endian=Endian.Little)
        x = decodert2.decode_16bit_uint()
        decodert2.reset()
        print('Buskoppler Status ' , x )
        return None
    def diag_all(self):#0x100B
        rr = self._modbuspy.read_holding_registers(4107,2)#Buskoppler status
        decodert2 = BinaryPayloadDecoder.fromRegisters(rr.registers, endian=Endian.Little)
        x = decodert2.decode_16bit_uint()
        decodert2.reset()
        print('Buskoppdiag' , x )
        return None   
    def toBinary2(self, n, invert = 1):##
        byte = '{:08b}'.format(n)
         
        i = int(16)-len(byte)
        ausgabe = ""
        for x in range(0,i):
            ausgabe = "0"+ausgabe
        ausgabe = ausgabe+byte
        if invert == 1:#invertieren
            ausgabe = ausgabe[::-1]
        return ausgabe
        
    def toBinary(self, n, invert = 0):##
        byte = '{:08b}'.format(n)
        if invert == 1:#invertieren
            byte = byte[::-1] 
        ausgabe = []
        if byte == '00000000':
            ausgabe.append('00000000')
            ausgabe.append('00000000')
        elif byte < '256' :
            ausgabe.append(byte[0:8])
            ausgabe.append('00000000')
        else:
            ausgabe.append(byte[0:8])
            ausgabe.append(byte[8:17])   
        return ausgabe 
        
        
    def normiere(self, min, max, val):
       #if invert == 0:
        xy = (100.0 * ((val - min) / (max - min)))
        return xy
   
