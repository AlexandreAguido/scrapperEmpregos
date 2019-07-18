#funcoes usadas por multiplos arquivos 
import re
from string import ascii_letters as alfa
from random import sample, choice

def get_headers():
    ua_list = [
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/7046A194A"
]
    return {"User-Agent": choice(ua_list)}

def get_random_name(size):
    """string aleatoria de tamanho <size>"""
    return ''.join(sample(alfa, size))

def remove_html_tags(vaga):
    """ remove tags html junto com seu conteudo"""
    p1 = re.compile(r'< *br[^\w/]*>')
    p2 = re.compile(r'<[^>]+>|\s{2,}')
    for key in vaga.keys():
        vaga[key] = p1.sub('\n', str(vaga[key]))
        vaga[key] = p2.sub('', str(vaga[key]))
    return vaga