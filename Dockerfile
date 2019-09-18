FROM osgeo/gdal:ubuntu-full-latest

RUN ln -s /usr/bin/python3 /usr/bin/python && apt-get update && apt-get install -y python3-pip && pip3 install boto3

WORKDIR "/home"

# Bundle app source
COPY . .

ENTRYPOINT ["python3", "-m", "harmony_gdal.cli"]
