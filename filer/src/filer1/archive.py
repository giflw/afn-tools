

MAGIC = "filer-archive-1:"
from threading import RLock
import bsdiff4
import gzip
import shutil
from afn.fileutils import File
from filer1 import bec
from afn.utils.concurrent import AtomicInteger

LITERAL = "\x01"
LITERAL_GZIP = "\x02"
DIFF = "\x03"
DIFF_GZIP = "\x04"

def compress_folder(folder, out, temp_dir):
    objects, bec_map = load_objects(folder)
    sort_commit_objects(objects, bec_map)
    make_archive(objects, out, temp_dir)


def load_objects(folder):
    objects = []
    for f in folder.list():
        objects.append((f.name, f))
    bec_map = {}
    for h, f in objects:
        bec_map[h] = bec.load(f.open("rb"))
    return objects, bec_map


def sort_commit_objects(objects, bec_map):
    objects.sort(key=lambda a: bec_map.get("current_name", ""))


def make_archive(objects, out, temp_dir):
    """
    Objects is a list of (hash, fileutils.File) tuples representing the objects
    to encode, in order.
    """
    # out.write(MAGIC)
    window = []
    current = AtomicInteger(0)
    in_lock = RLock()
    out_lock = RLock()
    # TODO: Spawn several processor threads
    in_total, out_total = _process(objects, window, current, in_lock, out_lock, temp_dir)
    print "Total space savings: %s%%" % int(100*(1.0 - (float(out_total) / float(in_total))))
    print "Input size: %sKB, output size: %sKB" % (in_total / 1000, out_total / 1000)


def _process(objects, window, current, in_lock, out_lock, temp_dir):
    in_total, out_total, processed = 0, 0, 0
    while True:
        with in_lock:
            position = current.get_and_add()
            if position >= len(objects):
                return in_total, out_total
            hash, object_file = objects[position]
            # Make a copy /before/ appending to ourselves so as not to
            # accidentally diff against ourselves
            window_copy = list(window)
            window.append((hash, object_file))
            if len(window) > 10:
                del window[0]
        o_dir = temp_dir.child(hash)
        o_dir.mkdirs()
        try:
            # First, generate diffs and gzipped diffs
            for h, f in window_copy:
                p = o_dir.child(h)
                # Generate diff
                bsdiff4.file_diff(f.path, object_file.path, p.path)
                # Generate gzipped diff
#                g = o_dir.child(h + ".gz")
#                with open(p.path, "rb") as in_patch:
#                    with gzip.GzipFile(filename=g.path, mode="wb") as out_patch:
#                        shutil.copyfileobj(in_patch, out_patch)
            # Then gzip the original
            with object_file.open("rb") as in_file:
                with gzip.GzipFile(filename=o_dir.child("original.gz").path, mode="wb") as out_file:
                    shutil.copyfileobj(in_file, out_file)
            # And compare the files.
            # Gather the files to compare
            to_compare = []
            for h, f in window_copy:
                p = o_dir.child(h)
                to_compare.append((p.size, DIFF, p))
#                g = o_dir.child(h + ".gz")
#                to_compare.append((g.size, DIFF_GZIP, g))
            to_compare.append((object_file.size, LITERAL, object_file))
            object_file_g = o_dir.child("original.gz")
            to_compare.append((object_file_g.size, LITERAL_GZIP, object_file_g))
            # Compare them
            min_size, min_type, min_file = min(to_compare)
            # Print a message about how much we compressed
            original_size = object_file.size
            fraction_of_original = float(min_size) / float(original_size)
            amount_saved = 1.0 - fraction_of_original
            print "For object %s:" % hash
            print "original_size, min_size, min_type, min_file: %s, %s, %s, %s" % (
                    original_size, min_size, hex(ord(min_type)), min_file)
            print "Compressed to %s%% smaller (larger numbers are better)" % (
                    int(amount_saved * 100))
            in_total += original_size
            out_total += min_size
            processed += 1
            print "Processed %s" % processed
            print "Space savings so far: %s%%" % int(100*(1.0 - (float(out_total) / float(in_total))))
        finally:
            o_dir.delete_folder(True)

















