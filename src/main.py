import os
import psutil
import socket

import gi
gi.require_version("Gst", "1.0")
gi.require_version("GstRtspServer", "1.0")

from gi.repository import GLib, Gst, GstRtspServer

# Get params from environment
HOST_ENV_VAR="RTSP_HOST"
PORT_ENV_VAR="RTSP_PORT"
URI_ENV_VAR="RTSP_URI"
USERNAME_ENV_VAR="RTSP_USERNAME"
PASSWORD_ENV_VAR="RTSP_PASSWORD"

# globals from environment variables
server_ip = socket.gethostbyname(os.environ.get(HOST_ENV_VAR))
server_port = os.environ.get(PORT_ENV_VAR)
uri = os.environ.get(URI_ENV_VAR)

print(f"Environment: server_ip {server_ip}, server_port {server_port}, uri {uri}")

# Globals for client connections (assumes single connection)
client_ip = ""
client_port = 0

class CustomRTSPMediaFactory(GstRtspServer.RTSPMediaFactory):
    def __init__(self, pipeline):
        GstRtspServer.RTSPMediaFactory.__init__(self)
        self.pipeline = pipeline
    
    def do_create_element(self, url):
        # ugly hack to get client ip and port 

        global client_ip, client_port
        
        current_process_id = os.getpid()
        try:
            process = psutil.Process(current_process_id)
            connections = process.connections(kind="tcp")
            for conn in connections:
                if (conn.status == psutil.CONN_ESTABLISHED) and (conn.raddr.ip == client_ip):
                    client_port = conn.raddr.port
        except psutil.NoSuchProcess:
            print(f"No process with PID {current_process_id} found")

        print(f"Client streaming: IP {client_ip}, Port {client_port}")
        
        return Gst.parse_launch(self.pipeline)

def on_client_connected(server, client):
    global client_ip, client_port
    connection = client.get_connection()
    client_ip = connection.get_ip()
    # XXX: calls to connection.get_url() trigger the following error on exit
    # (python:1): GLib-GIO-CRITICAL **: 00:06:32.644: g_inet_address_new_from_string: assertion 'string != NULL' failed
    # _, client_port = connection.get_url().get_port() # client_address.get_port()
    print(f"Client connected: IP {client_ip}")

# Initialize GStreamer
Gst.init(None)

# Create the RTSP server
server = GstRtspServer.RTSPServer.new()
server.attach(None)

# Pipeline description for CustomRTSPMediaFactory() that can handle any video file
# This pipeline description uses the filesrc element to read data from the specified video file, 
# and then uses the decodebin element to automatically detect and decode the video format. 
# The videoconvert element is used to convert the video to the I420 format, which is a common format for H.264 encoding. 
# The x264enc element is used to encode the video in H.264 format, and the rtph264pay element is used 
# to convert the H.264 video data into RTP packets for streaming over the network.

# This will create a CustomRTSPMediaFactory() instance that can handle any video file 
# by dynamically creating a GStreamer pipeline based on the video format.

video_file = "video.mp4"
pipeline_description = f"filesrc location={video_file} ! decodebin ! videoconvert ! video/x-raw,format=I420 ! x264enc ! rtph264pay pt=96 config-interval=1 name=pay0".format(video_file)

# ORIGINALS - ONLY WORK FOR SPECIFIC FILE FORMATS
# (CDLTLL) pipeline_description = "multifilesrc location=video.mp4 loop=true ! qtdemux ! queue ! rtph264pay pt=96 config-interval=1 name=pay0"
#pipeline_description = "multifilesrc location=video.mp4 loop=true ! qtdemux name=demux demux.video_0 ! h264parse ! rtph264pay config-interval=1 pt=96 ! udpsink host=127.0.0.1 port=8554"
#pipeline_description = "multifilesrc location=video.mp4 loop=true ! qtdemux ! decodebin ! videoconvert ! autovideosink"

#factory = GstRtspServer.RTSPMediaFactory.new()
#factory.set_launch(pipeline_description)

# Create a custom RTSP media factory
factory = CustomRTSPMediaFactory(pipeline_description)

# Add the media factory to the RTSP server
mounts = server.get_mount_points()
mounts.add_factory("/video", factory)

# Connect to the client-connected signal
server.connect("client-connected", on_client_connected)

# Run the main GStreamer event loop
GLib.MainLoop().run()