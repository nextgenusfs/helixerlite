import subprocess
import sys
import os
import errno
import socket
from urllib.request import urlopen
import helixerpost
from .__init__ import __version__


def human_readable_size(size, decimal_places=2):
    """
    Convert a size in bytes to a human-readable string representation.

    This function takes a size in bytes and converts it to a more human-readable format,
    using units such as B, KiB, MiB, GiB, TiB, and PiB. The size is formatted to the specified
    number of decimal places.

    Parameters:
    - size (float): The size in bytes to convert.
    - decimal_places (int, optional): The number of decimal places to include in the output (default is 2).

    Returns:
    - str: A string representing the size in a human-readable format with the appropriate unit.
    """
    for unit in ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]:
        if size < 1024.0 or unit == "PiB":
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"


def download(url, name, wget=False):
    """
    Download a file from a given URL.

    This function downloads a file from the specified URL and saves it with the given name.
    It can use either the `wget` command-line tool or Python's `urllib` for downloading,
    depending on the `wget` flag.

    Parameters:
    - url (str): The URL of the file to download.
    - name (str): The name to save the downloaded file as.
    - wget (bool, optional): Flag to use `wget` for downloading (default is False).

    Returns:
    None
    """
    if wget:
        # download with wget
        cmd = ["wget", "-O", name, "--no-check-certificate", "-t", "2", "-c", url]
        subprocess.call(cmd)
    else:
        file_name = name
        try:
            u = urlopen(url)
            f = open(file_name, "wb")
            block_sz = 8192
            while True:
                buffer = u.read(block_sz)
                if not buffer:
                    break
                f.write(buffer)
            f.close()
        except socket.error as e:
            if e.errno != errno.ECONNRESET:
                raise
            pass


def prediction2gff3(
    hd_genome,
    hd_prediction,
    gffout,
    window_size=100,
    edge_threshold=0.1,
    peak_threshold=0.8,
    min_coding_length=60,
):
    # helixer_post_bin <genome.h5> <predictions.h5> <window_size> <edge_threshold> <peak_threshold> <min_coding_length> <output.gff3>
    cmd = [
        "helixer_post_bin",
        hd_genome,
        hd_prediction,
        str(window_size),
        str(edge_threshold),
        str(peak_threshold),
        str(min_coding_length),
        gffout,
    ]
    runprocess(cmd)


def preds2gff3(
    hd_genome,
    hd_prediction,
    gffout,
    window_size=100,
    edge_threshold=0.1,
    peak_threshold=0.8,
    min_coding_length=60,
):
    # helixer_post_bin <genome.h5> <predictions.h5> <window_size> <edge_threshold> <peak_threshold> <min_coding_length> <output.gff3>
    helixerpost.run_helixer_post(
        hd_genome,
        hd_prediction,
        window_size,
        edge_threshold,
        peak_threshold,
        min_coding_length,
        gffout,
    )


def runprocess(cmd, stdout=False, stderr=False, cwd=".", debug=False):
    if not stdout and not stderr:
        proc = subprocess.Popen(
            cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    elif stdout and not stderr:
        with open(stdout, "w") as outfile:
            proc = subprocess.Popen(
                cmd, cwd=cwd, stdout=outfile, stderr=subprocess.PIPE
            )
    elif not stdout and stderr:
        with open(stderr, "w") as outfile:
            proc = subprocess.Popen(
                cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=outfile
            )
    elif stdout and stderr:
        if stdout == stderr:
            with open(stdout, "w") as outfile:
                proc = subprocess.Popen(cmd, cwd=cwd, stdout=outfile, stderr=outfile)
        else:
            with open(stdout, "w") as outfile1:
                with open(stderr, "w") as outfile2:
                    proc = subprocess.Popen(
                        cmd, cwd=cwd, stdout=outfile1, stderr=outfile2
                    )
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        sys.stderr.write("CMD ERROR: {}".format(" ".join(cmd)))
        if stdout:
            sys.stderr.write(stdout.decode("utf-8"))
        if stderr:
            sys.stderr.write(stderr.decode("utf-8"))
        sys.exit(1)
    if debug:
        if stdout:
            sys.stderr.write(stdout.decode("utf-8"))
        if stderr:
            sys.stderr.write(stderr.decode("utf-8"))


def execute(cmd):
    DEVNULL = open(os.devnull, "w")
    popen = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, universal_newlines=True, stderr=DEVNULL
    )
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)


