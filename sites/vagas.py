#!/usr/bin/python3
import json, re, requests
from threading import Thread
from queue import Queue
from bs4 import BeautifulSoup
from google_drive import Drive
from functions import *

def worker(fila, vagas):
    """Utiliza threads para procurar pelas vagas do dia"""
    while not fila.empty():
        pg_number = fila.get()
        url = "https://www.vagas.com.br/vagas-de--?ordenar_por=" + \
               "mais_recentes&q=+&pagina={}".format(pg_number)
        resp = requests.get(url, headers=get_headers()).text
        soup = BeautifulSoup(resp, 'html.parser')
        vagas_lista = soup.find('div', {'id' : 'todasVagas'}).ul.find_all('li')

        # buscar id das vagas e parar quando achar uma vaga que nao seja do dia
        for vaga in vagas_lista:
            if vaga.find('span', {'class' : "icon-relogio-24"}).string != "Hoje":
                break
            v_link = vaga.find('a')['href']
            vagas.add(v_link)

        fila.task_done()

def get_vagas_ids():
    """retorna uma lista com os links das
    vagas publicadas hoje"""
    num_paginas = 60
    vagas = set()
    fila = Queue()
    for i in range(1, num_paginas+1):
        fila.put(i) 
    #iniciar threads
    for i in range(10):
        t = Thread(target=worker, args=(fila,vagas), daemon=True)
        t.start()

    fila.join()
    return vagas


def search_vaga_info(vagas_info, fila):
    """
        armazenar em vagas_info as vagas identificadas
        pelos ids na fila
    """
    while not fila.empty():
        vaga = {}
        v_id = fila.get()
        url = "https://www.vagas.com.br" + v_id
        resp = requests.get(url, headers=get_headers()).text
        soup = BeautifulSoup(resp, 'html.parser')
        soup = soup.find('article', class_='vaga')
        try:
            vaga['titulo'] = str(soup.find('div', class_='nome-do-cargo').string)
            vaga['titulo'] = vaga['titulo'].split('-')[0].strip().title()
        except:
            vaga['titulo'] = v_id.split('/')[-1].split('-')
            vaga['titulo'] = ' '.join(vaga['titulo']).title()
        vaga['empresa'] = str(soup.find('span', class_='empresaVaga').string).strip().title()
        vaga['salario'] = str(soup.find('div', class_='infoVaga').find('ul').find_all('li')[0].find('span').string)
        vaga['cidade'] = str(soup.find('div', class_='infoVaga').find('ul').find_all('li')[1].find('span').string).strip().title()
        vaga['descricao'] = str(soup.find('div', class_='texto'))
        vaga['url'] = url

        #converter salario para numero decimal
        salario = re.search('[\d\.,]+', vaga['salario'])
        if salario:
            vaga['salario'] = int(re.sub('[\D]', '', salario.group(0))) / 1.0
            if vaga['salario'] > 20000: vaga['salario'] /= 100.0
        else:
            vaga['salario'] = -1
                
        vaga['descricao'] = re.sub('<p>\s*</p>', '', vaga['descricao'])
        vagas_info.append(vaga)
        fila.task_done()

    

def run():
    num_threads = 10
    vagas_ids = get_vagas_ids()
    vagas_info = []
    fila_vagas = Queue()
    for i in vagas_ids:
        fila_vagas.put(i)
    for i in range(num_threads):
        t = Thread(target=search_vaga_info, args =(vagas_info,fila_vagas),
            daemon=True)
        t.start()
    fila_vagas.join()
    fname = get_random_name(12) + '.json'
    with open(fname, 'w') as file:
        json.dump(vagas_info, file, ensure_ascii=False)
    
    #gravar info das vagas e enviar ao drive
    Drive().upload_file(fname)

