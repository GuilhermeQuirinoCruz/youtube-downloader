import os
from pathlib import Path
import platform

import pytubefix
from pytubefix import YouTube, Playlist

from moviepy.video.io.ffmpeg_tools import ffmpeg_merge_video_audio

DEFAULT_DOWNLOAD_PATH = '/var/home/guilhermequirino/Músicas'
TEMP_OUTPUT_PATH = './.temp'

# código original: https://dev.to/stokry/download-youtube-video-to-mp3-with-python-26p

# Não funciona porque o método Playlist só retorna os vídeos disponíveis
# def verificar_integridade_playlist(url):
#     playlist_verificar = Playlist(url)

#     tamanho_playlist = len(playlist_verificar.video_urls)
#     videos_disponiveis = tamanho_playlist
#     print(f'Tamanho: {tamanho_playlist}')
#     if tamanho_playlist == 0:
#         print('Playlist vazia')
#         return

#     for url_video_verificar in playlist_verificar.video_urls:
#         video = YouTube(url = url_video_verificar)
#         try:
#             video.check_availability()
#         except pytube.exceptions.VideoUnavailable:
#             print(f'Vídeo indisponível: {url_video_verificar}')
#             videos_disponiveis -= 1

#     porcentagem_disponiveis = (videos_disponiveis / tamanho_playlist) * 100
#     print(f'Integridade: {videos_disponiveis} / {tamanho_playlist} ({porcentagem_disponiveis}%)')

# Abre a pasta em que os arquivos foram baixados


def open_destination_folder(path):
    match platform.system():
        case 'Linux':
            os.system(f'xdg-open "{path}"')
        case 'Windows':
            os.system(f'start {path}')
        case _:
            print(path)


# Remove os caracteres que interferem no salvamento dos arquivos
def remove_invalid_characters(name):
    invalid_characters = ',.;:\'\'*|#</>\\?'
    for character in invalid_characters:
        name = name.replace(character, '')

    return name


# Formata o nome do vídeo ou playlist, removendo os caracteres
# inválidos e espaços antes e depois
def get_formatted_name(name):
    name = remove_invalid_characters(name)
    return name.strip()


# Adiciona um índice ao caminho do arquivo, evitando
# sobrescrever arquivos já existentes
def add_index_to_output_path(path, file_name, extension):
    index = 1
    fixed_path = Path(f'{path}/{file_name}{extension}')
    while os.path.exists(fixed_path):
        fixed_path = Path(f'{path}/{file_name} ({index}){extension}')
        index += 1

    return fixed_path


def add_index_to_folder_path(path):
    if (not os.path.exists(path)):
        return path
    
    path = add_index_to_output_path(path, '', '')
    # Remove o último '/' do caminho da pasta
    # https://stackoverflow.com/questions/2556108/rreplace-how-to-replace-the-last-occurrence-of-an-expression-in-a-string/59082116#59082116
    return ''.join(str(path).rsplit('/', 1))


# Exibe o progresso do download em MB
def show_download_progress(stream, _, remaining_bytes):
    stream_size_mb = round(stream.filesize / 1000000, 2)
    remaining_bytes_mb = round(remaining_bytes / 1000000, 2)
    remaining_bytes_mb = stream_size_mb - remaining_bytes_mb
    download_percentage = (remaining_bytes_mb / stream_size_mb) * 100

    # print('Progresso: %.2lf/%.2lf MB (%.2lf%%)' % (remaining_bytes_mb, tamanho_stream_mb, porcentagem_download))
    print(
        f'Progresso: {remaining_bytes_mb:.2f}/{download_percentage:.2f} MB ({download_percentage:.2f}%)')


# Exibe uma mensagem para downloads bem sucedidos
def download_finished(stream, _):
    print(f'Download Concluído: {stream.title}')


# Cria uma stream e baixa o vídeo ou áudio
def download_stream(video, audio_only=False):
    if audio_only:
        stream = video.streams.filter(
            adaptive=True, only_audio=True).order_by('abr').desc().first()
    else:
        stream = video.streams.filter(
            adaptive=True, file_extension='mp4', only_video=True).order_by('resolution').desc().first()

    return stream.download(output_path=TEMP_OUTPUT_PATH)


