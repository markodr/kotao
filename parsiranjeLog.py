# -*- coding: utf-8 -*-

def vadi_markere(lista,tekst):
    markeri=list()
    for i in range(len(lista)):
        if tekst in lista[i]:
            markeri.append(i)
    return markeri


def stampaj_problem(lista,pozicije,unazad):
    for line in pozicije:
        # print(lista[line])
        for i in range(unazad):
            print(lista[line-i])
        print('\n')

file = open('log.txt','r')
data = file.read().split('\n')
# Vadim reset modula
resetovano = vadi_markere(data,'rst cause')
print ('Resetvano : ',len(resetovano))



pukla_konekcija = vadi_markere(data,'Pukao je')
print ('Pukla konekcija : ',len(resetovano))


# print('\n\n\nVADIM RESET PODATKE : \n\n\n')
# stampaj_problem(data,resetovano,10)

print('\n\n\nVADIM PUKO SAM PODATKE : \n\n\n')
stampaj_problem(data,pukla_konekcija,5)
