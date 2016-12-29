import wget
import tarfile
import os
import gzip
import zipfile
from time import sleep
import threading
from queue import Queue


def extract_archive(source_path, destination_path=None, delete_originals=False):
    """
    Attempts to decompress the following formats for input filepath
    Support formats include `.tar.gz`, `.tar`, `.gz`, `.zip`.
    :param source_path:         a file path to an archive
    :param destination_path:    path to unzip, will be same name with dropped extension if left None
    :param delete_originals:    Set to "True" if archives may be deleted after
                                their contents is successful extracted.
    """

    head, tail = os.path.split(source_path)

    def set_destpath(destpath, file_ext):
        if destpath is not None:
            return destpath
        else:
            return os.path.join(head, tail.replace(file_ext, ""))

    if source_path.endswith(".tar.gz"):
        with tarfile.open(source_path, 'r:gz') as tfile:
            tfile.extractall(set_destpath(destination_path, ".tar.gz"))
            ret = destination_path

    # gzip only compresses single files
    elif source_path.endswith(".gz"):
        with gzip.open(source_path, 'rb') as gzfile:
            content = gzfile.read()
            with open(set_destpath(destination_path, ".gz"), 'wb') as of:
                of.write(content)
            ret = destination_path

    elif source_path.endswith(".tar"):
        with tarfile.open(source_path, 'r') as tfile:
            tfile.extractall(set_destpath(destination_path, ".tar"))
            ret = destination_path

    elif source_path.endswith(".zip"):
        with zipfile.ZipFile(source_path, "r") as zipf:
            zipf.extractall(set_destpath(destination_path, ".zip"))
            ret = destination_path

    else:
        raise Exception("supported types are tar.gz, gz, tar, zip")

    print("Extracted {0}".format(source_path))
    if delete_originals:
        os.remove(source_path)

    return ret


class BaseDownloader(object):
    """ basic downloader class with general/universal download utils """

    def __init__(self, local_dir):
        self.local_dir = local_dir
        self.queue = []

        if not os.path.exists(local_dir):
            os.mkdir(local_dir)

    @staticmethod
    def _download(source, dest, retries=2):
        trynum = 0
        while trynum < retries:
            try:
                wget.download(url=source, out=dest)
                return dest
            except:
                sleep(1)

    @staticmethod
    def _extract(source, dest):
        """ extracts a file to destination"""
        return extract_archive(source, dest, delete_originals=False)

    def _raw_destination_mapper(self, source):
        """ returns raw download destination from source url"""
        filename = os.path.basename(source)
        return os.path.join(self.local_dir, filename)

    def _ext_destination_mapper(self, source):
        """ maps a raw destination into an extracted directory dest """
        filename = os.path.basename(source).replace(".tar.gz", "")
        tilename = filename
        return os.path.join(self.local_dir, tilename)

    def download(self, source, mode='w', cleanup=True):
        """
        Downloads the source url and extracts it to a folder. Returns
        a tuple with the extract destination, and a bool to indicate if it is a
        fresh download or if it was already found at that location.

        :param source:  url from which to download data
        :param mode:    either 'w' or 'w+' to write or overwrite
        :param cleanup: use True to delete intermediate files (the tar.gz's)
        :return: tuple(destination path (str), new_download? (bool))
        """
        raw_dest = self._raw_destination_mapper(source)
        ext_dest = self._ext_destination_mapper(raw_dest)
        if not os.path.exists(ext_dest) or mode == 'w+':
            self._download(source, raw_dest)
            self._extract(raw_dest, ext_dest)
            fresh = True
        else:
            print("Found: {0}, Use mode='w+' to force rewrite".format(ext_dest))
            fresh = False
        if cleanup and os.path.exists(raw_dest):
            os.remove(raw_dest)
        return ext_dest, fresh