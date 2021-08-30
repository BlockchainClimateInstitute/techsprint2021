# Stop the running container
docker stop techsprint2021
docker rm techsprint2021

# Rebuild image completely (--no-cache)
#docker build --no-cache --tag techsprint2021_image:latest .
docker build --tag techsprint2021_image:latest .

# Run image
# docker run -d --name techsprint2021 -p 5000:5000 --rm -v /"$PWD":/$HOME/app/ -w /$HOME/app/ techsprint2021_image:latest
docker run -d --name techsprint2021 -p 5000:5000 techsprint2021_image:latest