# Verifica a disponibilidade do vídeo
def is_video_available(yt):
    try:
        yt.check_availability()
    except pytubefix.exceptions.VideoUnavailable:
        return False

    return True


# Baixa e salva o arquivo
def save_output(yt, path, audio_only):
    if audio_only:
        audio_stream = download_stream(yt, True)

        # Salva o áudio renomeando o arquivo
        os.rename(audio_stream, path)
    else:
        video_stream = download_stream(yt, False)
        audio_stream = download_stream(yt, True)

        # Junta o vídeo e o áudio
        ffmpeg_merge_video_audio(
            video_stream, audio_stream, path, 'copy', 'copy', None)


def delete_temp_file(file):
    if os.path.exists(file):
        try:
            os.remove(file)
        except:
            print(f'Não foi possível remover o arquivo temporário: {file}')


# Recebe os parâmetros e realiza o download
def download(url='', audio_only=False, path=DEFAULT_DOWNLOAD_PATH, ignore_duplicates=True, open_folder=True):
    yt = YouTube(url=url,
                 on_progress_callback=show_download_progress,
                 on_complete_callback=download_finished)

    if not is_video_available(yt):
        print(f'Vídeo indisponível: {url}')
        return

    # Define a extensão do arquivo e o nome formatado
    extension = '.mp3' if audio_only else '.mp4'
    formatted_title = get_formatted_name(yt.title)
    file_path = Path(f'{path + '/' + formatted_title}{extension}')

    if ignore_duplicates and os.path.exists(file_path):
        print(f'Vídeo já foi baixado : {yt.title}')
        return

    print(f'Baixando: {yt.title}')

    # Salva o arquivo na pasta temporária
    output_path = f'{TEMP_OUTPUT_PATH}/output{extension}'
    save_output(yt, output_path, audio_only)

    # Adiciona um índice ao arquivo, caso necessário
    fixed_output_path = add_index_to_output_path(
        path, formatted_title, extension)
    
    # Move o arquivo para o destino
    os.rename(output_path, fixed_output_path)

    temp_file_path = f'{TEMP_OUTPUT_PATH}/{formatted_title}'
    delete_temp_file(f'{temp_file_path}.m4a')
    delete_temp_file(f'{temp_file_path}.mp4')

    if not fixed_output_path.exists():
        print('Falha ao renomear o arquivo')
        return

    print(f'Arquivo salvo em: {fixed_output_path.name}')

    if open_folder:
        open_destination_folder(path)


# Verifica se a playlist está vazia
def is_playlist_empty(playlist):
    return len(playlist.video_urls) == 0


# Cria uma pasta para a playlist
def create_playlist_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)


# Baixa a playlist, criando uma pasta e salvando cada arquivo
def download_playlist(url, audio_only, create_folder, ignore_duplicates, path=DEFAULT_DOWNLOAD_PATH):
    playlist = Playlist(url)

    if is_playlist_empty(playlist):
        print('Não foi possível realizar o download')
        print('Playlist vazia ou privada')
        return

    formatted_playlist_title = get_formatted_name(playlist.title)

    if create_folder:
        path += f'/{formatted_playlist_title}'
        path = add_index_to_folder_path(path)
        create_playlist_folder(path)
    
    print(f'Baixando playlist: {playlist.title}')

    # Baixa cada vídeo da playlist
    for current, video in enumerate(playlist.videos, 1):
        print(f'Baixando vídeo {current} de {playlist.length}')

        download(url=video.watch_url, audio_only=audio_only, path=path, ignore_duplicates=ignore_duplicates, open_folder=False)

    open_destination_folder(path)


# download(url='https://www.youtube.com/watch?v=a8CwpGARAsQ',
#          audio_only=True, path=DEFAULT_DOWNLOAD_PATH, ignore_duplicates=False, open_folder=True)

download_playlist(
    url='https://www.youtube.com/playlist?list=PLjo8TsMC7aERPpO9Qbl_shkQGeGMZUpDL', audio_only=True, create_folder=True, ignore_duplicates=False, path=DEFAULT_DOWNLOAD_PATH)