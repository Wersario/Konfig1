import os
import zipfile
import xml.etree.ElementTree as ET
import csv
import datetime
import shutil

class ShellEmulator:
    def __init__(self, config_path):
        self.load_config(config_path)
        self.setup_filesystem()
        self.current_directory = "/"
        self.start_logging()

    def load_config(self, config_path):
        tree = ET.parse(config_path)
        root = tree.getroot()
        self.username = root.find('username').text
        self.hostname = root.find('hostname').text
        self.fs_zip_path = root.find('fs_zip').text
        self.log_path = root.find('log_file').text

    def setup_filesystem(self):
        with zipfile.ZipFile(self.fs_zip_path, 'r') as zip_ref:
            self.fs_root = "/tmp/virtual_fs"
            zip_ref.extractall(self.fs_root)

    def start_logging(self):
        self.log_file = open(self.log_path, 'w', newline='')
        self.logger = csv.writer(self.log_file)
        self.logger.writerow(['timestamp', 'user', 'command'])

    def log(self, command):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.logger.writerow([timestamp, self.username, command])

    def run(self):
        try:
            while True:
                command = input(f"{self.username}@{self.hostname}:{self.current_directory}$ ")
                self.execute_command(command.strip())
        except KeyboardInterrupt:
            self.exit()

    def execute_command(self, command):
        if command == "exit":
            self.exit()
        elif command.startswith("ls"):
            self.ls(command.split(" ")[1:])
        elif command.startswith("cd"):
            self.cd(command.split(" ")[1:])
        elif command.startswith("whoami"):
            self.whoami()
        elif command.startswith("chmod"):
            self.chmod(command.split(" ")[1:])
        elif command.startswith("cp"):
            self.cp(command.split(" ")[1:])
        else:
            print(f"Команда '{command}' не найдена")
        self.log(command)

    def ls(self, args=None):
        if args is None:
            args = []

        path = os.path.join(self.fs_root, self.current_directory[1:])
        if not os.path.exists(path):
            print(f"Ошибка: путь '{path}' не существует.")
            return

        show_hidden = "-a" in args
        detailed = "-l" in args
        human_readable = "-h" in args

        try:
            entries = os.listdir(path)
            if not show_hidden:
                entries = [entry for entry in entries if not entry.startswith('.')]

            entries.sort()
            for entry in entries:
                full_path = os.path.join(path, entry)
                if detailed:
                    stats = os.stat(full_path)
                    size = stats.st_size
                    mode = oct(stats.st_mode)[-3:]
                    mtime = datetime.datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    size_str = self._human_readable_size(size) if human_readable else f"{size}B"
                    print(f"{mode} {size_str} {mtime} {entry}")
                else:
                    print(entry)
        except Exception as e:
            print(f"Ошибка: {e}")

    def _human_readable_size(self, size):
        """Возвращает размер файла в удобочитаемом формате."""
        for unit in ['B', 'K', 'M', 'G', 'T']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}P"

    def cd(self, args):
        if not args:
            return
        path = args[0]
        if path == "..":
            self.current_directory = os.path.dirname(self.current_directory)
        else:
            new_path = os.path.join(self.fs_root, path)
            if os.path.isdir(new_path):
                self.current_directory = os.path.join(self.current_directory, path)
            else:
                print(f"Ошибка: '{path}' — не существует")

    def whoami(self):
        print(self.username)
        return self.username
        
    def chmod(self, args):
        if len(args) != 2:
            print("Usage: chmod <mode> <file>")
            return

        mode, filename = args
        path = os.path.join(self.fs_root, self.current_directory[1:], filename)

        if not os.path.exists(path):
            print(f"Ошибка: файл '{filename}' не найден.")
            return

        if not mode.isdigit() or len(mode) != 3:
            print("Ошибка: режим должен быть числом из трех цифр, например 755.")
            return

        try:
            mode_int = int(mode, 8)  # Переводим строку в восьмеричное число
            os.chmod(path, mode_int)
            print(f"Права для '{filename}' изменены на {mode}.")
        except Exception as e:
            print(f"Ошибка при изменении прав: {e}")
            
    def cp(self, args):
        if len(args) != 2:
            print("Usage: cp <source> <destination>")
            return

        source, destination = args
        source_path = os.path.join(self.fs_root, self.current_directory[1:], source)
        destination_path = os.path.join(self.fs_root, self.current_directory[1:], destination)

        if not os.path.exists(source_path):
            print(f"Ошибка: источник '{source}' не найден.")
            return

        try:
            if os.path.isdir(source_path):
                if os.path.exists(destination_path) and not os.path.isdir(destination_path):
                    print(f"Ошибка: путь назначения '{destination}' существует и не является папкой.")
                    return
                os.makedirs(destination_path, exist_ok=True)
                for item in os.listdir(source_path):
                    item_source = os.path.join(source_path, item)
                    item_destination = os.path.join(destination_path, item)
                    if os.path.isdir(item_source):
                        self.cp([item_source, item_destination])
                    else:
                        shutil.copy2(item_source, item_destination)
            else:
                os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                shutil.copy2(source_path, destination_path)

            print(f"'{source}' скопирован в '{destination}'.")
        except Exception as e:
            print(f"Ошибка при копировании: {e}")

    def exit(self):
        print("Выход из эмулятора.")
        self.log_file.close()
        exit()

if __name__ == "__main__":
    emulator = ShellEmulator("config.xml")
    emulator.run()