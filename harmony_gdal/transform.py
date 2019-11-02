# CLI for adapting a Harmony operation to GDAL
#
# If you have harmony in a peer folder with this repo, then you can run the following for an example
#    python3 -m harmony_gdal --harmony-action invoke --harmony-input "$(cat ../harmony/example/service-operation.json)"

import sys
import subprocess
import os
import urllib.request
import urllib.parse
import re
import boto3

from harmony import BaseHarmonyAdapter

from osgeo import gdal

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

class HarmonyAdapter(BaseHarmonyAdapter):
    """
    See https://git.earthdata.nasa.gov/projects/HARMONY/repos/harmony-service-lib-py/browse
    for documentation and examples.
    """

    def invoke(self):
        """
        Run the service on the message contained in `self.message`.  Fetches data, runs the service,
        puts the result in a file, calls back to Harmony, and cleans up after itself.

        Note: This only operates on a single granule.  If multiple granules are requested, it
            subsets the first.  The subsetter is capable of combining multiple granules but will not
            do so until asynchronous requests are available and performance of data access has
            been established
        """
        logger = self.logger
        message = self.message

        try:
            # Limit to the first granule.  See note in method documentation
            granules = message.granules[:1]

            output_dir = "tmp/data"
            self.cmd('rm', '-rf', output_dir)
            self.cmd('mkdir', '-p', output_dir)

            self.download_granules(granules)

            layernames = []

            result = None
            for granule in granules:
                if not granule.variables:
                    granule.variables = self.get_variables(granule.local_filename)

                for variable in granule.variables:
                    layer_format = self.read_layer_format(
                        granule.collection,
                        granule.local_filename,
                        variable.name
                    )
                    layer_id = granule.id + '__' + variable.name
                    filename = layer_format.format(granule.local_filename)
                    filename = self.subset(
                        layer_id,
                        filename,
                        output_dir
                    )
                    filename = self.reproject(
                        layer_id,
                        filename,
                        output_dir
                    )
                    filename = self.resize(
                        layer_id,
                        filename,
                        output_dir
                    )
                    result = self.add_to_result(
                        layer_id,
                        filename,
                        output_dir
                    )
                    layernames.append(layer_id)

            ds = gdal.Open(result)
            for i in range(len(layernames)):
                ds.GetRasterBand(i + 1).SetDescription(layernames[i])
            ds = None

            result = self.reformat(result, output_dir)

            self.completed_with_local_file(result)

        except Exception as e:
            logger.exception(e)
            self.completed_with_error('An unexpected error occurred')

        finally:
            self.cleanup()


    def cmd(self, *args):
        self.logger.info(args[0] + " " + " ".join(["'{}'".format(arg) for arg in args[1:]]))
        result_str = subprocess.check_output(args).decode("utf-8")
        return result_str.split("\n")

    def subset(self, layerid, srcfile, dstdir):
        subset = self.message.subset
        if not subset:
            return srcfile

        command = ['gdal_translate', '-of', 'GTiff']
        if subset.bbox:
            bbox = [str(c) for c in subset.bbox]
            command.extend(["-projwin", bbox[0], bbox[3], bbox[2], bbox[1]])

        dstfile = "%s/%s" % (dstdir, layerid + '__subsetted.tif')
        command.extend([srcfile, dstfile])
        self.cmd(*command)
        return dstfile

    def reproject(self, layerid, srcfile, dstdir):
        crs = self.message.format.crs
        if not crs:
            return srcfile
        dstfile = "%s/%s" % (dstdir, layerid + '__reprojected.tif')
        self.cmd('gdalwarp',
            "-t_srs",
            crs,
            srcfile,
            dstfile)
        return dstfile


    def resize(self, layerid, srcfile, dstdir):
        command = ['gdal_translate']

        fmt = self.message.format

        dstfile = "%s/%s__resized.tif" % (dstdir, layerid)

        if fmt.width or fmt.height:
            width = fmt.width or 0
            height = fmt.height or 0
            command.extend(["-outsize", str(width), str(height)])

        command.extend([srcfile, dstfile])

        self.cmd(*command)
        return dstfile


    def add_to_result(self, layerid, srcfile, dstdir):
        tmpfile = "%s/tmp-result.tif" % (dstdir)
        dstfile = "%s/result.tif" % (dstdir)

        command = ['gdal_merge.py',
                '-o', tmpfile,
                '-of', "GTiff",
                '-separate']
        command.extend(mime_to_options["image/tiff"])

        if not os.path.exists(dstfile):
            self.cmd('cp', srcfile, dstfile)
            return dstfile

        command.extend([dstfile, srcfile])

        self.cmd(*command)
        self.cmd('mv', tmpfile, dstfile)

        return dstfile


    def reformat(self, srcfile, dstdir):
        output_mime = self.message.format.mime
        if output_mime not in mime_to_gdal:
            raise Exception('Unrecognized output format: ' + output_mime)
        if output_mime == "image/tiff":
            return srcfile

        dstfile = "%s/translated.%s" % (dstdir, mime_to_extension[output_mime])

        command = ['gdal_translate',
                '-of', mime_to_gdal[output_mime],
                '-scale',
                srcfile, dstfile]
        self.cmd(*command)

        return dstfile

    def read_layer_format(self, collection, filename, layer_id):
        gdalinfo_lines = self.cmd("gdalinfo", filename)
        layer_line = next(
            filter((lambda line: line.endswith(":" + layer_id)), gdalinfo_lines), None)
        if layer_line == None:
            print('Invalid Layer:', layer_id)

        layer = layer_line.split("=")[-1]
        return layer.replace(filename, "{}")

    def get_variables(self, filename):
        gdalinfo_lines = self.cmd("gdalinfo", filename)
        result = []
        for subdataset in filter((lambda line: re.match(r"^\s*SUBDATASET_\d+_NAME=", line)), gdalinfo_lines):
            result.append({ "name": re.split(r":", subdataset)[-1] })
        print(result)
        return result