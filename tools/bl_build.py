#!/usr/bin/env python
"""
Bootloader Build Tool

This tool is responsible for building the bootloader from source and copying
the build outputs into the host tools directory for programming.
"""
import argparse
import os
import pathlib
import shutil
import subprocess

from Crypto.Random import get_random_bytes
from Crypto.PublicKey import ECC

FILE_DIR = pathlib.Path(__file__).parent.absolute()


# converts binary string to c array so that we can take it in as input
def arrayize(binary_string):
    return '{' + ','.join(['0x' + x for x in binary_string.hex()]) + '}'

def copy_initial_firmware(binary_path):
    """
    Copy the initial firmware binary to the bootloader build directory
    Return:
        None
    """
    # Change into directory containing tools
    os.chdir(FILE_DIR)
    bootloader = FILE_DIR / '..' / 'bootloader'
    shutil.copy(binary_path, bootloader / 'src' / 'firmware.bin')


def make_bootloader():
    """
    Build the bootloader from source.

    Return:
        True if successful, False otherwise.
    """
    # Change into directory containing bootloader.
    bootloader = FILE_DIR / '..' / 'bootloader'
    os.chdir(bootloader)

    aes_key = get_random_bytes(16)
    vkey = get_random_bytes(16)
    
    
    key = ECC.generate(curve='ed25519')

    private_key = key.export_key(format='DER')
    public_key = key.public_key().export_key(format='DER')

    # write keys to file
    with open('secret_build_output.txt', 'wb+') as f:
        f.write(aes_key)
        f.write(private_key)
        f.write(public_key)
        f.write(vkey)
    subprocess.call('make clean', shell=True)
    status = subprocess.call(f'make AES_KEY={arrayize(aes_key)} ECC_KEY={arrayize(public_key)} V_KEY={arrayize(vkey)}', shell=True)

    # Return True if make returned 0, otherwise return False.
    return (status == 0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Bootloader Build Tool')
    parser.add_argument("--initial-firmware", help="Path to the the firmware binary.", default=None)
    args = parser.parse_args()
    if args.initial_firmware is None:
        binary_path = FILE_DIR / '..' / 'firmware' / 'firmware' / 'gcc' / 'main.bin'
    else:
        binary_path = os.path.abspath(pathlib.Path(args.initial_firmware))

    if not os.path.isfile(binary_path):
        raise FileNotFoundError(
            "ERROR: {} does not exist or is not a file. You may have to call \"make\" in the firmware directory.".format(
                binary_path))

    copy_initial_firmware(binary_path)
    make_bootloader()
