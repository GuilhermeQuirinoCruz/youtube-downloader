import os
from dotenv import load_dotenv

import backend

load_dotenv()

DEFAULT_DOWNLOAD_PATH = os.getenv('DEFAULT_DOWNLOAD_PATH') or ''
ACCEPT_STR = ['S', 's', '']


def main():
    print('YouTube Downloader')
    print('------------------')

    while (True):
        url = input('URL do vídeo ou playlist: ')

        is_playlist = '?list=' in url

        if (not backend.is_url_valid(url, is_playlist)):
            print('URL inválida')
            continue

        path = input(
            'Caminho para download (deixe em branco para utilizar o padrão): ') or DEFAULT_DOWNLOAD_PATH
        if (not os.path.exists(path)):
            print('Caminho inválido')
            continue

        audio_only = input('Baixar apenas o aúdio? [S/n] ') in ACCEPT_STR

        # print('Ignorar arquivos repetidos? [S/n]')
        ignore_duplicates = input(
            'Ignorar arquivos repetidos? [S/n] ') in ACCEPT_STR

        if (is_playlist):
            create_folder = input('Criar uma pasta nova? [S/n] ') in ACCEPT_STR

            backend.download_playlist(
                url, path, audio_only, ignore_duplicates, create_folder)
        else:
            open_folder = input(
                'Abrir a pasta ao final do download? [S/n] ') in ACCEPT_STR

            backend.download(url, path, audio_only,
                             ignore_duplicates, open_folder)

        if input('Deseja realizar outro download? [S/n] ') not in ACCEPT_STR:
            break


if __name__ == "__main__":
    main()