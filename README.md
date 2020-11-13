# remote-import

https://i.imgur.com/2Frrx7i.png

## Prepare access to your data

cd to the directory with data
`cd to folder`

and then 

`docker run -p 8088:80 -v $(pwd):/mnt/data jetbrainsinfra/nginx-file-listing:0.2`

then go to page in your browser and check that files can be viewed or downloaded 

`http://localhost:8088/`

## How to use
- avoid using special characters in name, replace spaces with `_` or `-`
- existing datasets will be skipped. 
- app will be stopped automatically at the end
- app stops on error
- import images will be added later

## How to keep data private
