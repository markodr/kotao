import esp
import time
import dht
import socket
import network
import ure
import onewire, ds18x20
from machine import WDT
import utime
import network

'''
Izmerene vrednosti sa senzora
    V0 - Temperatura
    V1 - Vlaznost
    V4 - Temperatura vode u kotlu
Prekici za paljenje/gasenje senzora
    V2 - Prekidac PALI Grejanje
    V3 - Prekidac BLOKIRAJ Grejanje
Terminal
    V5 - Loguj custom exception
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
# PODESITI ONLINE STATUS

# Custom Exception za senzore, bynk i Thingspeak

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
def do_connect():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect('I9EBE', 'dTG7kKkAUJd4')
        while not sta_if.isconnected():
            pass
    print('network config:', sta_if.ifconfig())

esp.osdebug(None)
pauza = 60

#wdt = machine.WDT(5000)
#wdt.feed()

# Zabrana AP
ap_if = network.WLAN(network.AP_IF)
ap_if.active(False)
print ('\nAccess Point = ' , ap_if.active())
# Dozvola stanice
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
print ('Stanica = ', sta_if.active() )

# Definisanje modula
#taster_pali = machine.Pin(2, machine.Pin.OUT)
#taster_odblokiraj = machine.Pin(15, machine.Pin.OUT)

# Sobni senzor
d = dht.DHT11(machine.Pin(4))

# Senzor vode kotla
dat = machine.Pin(13)
ds = ds18x20.DS18X20(onewire.OneWire(dat))
roms = ds.scan()

# Ne treba za ovo
adc = machine.ADC(0)


# Povezivnje na web
print('\nDostupne mreze\n')
print(sta_if.scan())
do_connect()


while (True):
    # PRVO proveri da li smo povezani,
    if not sta_if.isconnected():
        do_connect()

# Merenje Senzora
    print('\nPocetak Merenja')
    d.measure()
    temperatura=d.temperature()
    vlaznost=d.humidity()
    print ('          Temperatura : ', temperatura)
    print ('          Vlaznost    : ',vlaznost)
    ds.convert_temp()
    time.sleep(1)
    for rom in roms:
        kotao_temperatura= ds.read_temp(rom)
        print( '          Temp. vode  : ', kotao_temperatura)
    print ('Kraj Merenja\n')

    try:
# BLINK
    # Vlaznost prostorije - Update v1
        http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V1?value='+str(vlaznost))
        print('Vlaznost : OK')
    # Temperatura prostorije - Update v0
        http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V0?value='+str(temperatura))
        print('Temperatura : OK')
    # Temperatura vode u kotlu - v4
        http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V4?value='+str(int(kotao_temperatura)))
        print('Kotao : OK')
    # Preuzmi RTC format podataka Update v10,v11 utime.localtime http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/rtc
        rtc_format = http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/rtc')
        RTC_raw = ure.search('\[(\d+)]', rtc_format).group(1)
        formatirano_vreme = utime.localtime(int(RTC_raw))
        #print ('RTC je      : ', RTC_raw, '=',formatirano_vreme)
    # Ispisi Vreme - Datum poslednje konekcije 1-red v10 2-red v11
        datum = '___' + str( formatirano_vreme[1]) + '.' + str(formatirano_vreme[2]) + '.' + str(formatirano_vreme[0]-30)
        #print(type(datum), datum)
        http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V10?value=' + datum )

        # Dodajemo 0 zbog formata sekundi
        if (formatirano_vreme[5]<10):
            vreme = '____' +  str(formatirano_vreme[3]) + ':' + str(formatirano_vreme[4]) + ':' + '0' + str(formatirano_vreme[5])
        else:
            vreme = '____' +  str(formatirano_vreme[3]) + ':' + str(formatirano_vreme[4]) + ':' + str(formatirano_vreme[5])
        http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V11?value=' + vreme )
        print('RTC : OK')
    # ThingSpeak https://community.blynk.cc/t/help-with-webhook-and-thingspeak/8242/3
        http_get( 'https://api.thingspeak.com/update?api_key=J1T84N77WN3S33B8&field1=' + str(temperatura) + '&field2=' + str(kotao_temperatura)  + '&field3=' + str(kotao_temperatura) + '&field4=' + str(vlaznost))
        print('ThingSpeak : OK')

    # Grejanje Taster PALI - Dowload/Update v2,v13
        web_prekidac_pali = http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/get/V2')
        prekidac_pali = ure.search('\[.\d.+\]', web_prekidac_pali).group(0)[2]
        #print( '\nUpali Grejanje je    : ', prekidac_pali)
        http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V13?value='+str(prekidac_pali))
        if (int(prekidac_pali)>0):
            taster_pali.on()
        else:
            taster_pali.off()
        print('Prekidac Grejanje : OK')

    # Grejanje Taster BLOKIRAJ Dowload/Update v3,v12
        web_prekidac_block = http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/get/V3')
        prekidac_gasi = ure.search('\[.\d.+\]', web_prekidac_block).group(0)[2]
        #print( 'Blokiraj Grejanje je : ', prekidac_gasi)
        http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V12?value='+str(prekidac_gasi))
        if (int(prekidac_gasi)>0): # OVo je malo nezgodno napisano...
            taster_odblokiraj.on()
        else:
            taster_odblokiraj.off()
        print('Prekidac Blokiraj : OK')

    except:

        print('\nPukao je UPDATE,pokusavam ponovo')
        time.sleep(10)
        continue
        # if not sta_if.isconnected():
        #     print('PUKAO SAM : Merim ponovo i povezujem se na WiFi')
        #     do_connect()
            # Ovde bi valjao reset ako se ne poveze za neko vreme

    print ('\nCekam ',pauza,'sekundi\n')
    time.sleep(pauza)