def execute_timeout(cmd, timeout=120):
    # stream execute but add a timeout
    DEVNULL = open(os.devnull, "w")
    try:
        p = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, universal_newlines=True, stderr=DEVNULL
        )
        return_code = p.wait(timeout=timeout)
        if return_code:
            raise subprocess.CalledProcessError(return_code, cmd)
        else:
            for stdout_line in iter(p.stdout.readline, ""):
                yield stdout_line
            p.stdout.close()
    except subprocess.TimeoutExpired:
        # print(f"Timeout for {cmd} ({timeout}s) expired", file=sys.stderr)
        p.terminate()
        return ""


def check_inputs(inputs):
    for filename in inputs:
        if not is_file(filename):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filename)


def is_file(f):
    if os.path.isfile(f):
        return True
    else:
        return False


def which2(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None


def open_pipe(command, mode="r", buff=1024 * 1024):
    import subprocess
    import signal

    if "r" in mode:
        return subprocess.Popen(
            command,
            shell=True,
            bufsize=buff,
            stdout=subprocess.PIPE,
            universal_newlines=True,
            preexec_fn=lambda: signal.signal(signal.SIGPIPE, signal.SIG_DFL),
        ).stdout
    elif "w" in mode:
        return subprocess.Popen(
            command,
            shell=True,
            bufsize=buff,
            universal_newlines=True,
            stdin=subprocess.PIPE,
        ).stdin
    return None


NORMAL = 0
PROCESS = 1
PARALLEL = 2

WHICH_BZIP2 = which2("bzip2")
WHICH_PBZIP2 = which2("pbzip2")


def open_bz2(filename, mode="r", buff=1024 * 1024, external=PARALLEL):
    if external is None or external == NORMAL:
        import bz2

        return bz2.BZ2File(filename, mode, buff)
    elif external == PROCESS:
        if not WHICH_BZIP2:
            return open_bz2(filename, mode, buff, NORMAL)
        if "r" in mode:
            return open_pipe("bzip2 -dc " + filename, mode, buff)
        elif "w" in mode:
            return open_pipe("bzip2 >" + filename, mode, buff)
    elif external == PARALLEL:
        if not WHICH_PBZIP2:
            return open_bz2(filename, mode, buff, PROCESS)
        if "r" in mode:
            return open_pipe("pbzip2 -dc " + filename, mode, buff)
        elif "w" in mode:
            return open_pipe("pbzip2 >" + filename, mode, buff)
    return None


WHICH_GZIP = which2("gzip")
WHICH_PIGZ = which2("pigz")


def open_gz(filename, mode="r", buff=1024 * 1024, external=PARALLEL):
    if external is None or external == NORMAL:
        import gzip

        return gzip.GzipFile(filename, mode, buff)
    elif external == PROCESS:
        if not WHICH_GZIP:
            return open_gz(filename, mode, buff, NORMAL)
        if "r" in mode:
            return open_pipe("gzip -dc " + filename, mode, buff)
        elif "w" in mode:
            return open_pipe("gzip >" + filename, mode, buff)
    elif external == PARALLEL:
        if not WHICH_PIGZ:
            return open_gz(filename, mode, buff, PROCESS)
        if "r" in mode:
            return open_pipe("pigz -dc " + filename, mode, buff)
        elif "w" in mode:
            return open_pipe("pigz >" + filename, mode, buff)
    return None


WHICH_XZ = which2("xz")


def open_xz(filename, mode="r", buff=1024 * 1024, external=PARALLEL):
    if WHICH_XZ:
        if "r" in mode:
            return open_pipe("xz -dc " + filename, mode, buff)
        elif "w" in mode:
            return open_pipe("xz >" + filename, mode, buff)
    return None


def zopen(filename, mode="r", buff=1024 * 1024, external=PARALLEL):
    """
    Open pipe, zipped, or unzipped file automagically

    # external == 0: normal zip libraries
    # external == 1: (zcat, gzip) or (bzcat, bzip2)
    # external == 2: (pigz -dc, pigz) or (pbzip2 -dc, pbzip2)
    """
    if "r" in mode and "w" in mode:
        return None
    if filename.startswith("!"):
        return open_pipe(filename[1:], mode, buff)
    elif filename.endswith(".bz2"):
        return open_bz2(filename, mode, buff, external)
    elif filename.endswith(".gz"):
        return open_gz(filename, mode, buff, external)
    elif filename.endswith(".xz"):
        return open_xz(filename, mode, buff, external)
    else:
        return open(filename, mode, buff)
    return None
