import esp
import time
import dht
import socket
import network
import ure
import onewire, ds18x20

'''
Izmerene vrednosti sa senzora
    V0 - Temperatura
    V1 - Vlaznost
    V4 - Temperatura vode u kotlu
Prekici za paljenje/gasenje senzora
    V2 - Prekidac PALI Grejanje
    V3 - Prekidac BLOKIRAJ Grejanje
Eksterni API
    V9 - Thingspeak prikaz
LCD za prikaz vremena
    V10- LCD prvi red
    V11 - LCD drugi red
Skalirane vrednosti za prikaz
    V12 - Prikaz prekidaca BLOKIRAJ Grejanje
    V13 - Prikaz prekidaca PALI Grejanje
'''

# Dodati jedan NEZAVISTAN izlaz za relej
# Dodati jedan buzzer prilikom zbog reseta, staviti ga na pwm pin
# DEKODOVATI RTC
# PODESITI ONLINE STATUS
# Dodati broj reseta u fajlu mozda i ne mora

reset=0 # Da znam koliko se puta resetovao uredjaj
pauza = 60

def http_get(url):
    _, _, host, path = url.split('/', 3)
    addr = socket.getaddrinfo(host, 80)[0][-1]
    s = socket.socket()
    s.connect(addr)
    s.send(bytes('GET /%s HTTP/1.0\r\nHost: %s\r\n\r\n' % (path, host), 'utf8'))
    while True:
        data = s.recv(1000)
        if data:
            #print('\nPrimljeno = ',len(data))
            #print(url)
            #print(str(data, 'utf8'), end='')
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

        if (ponavljanja==6):
            print(' RESETOVATI ESP8266 ')
            machine.reset()
            break
    print ('\nUspesno povezan na neku mrezu = ',sta_if.ifconfig())

def do_connect():
    import network
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect('I9EBE', 'dTG7kKkAUJd4')
        while not sta_if.isconnected():
            pass
    print('network config:', sta_if.ifconfig())


# Definisanje modula
esp.osdebug(None)
#taster_pali = machine.Pin(2, machine.Pin.OUT)
#taster_odblokiraj = machine.Pin(15, machine.Pin.OUT)
d = dht.DHT11(machine.Pin(4))
adc = machine.ADC(0)

# DS18x20 inicijalizacija
dat = machine.Pin(13)
ds = ds18x20.DS18X20(onewire.OneWire(dat))
roms = ds.scan()

# Zabrana AP
ap_if = network.WLAN(network.AP_IF)
ap_if.active(False)
print ('\nAccess Point = ' , ap_if.active())
# Dozvola stanice
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
print ('Stanica = ', sta_if.active() )

print('\nDostupne mreze\n')
print(sta_if.scan())

#proveriwifi()
do_connect()


while (True):
    # Merenje Senzora - 15364b6f7e934f859ab8cc3803d2971b
    print('\nPocetak Merenja')
    d.measure()
    temperatura=d.temperature()
    vlaznost=d.humidity()
    print ('     Temperatura', temperatura)
    print ('     Vlaznost   ',vlaznost)
    ds.convert_temp()
    time.sleep(1)
    for rom in roms:
        kotao_temperatura= ds.read_temp(rom)
        print( '   Temp. vode   ', kotao_temperatura)
    print ('Kraj Merenja\n')

    try:

# BLINK
    # Vlaznost prostorije - Update v1
        http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V1?value='+str(vlaznost))
    # Temperatura prostorije - Update v0
        http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V0?value='+str(temperatura))
    # Temperatura vode u kotlu - v4
        http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V4?value='+str(int(kotao_temperatura)))
    # Grejanje Taster PALI - Dowload/Update v2,v13
        web_prekidac_pali = http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/get/V2')
        prekidac_pali = ure.search('\[.\d.+\]', web_prekidac_pali).group(0)[2]
        print( '\nUpali Grejanje je    : ', prekidac_pali)
        http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V13?value='+str(prekidac_pali))
        if (int(prekidac_pali)>0):
            taster_pali.on()
        else:
            taster_pali.off()
    # Grejanje Taster BLOKIRAJ Dowload/Update v3,v12
        web_prekidac_block = http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/get/V3')
        prekidac_gasi = ure.search('\[.\d.+\]', web_prekidac_block).group(0)[2]
        print( '\nBlokiraj Grejanje je : ', prekidac_gasi)
        http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V12?value='+str(prekidac_gasi))
        if (int(prekidac_gasi)>0): # OVo je malo nezgodno napisano...
            taster_odblokiraj.on()
        else:
            taster_odblokiraj.off()
    # Preuzmi RTC format podataka Update v10,v11 http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/rtc
        rtc_format = http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/rtc')
        RTC_raw = ure.search('\[(\d+)]', rtc_format).group(1)
        print ('\nRTC je      : ', RTC_raw )
        # Ispisi Vreme - Datum poslednje konekcije 1-red v10 2-red v11
        http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V10?value=TimeAndDate')
        http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V11?value='+str(RTC_raw))
# ThingSpeak
        http_get( 'https://api.thingspeak.com/update?api_key=J1T84N77WN3S33B8&field1=' + str(temperatura) + '&field2=' + str(kotao_temperatura) )
# Ako je UPDATE prosao pocni da brojis ponovo neuspela povezivanja.
        reset=0
    except:
        #
        reset = reset + 1
        print ('\nP------------------------')
        print ('\nPUKAO SAM : ',reset,'puta\n')
        print ('\nP------------------------')
        if (reset >=3):
            machine.reset()
    print ('\nCekam ',pauza,'sekundi\n')
    time.sleep(pauza)
