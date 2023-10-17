import socket
import os
import hashlib
from tqdm import tqdm
# Konfigurasi server
host = '192.168.1.26'  # Ganti dengan alamat IP atau nama host server
port = 8080         # Ganti dengan port yang sesuai dengan server

try:
    # Membuat koneksi ke server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    # Meminta operasi dari pengguna (SEARCH atau SEND)
    operation = input("Pilih operasi (SEARCH atau SEND): ")
    client_socket.send(operation.encode())

    if operation == "SEARCH":
        # Meminta search query dari pengguna
        query = input("Masukkan query pencarian: ")
        client_socket.send(query.encode())

        # Menerima hasil pencarian dari server
        search_results = client_socket.recv(1024).decode()

        if search_results == "No matching files found":
            print("Tidak ada file yang cocok dengan query.")
        else:
            print("Hasil pencarian:")
            print(search_results)
    elif operation == "SEND":
        # Meminta nama file yang akan diunduh
        filename = input("Masukkan nama file yang akan diunduh: ")

        #untuk menyesuaikan path sesuai device client
        current_directory = os.getcwd()
        destination_file = os.path.join(current_directory, os.path.basename(filename))
        source_file_normalization = os.path.normpath(filename)
        file_size = os.path.getsize(source_file_normalization)
        client_socket.send(filename.encode())

        # Menerima hash file dari server
        server_hash = client_socket.recv(64).decode()

        # Menerima data dari server
        data = b''
        progress_bar = tqdm(total=os.path.getsize(file_size), unit="B", unit_scale=True)
        while True:
            chunk = client_socket.recv(8388608)
            if not chunk:
                break
            data += chunk
            progress_bar.update(len(chunk))
        progress_bar.close()

        # Memeriksa hash file yang diterima
        client_hash = hashlib.sha256(data).hexdigest()
        if client_hash == server_hash:
            # Menyimpan data ke dalam file
            saved_filename = os.path.basename(filename)
            with open(saved_filename, 'wb') as file:
                file.write(data)
            print(f"File '{filename}' berhasil diterima dan disimpan sebagai '{saved_filename}'.")
        else:
            print("Hash file tidak cocok. File dapat rusak atau termodifikasi selama transfer.")
    else:
        print("Operasi tidak valid.")

except ConnectionRefusedError:
    print("Koneksi ditolak. Pastikan server sudah berjalan atau alamat dan port yang benar.")
except Exception as e:
    print(f"Terjadi kesalahan saat menghubungi server: {str(e)}")
finally:
    client_socket.close()
