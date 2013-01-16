import os
import tempfile
import subprocess
import shutil
from celery import task
from django.conf import settings
from renamer.helpers.directoryinfo import alphanum_key

valid_extensions = [".pdf", ".zip", ".jpg", ".jpeg", ".tif", ".tiff", ".JPG", ".JPEG", ".TIF", ".TIFF", ".PDF", '.png', '.PNG']


@task(ignore_result=True)
def convert_to_diva(indir):
    outdir = settings.DIVA_LOCATION
    pgimg_path = os.path.join(indir, 'pageimg')
    ms_name = os.path.basename(indir)
    out_path = os.path.join(outdir, ms_name)

    if not os.path.exists(out_path):
        os.mkdir(out_path)

    f = open(os.path.join(out_path, ".diva_conversion_in_progress"), "w")
    f.close()

    images = [os.path.join(pgimg_path, f) for f in os.listdir(pgimg_path) if __filter_fnames(f)]
    images.sort(key=alphanum_key)
    tdir = tempfile.mkdtemp(dir=settings.TMPDIR)

    for image in images:
        tdir = None
        name = os.path.basename(image)
        name, ext = os.path.splitext(name)

        # some tiff files are corrupted, causing KDU to bail.
        # We'll take the safe route and convert all files, TIFF or not.
        subprocess.call([settings.PATH_TO_VIPS,
                            "im_copy",
                            image,
                            os.path.join(tdir, "{0}.tiff".format(name))])

        input_file = os.path.join(tdir, "{0}.tiff".format(name))
        output_file = os.path.join(out_path, "{0}.jp2".format(name))

        subprocess.call([settings.PATH_TO_KDU,
                            "-i", input_file,
                            "-o", output_file,
                            "-quiet",
                            "-num_threads", "1",
                            "Clevels=5",
                            "Creversible=yes",
                            "-rate", "-,1,0.5,0.25",
                        ])
    shutil.rmtree(tdir)
    os.remove(os.path.join(out_path, ".diva_conversion_in_progress"))

    return True


def __filter_fnames(fname):
    if fname.startswith('.'):
        return False
    if fname == "Thumbs.db":
        return False
    if os.path.splitext(fname)[-1].lower() not in valid_extensions:
        return False
    return True