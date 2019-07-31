#!/usr/bin/python3
# script para buscar vagas no site
# www.trabalhabrasil.com.br


import requests, json
from bs4 import BeautifulSoup
from functions import *
from queue import Queue
from threading import Thread, Lock
import re
from google_drive import Drive



def get_vagas():
    """
       retorna uma lista com as vagas de
       10 paginas ordenadas pela data de criacao
    """
    vagas = []
    base_url = "https://www.trabalhabrasil.com.br/api/v1.0/Job/List?idFuncao=0&idCidade=0&pagina={}&pesquisa=&ordenacao=1&idUsuario="
    for i in range(1, 11):
        url = base_url.format(i)
        resp = requests.get(url, headers=get_headers())
        vagas += resp.json()
    return vagas

def complete_description(ids, vagas):
    """
    Completa a descricao de uma vaga
    """
    while not ids.empty():
        i = ids.get()
        url = vagas[i]['url']
        resp = requests.get(url, headers=get_headers()).text
        soup = BeautifulSoup(resp, 'html.parser')
        descricao = soup.find_all(['h6', 'p'], {'class' : 'job-plain-text'})[-1]      
        with Lock():
            try:vagas[i]['descricao'] = str(descricao.string).replace('\r\n', '<br>')
            except:
                print(url, descricao, sep="\n"*5)
                exit()
        ids.task_done()



def clean_vagas(vagas):
    """
    retorna uma lista das vagas filtradas com as informacoes
    uteis e completar a descricao caso necessario
    """

    vagas_clean = {}
    ids = Queue() # vagas com a descricao incompleta
    #campos originais       #significado
    #id                      id da vaga
    #d                       descricao
    #df                      titulo
    #ne                      empresa
    #u                       "slug" url relativa da vaga
    #dc                      cidade
    #uf                      estado
    #qv                      quantidade
    #tt                      subtitulo  da vaga
    #sl                      salario
    #pcd                     pessoa com deficiencia

    for v in vagas:
        _id = v['id']
        if v['d'].endswith('...'):
            ids.put(_id)
        v = {'descricao' : v['d'].replace('\r\n', '<br>'),
                'id' : _id,
                'titulo' : str(v['df']).title(),
                'empresa' : str(v['ne']).title(),
                'url' : "https://trabalhabrasil.com.br/" + v['u'],
                'cidade' : str(v['dc']).title(),
                'uf' : str(v['uf']).upper(),
                'quantidade' : v['qv'],
                'sub_titulo' : str(v['tt']).title(),
                'salario' : re.search("[\d\.,]+", v['sl']),
                'pcd' : v['pcd']
        
        }
        if v['salario']: v['salario'] = int(re.sub('[\D]', '', v['salario'].group(0))) / 100.0
        else: v['salario'] = -1 

        # empresa nao especificada
        if v['empresa'] == 'None': v['empresa'] = 'Não Informada'
        vagas_clean[_id] = v

    #completar descricao das vagas
    for i in range(10):
        t = Thread(target=complete_description, args=(ids,vagas_clean), daemon=True)
        t.start()
    ids.join()
    

    return [vagas_clean[x] for x in vagas_clean.keys()]


def run():
    vagas = get_vagas()
    vagas = clean_vagas(vagas)
    fname = get_random_name(15) + '.json'
    with open(fname, 'w') as file:
        json.dump(vagas,file, ensure_ascii=False)
    Drive().upload_file(fname)


