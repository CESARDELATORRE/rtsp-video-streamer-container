$rtsp_host="localhost"
$rtsp_port="8554"
$rtsp_uri="video"
$rtsp_name="rtsp-streamer"

$containterImage="ghcr.io/cesardelatorre/rtsp-streamer-container:0.5"

# sudo docker pull $containterImage

docker run -it --name rtsp-streamer -p 8554:8554 -e RTSP_HOST=localhost -e RTSP_PORT=8554 -e RTSP_URI=video ghcr.io/cesardelatorre/rtsp-streamer-container:0.5

