import esp
import time
import machine
import dht
import socket
import network

pauza = 300
skalirana_vrednost = 15

def http_get(url):
    _, _, host, path = url.split('/', 3)
    addr = socket.getaddrinfo(host, 80)[0][-1]
    s = socket.socket()
    s.connect(addr)
    s.send(bytes('GET /%s HTTP/1.0\r\nHost: %s\r\n\r\n' % (path, host), 'utf8'))
    while True:
        data = s.recv(1000)
        if data:
            print('\nPrimljeno = ',len(data))
            print(url)
            print(str(data, 'utf8'), end='')
            # Zasto ovde radi return ?
            return data.decode('utf-8')
        else:
            break
    s.close()

def proveriwifi():
    ponavljanja=0
    while (  sta_if.isconnected() is  False ):
        time.sleep(2)
        sta_if.connect('I9EBE','dTG7kKkAUJd4')
        if (sta_if.isconnected()):
            print('I9EBE - Povezan')
            break
        time.sleep(2)
        sta_if.connect('Dimic','aleksandarivan')
        if (sta_if.isconnected()):
            print('Dimic - Povezan')
            break
        time.sleep(2)
        sta_if.connect('CETASmarac','ceta12345')
        if (sta_if.isconnected()):
            print('CETASmarac - Povezan')
            break

        ponavljanja=ponavljanja+1
        print(ponavljanja,'ponavaljanja  povezivanja na WiFi')

        if (ponavljanja==10):
            print(' RESETOVATI ESP8266 ')
            machine.reset()
            break
    print ('\nUspesno povezan na neku mrezu = ',sta_if.ifconfig())



# Da bih video pocetak programa
time.sleep(5)

# Definisanje modula
esp.osdebug(None)
pin = machine.Pin(0, machine.Pin.OUT)
d = dht.DHT11(machine.Pin(4))
adc = machine.ADC(0)

# Zabrana AP
ap_if = network.WLAN(network.AP_IF)
ap_if.active(False)
print ('\nAccess Point = ' , ap_if.active())

# Prilikom reseta ugasi grejanje_dugme
pin.off()

# Dozvola stanice
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
print ('Stanica = ', sta_if.active() )

# Povezivanje na ruter
    # print ('Povezani smo = ', sta_if.isconnected() )
    # if (  sta_if.isconnected() is not True ):
    #     sta_if.connect('I9EBE','dTG7kKkAUJd4')
    # print( '\nI9EBE', sta_if.ifconfig() )

proveriwifi()

while (True):
    #time.sleep(pauza)
# Pocetak akvizicije - 15364b6f7e934f859ab8cc3803d2971b
    print('\nStart.')
    d.measure()
    temperatura=d.temperature()
    vlaznost=d.humidity()
    print ('     Temperatura', temperatura)
    print ('     Vlaznost',vlaznost)
    print ('Kraj Merenja\n')
    try:
#BLINK
    # Vlaznost
        vlaznost_link = 'http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V1?value='+str(vlaznost)
        http_get(vlaznost_link)
    # Temperatura
        temperatura_link = 'http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V0?value='+str(temperatura)
        http_get(temperatura_link)
    # Grejanje Taster
        grejanje_link= 'http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/get/V2'
        web_prekidac = http_get(grejanje_link)
        #print('\n\nRESPONSE web_prekidac je', type(web_prekidac), 'duzine ', len(web_prekidac))
        print('\n\nBlyink prekidac je : ',web_prekidac[-3])
        if (int(web_prekidac[-3])==1):
            pin.on()
        else:
            pin.off()
    # Grejanje skalirani prikaz
        skalar = int(web_prekidac[-3])*skalirana_vrednost
        skaliran_link = 'http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V3?value='+str(skalar)
        http_get(skaliran_link)
#ThingSpeak
        #http_get( 'https://api.thingspeak.com/update?api_key=J1T84N77WN3S33B8&field1='+str(vlaznost) )
        http_get( 'https://api.thingspeak.com/update?api_key=J1T84N77WN3S33B8&field2='+str(temperatura) )
        #Shttp_get( 'https://api.thingspeak.com/update?api_key=J1T84N77WN3S33B8&field3='+str(web_prekidac[-3]) )



   # Hendlovati status tastera
    except:
        machine.reset()
        proveriwifi()
    print ('\nCekam ',pauza,'sekundi\n')
    time.sleep(pauza)

    # DODATI DECIMALNU VREDNOST ZA DHT11
    #https://forum.micropython.org/viewtopic.php?t=1392
