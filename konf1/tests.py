import os
import unittest
from EMUL import ShellEmulator2

class TestShellEmulator(unittest.TestCase):
    def setUp(self):
        """Подготовка окружения для тестов."""
        self.shell = ShellEmulator2("config.xml")
        self.shell.current_directory = "/"

        os.makedirs(os.path.join(self.shell.fs_root, "dir1"), exist_ok=True)
        os.makedirs(os.path.join(self.shell.fs_root, "dir2"), exist_ok=True)
        with open(os.path.join(self.shell.fs_root, "file1.txt"), "w") as f:
            f.write("Test file 1")
        with open(os.path.join(self.shell.fs_root, "file2.txt"), "w") as f:
            f.write("Test file 2")

    def tearDown(self):
        """Очистка тестового окружения."""
        for root, dirs, files in os.walk(self.shell.fs_root, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))

    def test_ls_detailed(self):
        result = self.shell.ls(["-l"])
        self.assertRegex(result, r"file1.txt")

    def test_cd_valid(self):
        self.shell.cd(["dir1"])
        self.assertEqual(self.shell.current_directory, "/dir1")

    def test_cd_invalid(self):
        with self.assertRaises(FileNotFoundError):
            self.shell.cd(["nonexistent"])

    def test_cd_back(self):
        self.shell.cd(["dir1"])
        self.shell.cd([".."])
        self.assertEqual(self.shell.current_directory, "/")

    def test_chmod_invalid_file(self):
        with self.assertRaises(FileNotFoundError):
            self.shell.chmod(["755", "nonexistent.txt"])

    def test_chmod_invalid_mode(self):
        with self.assertRaises(ValueError):
            self.shell.chmod(["invalid", "file1.txt"])

    def test_cp_valid(self):
        self.shell.cp(["file1.txt", "dir1/file1_copy.txt"])
        copied_file = os.path.join(self.shell.fs_root, "dir1", "file1_copy.txt")
        self.assertTrue(os.path.exists(copied_file))

    def test_cp_invalid_source(self):
        with self.assertRaises(FileNotFoundError):
            self.shell.cp(["nonexistent.txt", "dir1/file1_copy.txt"])

    def test_whoami(self):
        result = self.shell.whoami()
        self.assertEqual(result, "user")

    def test_exit(self):
        with self.assertRaises(SystemExit):
            self.shell.exit()