$imageHost="ghcr.io"
$user="cesardelatorre"
$prefix="rtsp-streamer"
$tags="0.5"
$imageName="${imageHost}/${user}/${prefix}-container:${tags}"

docker build --tag=${imageName} --file=./Dockerfiles/rtsp .

docker push ${imageName}
