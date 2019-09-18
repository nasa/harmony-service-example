"""
=========
data_transfer.py
=========

Functions for moving remote data (HTTPS and S3) to be operated on locally and for staging
data results for external access (S3 pre-signed URL).

This module relies (overly?) heavily on environment variables to know which endpoints to use
and how to authenticate to them as follows:

Required when reading from or staging to S3:
    AWS_DEFAULT_REGION: The AWS region in which the S3 client is operating

Required when staging to S3:
    STAGING_BUCKET: The bucket where staged files should be placed
    STAGING_PATH: The base path under which staged files should be placed

Recommended when using HTTPS, allowing Earthdata Login auth.  Prints a warning if not supplied:
    EDL_ENDPOINT: The endpoint to use for Earthdata Login, e.g. https://urs.earthdata.nasa.gov or https://uat.urs.earthdata.nasa.gov
    EDL_USERNAME: The username to be passed to Earthdata Login when challenged
    EDL_PASSWORD: The password to be passed to Earthdata Login when challenged

Optional when reading from or staging to S3:
    USE_LOCALSTACK: 'true' if the S3 client should connect to a LocalStack instance instead of Amazon S3 (for testing)
"""

import boto3

from http.cookiejar import CookieJar
from urllib import request
from os import environ, path

_s3 = None
_is_networking_setup = False

# Flag determining the use of LocalStack (for testing), which will influence how URLs are structured
# and how S3 is accessed
USE_LOCALSTACK = 'USE_LOCALSTACK' in environ and environ['USE_LOCALSTACK'] == 'true'


def _get_s3_client():
    """
    Returns a client for accessing S3.  Expects the environment variable "AWS_DEFAULT_REGION"
    to be set.  If the environment variable "USE_LOCALSTACK" is set to "true", it will return
    a client that will access a LocalStack S3 instance instead of AWS.

    Returns
    -------
    s3_client : boto3.S3.Client
        A client appropriate for accessing S3
    """
    if _s3 != None:
        return _s3
    region = environ.get('AWS_DEFAULT_REGION')
    if USE_LOCALSTACK:
        return boto3.client('s3',
                            endpoint_url='http://host.docker.internal:4572',
                            use_ssl=False,
                            aws_access_key_id='ACCESS_KEY',
                            aws_secret_access_key='SECRET_KEY',
                            region_name=region)
    else:
        return boto3.client('s3', region_name=region)


def _setup_networking():
    """
    Sets up HTTP(S) cookies and basic auth so that HTTP calls using urllib.request will
    use Earthdata Login (EDL) auth as appropriate.  Will allow Earthdata login auth only if
    the following environment variables are set and will print a warning if they are not:

    EDL_ENDPOINT: The endpoint to use for Earthdata Login, e.g. https://urs.earthdata.nasa.gov or https://uat.urs.earthdata.nasa.gov
    EDL_USERNAME: The username to be passed to Earthdata Login when challenged
    EDL_PASSWORD: The password to be passed to Earthdata Login when challenged

    Returns
    -------
    None
    """
    if _is_networking_setup:
        return
    try:
        manager = request.HTTPPasswordMgrWithDefaultRealm()
        manager.add_password(
            None, environ['EDL_ENDPOINT'], environ['EDL_USERNAME'], environ['EDL_PASSWORD'])
        auth = request.HTTPBasicAuthHandler(manager)

        jar = CookieJar()
        processor = request.HTTPCookieProcessor(jar)
        opener = request.build_opener(auth, processor)
        request.install_opener(opener)
    except KeyError:
        print('Warning: Earthdata Login must be set up for authenticated downloads.  Requests will be unauthenticated.')
    _is_networking_setup = True


def download(url, destination_dir):
    """
    Downloads the given URL to the given destination directory, using the basename of the URL
    as the filename in the destination directory.  Supports http://, https:// and s3:// schemes.
    When using the s3:// scheme, expects the "AWS_DEFAULT_REGION" environment variable to be set.
    When using http:// or https:// schemes, expects the following environment variables or will
    print a warning:

    EDL_ENDPOINT: The endpoint to use for Earthdata Login, e.g. https://urs.earthdata.nasa.gov or https://uat.urs.earthdata.nasa.gov
    EDL_USERNAME: The username to be passed to Earthdata Login when challenged
    EDL_PASSWORD: The password to be passed to Earthdata Login when challenged

    Parameters
    ----------
    url : stringß
        The URL to fetch
    destination_dir : string
        The directory in which to place the downloaded file

    Returns
    -------
    destination : string
      The filename, including directory, of the downloaded file
    """

    def download_from_s3(url, destination):
        bucket = url.split('/')[2]
        key = '/'.join(url.split('/')[3:])
        _get_s3_client().download_file(bucket, key, destination)
        return destination

    def download_from_http(url, destination):
        _setup_networking()
        # Open the url
        f = request.urlopen(url)
        print('Downloading', url)

        with open(destination, 'wb') as local_file:
            local_file.write(f.read())

        print('Completed', url)
        return destination

    destination = path.join(destination_dir, path.basename(url))

    # Allow faster local testing by referencing files directly
    if not url.startswith('http') and not url.startswith('s3'):
        return url

    # Don't overwrite, as this can be called many times for a granule
    # Long-term a this has some theoretical problems with name clashes
    if path.exists(destination):
        return destination

    if url.startswith('s3'):
        return download_from_s3(url, destination)

    return download_from_http(url, destination)


def stage(local_filename, remote_filename, mime):
    """
    Stages the given local filename, including directory path, to an S3 location with the given
    filename and mime-type, returning a pre-signed URL to the staged file

    Requires the following environment variables:
        AWS_DEFAULT_REGION: The AWS region in which the S3 client is operating
        STAGING_BUCKET: The bucket where staged files should be placed
        STAGING_PATH: The base path under which staged files should be placed


   Parameters
    ----------
    local_filename : string
        A path and filename to the local file that should be staged
    remote_filename : string
        The basename to give to the remote file
    mime : string
        The mime type to apply to the staged file for use when it is served, e.g. "application/x-netcdf4"

    Returns
    -------
    url : string
        A pre-signed S3 URL to the staged file
    """
    staging_bucket = environ['STAGING_BUCKET']
    staging_path = environ['STAGING_PATH']

    key = '%s/%s' % (staging_path, remote_filename)

    s3 = _get_s3_client()
    s3.upload_file(local_filename, staging_bucket, key,
                   ExtraArgs={'ContentType': mime})
    url = s3.generate_presigned_url(
        'get_object', Params={'Bucket': staging_bucket, 'Key': key})

    if USE_LOCALSTACK:
        url = url.replace('host.docker.internal', 'localhost')

    return url
