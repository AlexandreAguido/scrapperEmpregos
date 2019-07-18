#!/usr/bin/python3
# script para buscar vagas no site balcaodeempregos.com.br

import re, requests, json
from bs4 import BeautifulSoup
from random import choice
from queue import Queue
from threading import Thread, Lock
from functions import *
from google_drive import Drive

def get_vagas_id(periodo="day"):
    """ Busca id das vagas de acordo com a opcao
        do parametro periodo que sao
        day, week or month 
        Retorna lista com os ids das vagas      
    """
    base_url = "https://www.balcaodeempregos.com.br/Vagas/Buscar/?cadastro="+\
    "{}&pagina={}&submitcadastro=Refinar"
    id_list = set()
    page = 1
    patt = re.compile('\d')
    opts = {
        "day": "Hoje",
        "week": "Última semana",
        "month": "Último mês"
    }
    
    #parar busca quando encontrar id repetido
    while(True):
        url = base_url.format(opts[periodo], page)
        headers=get_headers()
        resp = requests.get(url, headers=headers).text
        soup = BeautifulSoup(resp, "html.parser")
        ids = [x['id-vaga'] for x in soup.find_all("div", {"id-vaga" : patt})]
        list_size = len(id_list)
        id_list = set.union(id_list, ids)
        if(list_size == len(id_list)):break
        page += 1
    return id_list


def get_vaga_info(fila, vagas):
    """ Cria uma lista e guarda em <vagas_info> com as seguintes 
        informacoes das vagas: empresa, titulo, areas, quantidade, 
        uf, cidade, escolaridade, salario, descricao, email, dataCadastro
    """
    while not fila.empty():
        vaga_id = fila.get()
        url = "https://www.balcaodeempregos.com.br/Vaga/GetVagaById"
        data = {"id": vaga_id}
        r = requests.get(url, data=data)
        vaga_full = r.json()['vaga']
        vaga_info = {
            "url":  'https://www.balcaodeempregos.com.br/vaga-visualizar/' + str(vaga_id),
            "empresa" : str(vaga_full['Empresa']).title(),
            "titulo" : str(vaga_full['Titulo']).title(),
            "quantidade" : vaga_full['Quantidade'],
            "uf": str(vaga_full["UF"]).upper(),
            "cidade": str(vaga_full['Cidade']).title(),
            "escolaridade": str(vaga_full["Escolaridade"]).title(),
            "descricao": vaga_full["Descricao"],
            "email_empresa": vaga_full["Email"]
            }
        salario = re.search("R\$\s*[\d\.,]+", vaga_info["descricao"])
        if salario == None:
            if vaga_full['Salario'] == 'A combinar': vaga_info["salario"] = -1
            else: vaga_info["salario"] = int(re.sub('[\D]', '',  vaga_full['Salario'])) / 100.0
        else:
            vaga_info['salario'] = int(re.sub('[\D]', '', salario.group(0))) / 100.0
        with Lock():
            vagas.append(vaga_info)
        fila.task_done()


def run():
    """Funcao que controla a execucao do scrapper"""
    vagas = []
    fila_id = Queue()
    drive = Drive()
    num_threads = 10
    vaga_ids = get_vagas_id('day')

    #busca com auxilio de threads
    for i in vaga_ids:
        fila_id.put(i)
    for i in range(num_threads):
        t = Thread(target=get_vaga_info, args=(fila_id, vagas), daemon=True)
        t.start()
    fila_id.join() 

    #cria json com as vagas e envia para o drive
    fname = get_random_name(15) + '.json'
    with open (fname, "w")  as file:
        json.dump(vagas, file, ensure_ascii=False)
    fname = drive.upload_file(fname)


