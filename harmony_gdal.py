# CLI for adapting a Harmony operation to GDAL
#
# If you have harmony peered with this repo, then you can run the following for an example
#    python3 harmony_gdal.py invoke "$(cat ../harmony/example/service-operation.json)"

import sys
import argparse
import json
import subprocess
import os
import urllib.request
import urllib.parse
import boto3
import hashlib
import traceback

from http.cookiejar import CookieJar

from osgeo import gdal
from pprint import pprint

config = None
with open('config.json') as json_file:
  config = json.load(json_file)


s3 = None
if config['s3']['use_localstack']:
  s3 = boto3.client('s3',
                    endpoint_url="http://host.docker.internal:4572",
                    use_ssl=False,
                    aws_access_key_id="ACCESS_KEY",
                    aws_secret_access_key="SECRET_KEY",
                    region_name=config['s3']['region'])
else:
  s3 = boto3.client('s3', region_name=config['s3']['region'])

def setup_networking():
  creds = config['earthdata_login']
  baseurl = creds['endpoint']

  manager = urllib.request.HTTPPasswordMgrWithDefaultRealm()
  manager.add_password(None, baseurl, creds['username'], creds['password'])
  auth = urllib.request.HTTPBasicAuthHandler(manager)

  jar = CookieJar()
  processor = urllib.request.HTTPCookieProcessor(jar)
  opener = urllib.request.build_opener(auth, processor)
  urllib.request.install_opener(opener)

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

def download(url, dstdir):
  filename = os.path.basename(url)
  dstfile = "%s/%s" % (dstdir, filename)

  # Allow faster local testing by referencing files directly
  if not url.startswith("http") and not url.startswith("s3"):
    return url

  # Don't overwrite, as this can be called many times for a granule
  # Long-term a this has some theoretical problems with name clashes
  if os.path.exists(dstfile):
    return dstfile

  if url.startswith('s3'):
    try:
      bucket = url.split('/')[2]
      key = '/'.join(url.split('/')[3:])
      s3.download_file(bucket, key, dstfile)
      return dstfile
    except Exception as e:
      print("Error:", e.reason, url)
      traceback.print_exc()
      exit(1)

  # Open the url
  try:
    f = urllib.request.urlopen(url)
    print("Downloading", url)

    with open(dstfile, "wb") as local_file:
      local_file.write(f.read())

  except urllib.request.HTTPError as e:
    print("HTTP Error:", e.code, url)
    exit(1)
  except urllib.request.URLError as e:
    print("URL Error:", e.reason, url)
    exit(1)
  return dstfile


def subset(layerid, operation, srcfile, dstdir):
  subset = operation["subset"]
  if len(subset) == 0:
    return srcfile

  command = ['gdal_translate', '-of', 'GTiff'] #, '-projwin_srs', operation["format"]["crs"]]
  if "bbox" in subset:
    bbox = [str(c) for c in subset["bbox"]]
    command.extend(["-projwin", bbox[0], bbox[3], bbox[2], bbox[1]])

  dstfile = "%s/%s" % (dstdir, layerid + '__subsetted.tif')
  command.extend([srcfile, dstfile])
  cmd(*command)
  return dstfile

def reproject(layerid, operation, srcfile, dstdir):
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

def stage(operation, local_filename, bucket, key):
  print("Uploading file:", local_filename, "to", "s3://%s/%s" % (bucket, key))

  content_type = operation["format"]["mime"]
  s3.upload_file(local_filename, bucket, key, ExtraArgs={'ContentType': content_type})
  url = s3.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': key})

  if config["s3"]["use_localstack"]:
    url = url.replace("host.docker.internal", "localhost")

  return url

def read_layer_format(collection, filename, layer_id):
  gdalinfo_lines = cmd("gdalinfo", filename)
  layer_line = next(filter((lambda line: line.endswith(":" + layer_id)), gdalinfo_lines), None)
  if layer_line == None:
    print('Invalid Layer:', layer_id)

  layer = layer_line.split("=")[-1]
  return layer.replace(filename, "{}")

def post_file(url, filename, mime):
  headers = {
    'Content-Type': mime,
    'Content-Length': os.stat(filename).st_size,
  }
  print(headers)
  request = urllib.request.Request(url, open(filename, 'rb'),
                          headers=headers)
  return urllib.request.urlopen(request)

def invoke(operation_json):
  operation = json.loads(operation_json)

  try:
    output_dir = "tmp/data"
    cmd('rm', '-rf', output_dir)
    cmd('mkdir', '-p', output_dir)

    layernames = []

    for source in operation['sources']:
      collection = source['collection']
      for variable in source['variables']:
        layer_format = None
        result = None
        for granule in source['granules']:
          filename = download(granule['url'], output_dir)
          layer_format = layer_format or read_layer_format(collection, filename, variable['name'])
          layer_id = granule['id'] + '__' + variable['name']
          filename = layer_format.format(filename)
          filename = subset(layer_id, operation, filename, output_dir)
          filename = reproject(layer_id, operation, filename, output_dir)
          filename = resize(layer_id, operation, filename, output_dir)
          result = add_to_result(layer_id, operation, filename, output_dir)
          layernames.append("%s__%s" % (granule['name'], variable['name']))

          # Currently limit to the first granule so it runs faster and doesn't annoy the DAACs
          break

    ds = gdal.Open(result)
    for i in range(len(layernames)):
      ds.GetRasterBand(i + 1).SetDescription(layernames[i])
    ds = None

    result = reformat(operation, result, output_dir)

    base, ext = os.path.splitext(result)
    shasum = hashlib.sha256(operation_json.encode("utf-8")).hexdigest()
    bucket = config["s3"]["staging_bucket"]
    key = "%s/%s%s" % (config["s3"]["staging_path"], shasum, ext)
    staged = stage(operation, result, bucket, key)

    #response = post_file(operation['callback'] + '/response', result, operation["format"]["mime"])
    response = operation['callback'] + "/response?redirect=%s" % (urllib.parse.quote(staged))
    print("Executing callback", response)
    request = urllib.request.Request(response, method="POST")
    print('Remote response:', urllib.request.urlopen(request).read().decode('utf-8'))
    print('Complete')
  except Exception as e:
    traceback.print_exc()
    errorResponse = urllib.parse.quote("Unable to complete request")
    response = operation['callback'] + "/response?error=%s" % (errorResponse)
    print("Executing callback", response)
    request = urllib.request.Request(response, method="POST")
    print('Remote response:', urllib.request.urlopen(request).read().decode('utf-8'))
    print('Complete')
    sys.exit(1)



def run_invoke(args):
  try:
    invoke(args.input)
  except ValueError:
    print('Invalid JSON was provided to the service invocation')
    sys.exit(1)

def main():
  parser = argparse.ArgumentParser(description = 'Run gdal from a Harmony operation.')
  subparsers = parser.add_subparsers()

  invoke_parser = subparsers.add_parser('invoke', help = 'invoke a harmony command')
  invoke_parser.add_argument('input', help = 'a JSON object containing the invocation input')
  invoke_parser.set_defaults(func=run_invoke)

  args = parser.parse_args()

  setup_networking()
  args.func(args)

if __name__ == '__main__':
    main()