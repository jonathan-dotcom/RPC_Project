import socket
import threading
import os
import logging
import hashlib

# Inisialisasi logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fungsi untuk mengirim file ke client
def send_file(client_socket, filename):
    try:
        with open(filename, 'rb') as file:
            file_size = os.path.getsize(filename)  # Get the file size
            client_socket.send(file_size)
            while True:
                data = file.read(8388608)
                if not data:
                    break
                client_socket.send(data)
            logger.info(f"File '{filename}' berhasil dikirim.")
    except FileNotFoundError:
        logger.error(f"File '{filename}' tidak ditemukan.")
        client_socket.send(b"File not found")
    except Exception as e:
        logger.error(f"Terjadi kesalahan saat mengirim file: {str(e)}")
    finally:
        client_socket.close()

# Fungsi untuk menghitung hash file
def calculate_file_hash(filename):
    sha256 = hashlib.sha256()
    with open(filename, 'rb') as file:
        while True:
            data = file.read(8388608)
            if not data:
                break
            sha256.update(data)
    return sha256.hexdigest()

# Fungsi untuk mencari file di direktori server
def search_files(directory, query):
    matching_files = []
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if query in filename:
                matching_files.append(os.path.join(root, filename))
    return matching_files

# Fungsi untuk menangani pencarian file dari client
def handle_search(client_socket):
    try:
        # Menerima permintaan pencarian dari client
        query = client_socket.recv(1024).decode()
        if not query:
            logger.warning("Permintaan pencarian kosong. Koneksi akan ditutup.")
            return

        # Melakukan pencarian file
        search_results = search_files('/home', query)  # Replace with the directory you want to search

        # Mengirim hasil pencarian ke client
        if search_results:
            result_str = '\n'.join(search_results)
            client_socket.send(result_str.encode())
        else:
            client_socket.send(b"No matching files found")

    except Exception as e:
        logger.error(f"Terjadi kesalahan saat menangani pencarian file: {str(e)}")
    finally:
        client_socket.close()

# Fungsi untuk menangani koneksi dari client
def handle_client(client_socket):
    try:
        # Menerima permintaan operasi dari client (pencarian atau pengiriman file)
        operation = client_socket.recv(1024).decode()
        if operation == "SEARCH":
            handle_search(client_socket)
        elif operation == "SEND":
            # Menerima permintaan nama file dari client
            filename = client_socket.recv(1024).decode()
            if not filename:
                logger.warning("Permintaan file kosong. Koneksi akan ditutup.")
                return

            # Validasi nama file
            if not os.path.isfile(filename):
                logger.error(f"File '{filename}' tidak ditemukan.")
                client_socket.send(b"File not found")
                return

            # Mengirim hash file sebelum mengirim file itu sendiri
            file_hash = calculate_file_hash(filename)
            client_socket.send(file_hash.encode())

            # Mengirim file
            send_file(client_socket, filename)
    except Exception as e:
        logger.error(f"Terjadi kesalahan saat menangani koneksi dari client: {str(e)}")
    finally:
        client_socket.close()

def main():
    # Konfigurasi server
    host = '192.168.1.26'
    port = 8080
    max_connections = 5  # Batasan jumlah koneksi yang diizinkan

    # Inisialisasi socket server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(max_connections)

    logger.info(f"Server listening on {host}:{port}")

    try:
        while True:
            # Menerima koneksi dari client
            client_socket, client_addr = server_socket.accept()
            logger.info(f"Accepted connection from {client_addr}")

            # Membuat thread baru untuk menangani koneksi dari client
            client_handler = threading.Thread(target=handle_client, args=(client_socket,))
            client_handler.start()
    except KeyboardInterrupt:
        logger.info("Server dihentikan.")
        server_socket.close()

if __name__ == "__main__":
    main()
