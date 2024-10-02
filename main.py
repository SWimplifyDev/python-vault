from cryptography.fernet import Fernet, InvalidToken
from InquirerPy import inquirer
import os
import platform
from datetime import datetime
import psutil

import tempfile

# create timestamp, it will be used to create a name to a report file
time_now = datetime.now().strftime("%d-%b-%Y-%H%M%S")

MAX_SIZE = 1024

# print messages to user in console for information
def log(message:str, type:str='INFO')->None:
    print(f"[{type}] {message}")

# write a file from bytes data
def write_file_at(file_path:str, data:bytes)->None:
    with open(file_path, 'wb') as file:
        file.write(data)

# reads a file and return data in bytes
def read_file_at(file_path:str)->bytes:
    with open(file_path, 'rb') as file:
        data = file.read()
    return data

# generates a key to use for encryption
def get_new_key() -> bytes:
    return Fernet.generate_key()

# write report file with key and files that are being encrypted
def write_report(time_now:str, line_note:str):
    with open(f"Encryption_report-{time_now}.txt", 'a') as file:
        file.write(f"{line_note}\n")

# encrypts content of a file
def encrypt_file_at(file_path:str, key:bytes):
    data = read_file_at(file_path)
    try:
        encrypted_data  = Fernet(key).encrypt(data)
    except ValueError:
        log("Not a valid key for encryption", type='ERROR')
        return
    write_file_at(file_path, encrypted_data)
    write_report(time_now, f"{file_path}")
    log(f"File at '{file_path}' is now locked")

# encrypts content of a file
def encrypt_file_at_v2(file_path:str, key:bytes):
    temp_file_path = tempfile.mktemp()
    with open(file_path, 'rb') as file, open(temp_file_path, 'wb') as temp_file:
        while data_chunk := file.read(MAX_SIZE):
            encrypt_chunk = Fernet(key).encrypt(data_chunk)
            temp_file.write(encrypt_chunk)

    os.replace(temp_file_path, file_path)
    write_report(time_now, f"{file_path}")
    log(f"File at '{file_path}' is now locked")

# decrypts content of a file
def decrypt_file_v2(file_path:str, key:bytes):
    temp_file_path = tempfile.mktemp()
    with open(file_path, 'rb') as file, open(temp_file_path, 'wb') as temp_file:
        while data_chunk := file.read(MAX_SIZE + 44):
            decrypt_chunk = Fernet(key).decrypt(data_chunk)
            temp_file.write(decrypt_chunk)
    
    os.replace(temp_file_path, file_path)
    log(f"File at '{file_path}' is now unlocked")

# decrypts content of a file
def decrypt_file(file_path:str, key:bytes):
    data = read_file_at(file_path)
    try:
        decrypted_data = Fernet(key).decrypt(data)
    except InvalidToken:
        log("Invalid Key", type="ERROR")
        return
    write_file_at(file_path, decrypted_data)
    log(f"File at '{file_path}' is now unlocked")

# performs a function on all files on path
def process_folder(folder_path, func):
    if func.__name__ == "encrypt_file_at":
        key = get_new_key()
        write_report(time_now, f"KEY:{key.decode('utf-8')}\n\nFILES:")
        log(f"Key = {key.decode('utf-8')}")
    else:
        key:str = inquirer.text("Enter Key:").execute()
        key = key.encode('utf-8')

    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            func(file_path,key)     

# list drives connected to the computer system
def list_drives_available()->list:
    os_type = platform.system()
    if os_type == "Windows":
        return [f"{chr(x)}:\\" for x in range(65, 91) if os.path.exists(f"{chr(x)}:\\")]
    else:
        partitions = psutil.disk_partitions()
        return [partition.mountpoint for partition in partitions]

# list all dirs and files on a path
def list_dir(path:str):
    options = os.listdir(path)
    options.append('< GO BACK')
    subdir = inquirer.select("Select Dir or File:", choices=options).execute()
    if subdir == "< GO BACK":
        return os.path.dirname(path)
    return subdir

# clear the console
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def dir_navigator(drive:str):
    path = drive
    while True:
        clear_console()
        subdir = list_dir(path)
        path = os.path.join(path,subdir)
        min_action = inquirer.select(f"Action on - {subdir}", choices=['Open', 'Encrypt', 'Decrypt', 'CANCEL']).execute()
        
        if min_action == 'Encrypt':
            proceed = inquirer.confirm(message=f"All files at {path} will be Encrypted, Proceed?", default=True).execute()
            if proceed:
                process_folder(path, encrypt_file_at)
                return        
        
        if min_action == 'Decrypt':
             proceed = inquirer.confirm(message=f"All files at {path} will be Decrypted, Proceed?", default=True).execute()
             if proceed:
                 process_folder(path, decrypt_file)
                 return
        
        if min_action == 'CANCEL':
            return
        
        if min_action == "Go Back":
            path = os.path.dirname(path)       


if __name__ == "__main__":
    drives = list_drives_available()
    drives.append("Exit")
    drive = inquirer.select("Drives connected to this computer:",choices=drives, default="Exit").execute()
    dir_navigator(drive)
    log("Program ended")