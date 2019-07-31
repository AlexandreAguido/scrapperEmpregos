from apiclient.http import MediaFileUpload
from os.path import dirname
from googleapiclient.discovery import build

class Drive:
    def __init__(self):
        self.service = build('drive', 'v3')      


    def list_files(self):
        """ 
        retorna uma lista com o nome e id
        dos arquivos na pasta do aplicativo
        """

        #especificar o uso da pasta do aplicativo
        #gera erro 403 caso nao tenha permissao para acessar o drive completo
        spaces = 'appDataFolder' 
        return self.service.files().list(spaces='appDataFolder', fields='files(id, name)').execute()['files']


    def upload_file(self, local_file_path):
        """
        envia o arquivo para a pasta do aplicativo

        params
        :local_file_path: = caminho do arquivo que será enviado
        """
        #criar arqivo que será enviado no corpo da requisicao
        media = MediaFileUpload(filename=local_file_path)
        remote_file_name = local_file_path.split('/')[-1]
        metadata = {'name' : remote_file_name,
                    'parents' : ['appDataFolder']
                    }
        resp = self.service.files().create(body=metadata, media_body = media, fields='name').execute()
        return resp


    def get_file_by_id(self, file_id):
        """retorna em bytes o arquivo com o id igual ao parametro
           file_id
        """
        file = self.service.files().get_media(fileId = file_id).execute()
        return file

    
    def remove_file(self, file_id):
        try:
            self.service.files().delete(fileId=file_id).execute()
        except Exception as e:
            print(e)
        

    def get_all_files(self, folder="./"):
        """
            Get all files on appfolder and saves on local path
            if the param folder not specified
        """
        files = self.list_files()
        for i in files:
            file = open(folder + i['name'], 'wb')
            file.write(self.get_file_by_id(i['id']))
            file.close()
            self.remove_file(i['id'])