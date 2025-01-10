"""
This script generates the ARM-GCC toolchain from the official ARM website
"""

from urllib.request import urlopen
from traceback import print_exc
import os
import sys
import zipfile
import tarfile
import shutil

BASE_URL = "https://developer.arm.com/-/media/Files/downloads/gnu/14.2.rel1/binrel/"


ALL_TOOLCHAINS = [
    "arm-gnu-toolchain-14.2.rel1-mingw-w64-x86_64-arm-none-eabi.zip",
    "arm-gnu-toolchain-14.2.rel1-x86_64-arm-none-eabi.tar.xz",
    "arm-gnu-toolchain-14.2.rel1-aarch64-arm-none-eabi.tar.xz",
    "arm-gnu-toolchain-14.2.rel1-darwin-x86_64-arm-none-eabi.tar.xz",
    "arm-gnu-toolchain-14.2.rel1-darwin-arm64-arm-none-eabi.tar.xz",
]

ALL_ARCHS = [
    "v6-m", # Cortex M0+ 
    "v7e-m+fp", # Cortex M4
    "v7e-m+dp", # Cortex M7
    "v8-m.main+fp" # Cortex M33
]


def download_file(url, target):
    if os.path.exists(target):
        print(f"File {target} already exists. Skipping download.")
        return
    print(f"Downloading {url} into {target}")
    try:
        with urlopen(url) as remote, open(target, "wb") as f:

            headers = dict(remote.info())
            expected_size = int(headers.get("Content-Length", 0))

            if not expected_size:
                print("URL has no Content-Length header")

            mb_expected = expected_size / 1048576
            block_size = (expected_size + 49) // 50
            blocks_downloaded = 0
            file_size_downloaded = 0

            while True:
                buffer = remote.read(block_size)
                if not buffer:
                    break
                file_size_downloaded += len(buffer)
                blocks_downloaded += 1
                f.write(buffer)

                mb_downloaded = file_size_downloaded / 1048576

                progress_bar = "    [ " + "━" * blocks_downloaded + " " * (50 - blocks_downloaded) + " ]"
                progress_bar += f" {mb_downloaded:.1f}/{mb_expected:.1f} MiB"
                print(progress_bar, end="\r")
        print()
    except Exception:
        print_exc()
        sys.exit("Failed to download files")


def extract_tar_xz(path: str, name: str):
    if os.path.exists(name):
        print(f"Folder {name} Already Exists. Skipping extract tar.")
        return
    print(f"Extracting {path}")
    with tarfile.open(path, "r:xz") as tf:
        tf.extractall(".", filter="data")
    print("Done extracting tar.")


def extract_zip(path: str, name: str):
    if os.path.exists(name):
        print(f"Folder {name} Already Exists. Skipping unzip.")
        return
    print(f"Unzipping {path}")
    with zipfile.ZipFile(path, "r") as zf:
        zf.extractall(name)
    print("Done unzipping.")


def delete_if_exist(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.isfile(path):
        os.remove(path)
    else:
        pass # does not exist


def delete_unused_folders(parent, folders_to_keep):
    for name in os.listdir(parent):
        if name not in folders_to_keep:
            delete_if_exist(os.path.join(parent, name))
    
    # only keep the hard float / no float option
    for folder in folders_to_keep:
        delete_if_exist(os.path.join(parent, folder, "softfp"))


def main():
    if not os.path.isdir("dist"):
        os.mkdir("dist")

    for toolchain in ALL_TOOLCHAINS:
        download_file(url=BASE_URL+toolchain, target=toolchain)
        if toolchain.endswith(".zip"):
            toolchain_dir = toolchain.removesuffix(".zip")
            extract_zip(toolchain, toolchain_dir)

            delete_if_exist(os.path.join(toolchain_dir, "libexec/gcc/arm-none-eabi/14.2.1/f951.exe"))
            delete_if_exist(os.path.join(toolchain_dir, "libexec/gcc/arm-none-eabi/14.2.1/lto1.exe"))
            delete_if_exist(os.path.join(toolchain_dir, "bin/arm-none-eabi-lto-dump.exe"))

        elif toolchain.endswith(".tar.xz"):
            toolchain_dir = toolchain.removesuffix(".tar.xz")
            extract_tar_xz(toolchain, toolchain_dir)

            delete_if_exist(os.path.join(toolchain_dir, "libexec/gcc/arm-none-eabi/14.2.1/f951"))
            delete_if_exist(os.path.join(toolchain_dir, "libexec/gcc/arm-none-eabi/14.2.1/lto1"))
            delete_if_exist(os.path.join(toolchain_dir, "bin/arm-none-eabi-lto-dump"))

        else:
            raise ValueError("unexpected format")
        
        thumb_path = os.path.join(toolchain_dir, "lib/gcc/arm-none-eabi/14.2.1/thumb")
        delete_unused_folders(thumb_path, ALL_ARCHS)
        thumb_path = os.path.join(toolchain_dir, "arm-none-eabi/lib/thumb")
        delete_unused_folders(thumb_path, ALL_ARCHS)

        delete_if_exist(os.path.join(toolchain_dir, "lib/gcc/arm-none-eabi/14.2.1/arm"))
        delete_if_exist(os.path.join(toolchain_dir, "arm-none-eabi/lib/arm"))

        # compress to archive
        with tarfile.open(os.path.join("dist", toolchain_dir + ".tar.xz"), "w:xz") as tar:
            tar.add(toolchain_dir)


if __name__ == "__main__":
    main()
