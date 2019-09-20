# CLI for adapting a Harmony operation to GDAL
#
# If you have harmony peered with this repo, then you can run the following for an example
#    python3 harmony_gdal.py invoke "$(cat ../harmony/example/service-operation.json)"

import sys
import subprocess
import os
import urllib.request
import urllib.parse
import re
import boto3

from osgeo import gdal

from harmony_gdal.util.data_transfer import download, stage

mime_to_gdal = {
    "image/tiff": "GTiff",
    "image/png": "GIF",
    "image/gif": "PNG"
}

mime_to_extension = {
    "image/tiff": "tif",
    "image/png": "png",
    "image/gif": "gif"
}

mime_to_options = {
    "image/tiff": ["-co", "COMPRESS=LZW"]
}


def cmd(*args):
    print(args[0], *["'{}'".format(arg) for arg in args[1:]])
    result_str = subprocess.check_output(args).decode("utf-8")
    return result_str.split("\n")

def subset(layerid, operation, srcfile, dstdir):
    subset = operation["subset"]
    if len(subset) == 0:
        return srcfile

    # , '-projwin_srs', operation["format"]["crs"]]
    command = ['gdal_translate', '-of', 'GTiff']
    if "bbox" in subset:
        bbox = [str(c) for c in subset["bbox"]]
        command.extend(["-projwin", bbox[0], bbox[3], bbox[2], bbox[1]])

    dstfile = "%s/%s" % (dstdir, layerid + '__subsetted.tif')
    command.extend([srcfile, dstfile])
    cmd(*command)
    return dstfile


def reproject(layerid, operation, srcfile, dstdir):
    if "crs" not in operation["format"]:
        return srcfile
    dstfile = "%s/%s" % (dstdir, layerid + '__reprojected.tif')
    cmd('gdalwarp',
        "-t_srs",
        operation["format"]["crs"],
        srcfile,
        dstfile)
    return dstfile


def resize(layerid, operation, srcfile, dstdir):
    command = ['gdal_translate']

    fmt = operation["format"]

    dstfile = "%s/%s__resized.tif" % (dstdir, layerid)

    if "width" in fmt or "height" in fmt:
        width = fmt["width"] or 0
        height = fmt["height"] or 0
        command.extend(["-outsize", str(width), str(height)])

    command.extend([srcfile, dstfile])

    cmd(*command)
    return dstfile


def add_to_result(layerid, operation, srcfile, dstdir):
    tmpfile = "%s/tmp-result.tif" % (dstdir)
    dstfile = "%s/result.tif" % (dstdir)

    command = ['gdal_merge.py',
               '-o', tmpfile,
               '-of', "GTiff",
               '-separate']
    command.extend(mime_to_options["image/tiff"])

    if not os.path.exists(dstfile):
        cmd('cp', srcfile, dstfile)
        return dstfile

    command.extend([dstfile, srcfile])

    cmd(*command)
    cmd('mv', tmpfile, dstfile)

    return dstfile


def reformat(operation, srcfile, dstdir):
    output_mime = operation["format"]["mime"]
    if output_mime not in mime_to_gdal:
        raise Exception('Unrecognized output format: ' + output_mime)
    if output_mime == "image/tiff":
        return srcfile

    dstfile = "%s/translated.%s" % (dstdir, mime_to_extension[output_mime])

    command = ['gdal_translate',
               '-of', mime_to_gdal[output_mime],
               '-scale',
               srcfile, dstfile]
    cmd(*command)

    return dstfile

def read_layer_format(collection, filename, layer_id):
    gdalinfo_lines = cmd("gdalinfo", filename)
    layer_line = next(
        filter((lambda line: line.endswith(":" + layer_id)), gdalinfo_lines), None)
    if layer_line == None:
        print('Invalid Layer:', layer_id)

    layer = layer_line.split("=")[-1]
    return layer.replace(filename, "{}")

def get_variables(filename):
    gdalinfo_lines = cmd("gdalinfo", filename)
    result = []
    for subdataset in filter((lambda line: re.match(r"^\s*SUBDATASET_\d+_NAME=", line)), gdalinfo_lines):
        result.append({ "name": re.split(r":", subdataset)[-1] })
    print(result)
    return result

