import esp
import time
import machine
import dht
import socket
import network
import ure

'''
Izmerene vrednosti sa senzora
    V0 - Temperatura
    V1 - Vlaznost
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

pauza = 30
skalar = 15

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
taster_pali = machine.Pin(0, machine.Pin.OUT)
taster_odblokiraj = machine.Pin(12, machine.Pin.OUT)
d = dht.DHT11(machine.Pin(4))
adc = machine.ADC(0)

# Zabrana AP
ap_if = network.WLAN(network.AP_IF)
ap_if.active(False)
print ('\nAccess Point = ' , ap_if.active())

# Prilikom reseta ugasi grejanje_dugme
taster_pali.off()
taster_odblokiraj.on()

# Dozvola stanice
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
print ('Stanica = ', sta_if.active() )

print('\nDostupne mreze\n')
print(sta_if.scan())



#proveriwifi()
do_connect()


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
    # Grejanje Taster PALI
        grejanje_link_pali= 'http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/get/V2'
        web_prekidac_pali = http_get(grejanje_link_pali)
        prekidac_pali = ure.search('\[.\d.\]', web_prekidac_pali).group(0)[2]
        print( '\nUpali Grejanje je    : ', prekidac_pali)

        if (int(prekidac_pali)==1): # Ovo je malo nezgodno napisano...
            taster_pali.on()
            http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V13?value='+str(prekidac_pali))
        else:
            taster_pali.off()
            http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V13?value='+str(prekidac_pali))

    # Grejanje Taster BLOKIRAJ
        grejanje_link_gasi = 'http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/get/V3'
        web_prekidac_gasi = http_get(grejanje_link_gasi)
        prekidac_gasi = ure.search('\[.\d.\]', web_prekidac_gasi).group(0)[2]
        print( '\nBlokiraj Grejanje je : ', prekidac_gasi)
# Ako je blokiran kotao mora biti i ugasen !!! Obavezno ugasiti i prikazati na grafiku
        if (int(prekidac_gasi)==1): # OVo je malo nezgodno napisano...
            taster_odblokiraj.off()
            http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V12?value='+str(prekidac_gasi))
        else:
            taster_odblokiraj.on()
            http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V12?value='+str(prekidac_gasi))


    # Preuzmi RTC format podataka http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/rtc
        rtc_link = 'http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/rtc'
        rtc_format = http_get(rtc_link)
        RTC_raw = ure.search('\[(\d+)]', rtc_format).group(1)
        print ('\nRTC je      : ', RTC_raw )

    # Ispisi Vreme - Datum poslednje konekcije 1-red v10 2-red v11
        http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V10?value=TimeAndDate')
        http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V11?value='+str(RTC_raw))

#ThingSpeak WebHook
        http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V9?value=69')

        # DODATI DS18S20
        # DEKODOVATI RTC
        # SREDITI REGRESION DA MOZE DVOCIFREN BROJ
        # PODESITI ONLINE STATUS
        # PROVERITI ZASTO SE PRIKAZUJU V12,V3 A NE V2,V3
        # AKO BLOKIRAM KOTAO TREBA DA SE DISEJBLUJE DUGME ZA PALJENJE
        # DODATI NOTIFIKACIJE



    # #ThingSpeak iskoristi webhook ne ovako iz nekog razloga puca
    #     #http_get( 'https://api.thingspeak.com/update?api_key=J1T84N77WN3S33B8&field1='+str(vlaznost) )
    #     http_get( 'https://api.thingspeak.com/update?api_key=J1T84N77WN3S33B8&field2='+str(temperatura) )
        #Shttp_get( 'https://api.thingspeak.com/update?api_key=J1T84N77WN3S33B8&field3='+str(web_prekidac[-3]) )

        #print('\nRESPONSE\n')
        #print('Temp: {0:.2f}, Humi: {1:.2f}'.format(d.temperature(),d.humidity()))

   # Hendlovati status tastera
    except:
        machine.reset()
    print ('\nCekam ',pauza,'sekundi\n')
    time.sleep(pauza)

    # DODATI DECIMALNU VREDNOST ZA DHT11
    #https://forum.micropython.org/viewtopic.php?t=1392