def post_file(url, filename, mime):
    headers = {
        'Content-Type': mime,
        'Content-Length': os.stat(filename).st_size,
    }
    print(headers)
    request = urllib.request.Request(url, open(filename, 'rb'),
                                     headers=headers)
    return urllib.request.urlopen(request)


def callback_do_post(input, path):
    """
    POSTs to the Harmony callback URL at the given path, which may include query params

    Parameters
    ----------
    input : object
        The Harmony input object.  See example/harmony-operation.json for the shape
    path : string
        The URL path relative to the Harmony callback URL which should be POSTed to

    Returns
    -------
    None
    """

    url = input['callback'] + path
    print('Starting response', url)
    request = urllib.request.Request(url, method='POST')
    print('Remote response:', urllib.request.urlopen(
        request).read().decode('utf-8'))
    print('Completed response', url)


def callback_with_redirect(input, redirect_url):
    """
    Performs a callback instructing Harmony to redirect the service user to the given URL

    Parameters
    ----------
    input : object
        The Harmony input object.  See example/harmony-operation.json for the shape
    redirect_url : string
        The URL where the service user should be redirected

    Returns
    -------
    None
    """
    callback_do_post(input, '/response?redirect=%s' %
                     (urllib.parse.quote(redirect_url)))


def callback_with_error(input, message):
    """
    Performs a callback instructing Harmony that there has been an error and providing a
    message to send back to the service user

    Parameters
    ----------
    input : object
        The Harmony input object.  See example/harmony-operation.json for the shape
    message : string
        The error message to pass on to the service user

    Returns
    -------
    None
    """
    print("DELETE ME! ", message)
    return
    callback_do_post(input, '/response?error=%s' %
                     (urllib.parse.quote(message)))


def invoke(operation, output_name):
    """
    Invokes the service for the given input, calling back to Harmony as appropriate

    Parameters
    ----------
    input : object
        The Harmony input object.  See example/harmony-operation.json for the shape
    output_name : string
        A unique name corresponding to the input, currently used to identify the output file.
        Note: In the future this may be used to avoid performing the same service
            multiple times.  Doing so requires stripping off unique identifiers such as
            the callback URL before hashing.

    Returns
    -------
    None
    """

    try:
        output_dir = "tmp/data"
        cmd('rm', '-rf', output_dir)
        cmd('mkdir', '-p', output_dir)

        layernames = []

        result = None
        for source in operation['sources']:
            collection = source['collection']
            if 'variables' not in source or len(source['variables']) == 0:
                # Use all variables if none are specified
                download(source['granules'][0]['url'], output_dir)
                filename = download(source['granules'][0]['url'], output_dir)
                source['variables'] = get_variables(filename)

            for variable in source['variables']:
                layer_format = None
                result = None
                for granule in source['granules']:
                    filename = download(granule['url'], output_dir)
                    layer_format = layer_format or read_layer_format(
                        collection, filename, variable['name'])
                    layer_id = granule['id'] + '__' + variable['name']
                    filename = layer_format.format(filename)
                    filename = subset(layer_id, operation,
                                      filename, output_dir)
                    filename = reproject(
                        layer_id, operation, filename, output_dir)
                    filename = resize(layer_id, operation,
                                      filename, output_dir)
                    result = add_to_result(
                        layer_id, operation, filename, output_dir)
                    layernames.append(layer_id)

                    # Currently limit to the first granule so it runs faster and doesn't annoy the DAACs
                    break

        ds = gdal.Open(result)
        for i in range(len(layernames)):
            print(layernames[i])
            ds.GetRasterBand(i + 1).SetDescription(layernames[i])
        ds = None

        result = reformat(operation, result, output_dir)

        base, ext = os.path.splitext(result)
        staged = stage(result, output_name + ext, operation["format"]["mime"])

        callback_with_redirect(operation, staged)
    except Exception as e:
        raise
        callback_with_error(input, "Unable to complete request")

