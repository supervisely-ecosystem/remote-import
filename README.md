<div align="center" markdown>

<img src="https://user-images.githubusercontent.com/48245050/182372844-1b874c60-530f-4b24-9e98-4875648b1e0e.png"/>

# Remote Import

<p align="center">

  <a href="#Overview">Overview</a> •
  <a href="#Preparation">Preparation</a> •
  <a href="#How-To-Run">How To Run</a> •
  <a href="#How-To-Use">How To Use</a>
</p>

[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervise.ly/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/remote-import)
[![views](https://app.supervise.ly/img/badges/views/supervisely-ecosystem/remote-import.png)](https://supervise.ly)
[![runs](https://app.supervise.ly/img/badges/runs/supervisely-ecosystem/remote-import.png)](https://supervise.ly)

</div>

## Overview

Connect your remote data storage to Supervisely Platform without data duplication.   

**NOTE #1:** most frequest usecase is when Enterprise Customer would like to connect huge existing data storage (tens of terabytes) and avoid data duplication. In other cases we recommend to use general import procedure to store data in Supervisely Data Storage.  

**NOTE #2:** this release works only with data structured in Supervisely format. In future versions raw images, videos, and other formats will be added. 

<img src="https://i.imgur.com/AmnUCBV.png"/>


## Preparation

0. Be sure that docker is installed on the server.
1. Go to your server and `cd` to directory with the data you want to connect. For example: `cd work/data`. We recommend to avoid using special characters in paths (spaces, etc...).
2. Run NGINX to to serve static files (images and annotation) by executing the following command: 

`docker run -p 8088:80 -v $(pwd):/mnt/data jetbrainsinfra/nginx-file-listing:0.2`

3. ⚠️ By default your new nginx web server is available for outside world. If needed, change `nginx.conf` to disallow it.

Now you can check that data is accesible in browser:

<img src="https://media4.giphy.com/media/tgVlRYEBJKsGbZfZnM/giphy.gif"/>

## How To Run 
**Step 1**: Add app to your team from Ecosystem if it is not there.

**Step 2**: Go to `Plugins & Apps` section in current team. And press `Run` button in front of application.

**Step 3**: You will be redirected to `Current Workspace`->`Tasks` page. Wait until app is started and press `Open` button. 

**Note**: Running procedure is simialr for almost all apps that are started from context menu. Example steps with screenshots are [here in how-to-run section](https://github.com/supervisely-ecosystem/merge-classes#how-to-run). 


## How to use

1. Put address to the remote directory with project in Supervisely format (where `meta.json` is). And press `Preview remote`.

2. List of all files and directories will be shown. Every directory is dataset (because this release supports only supervisely format) with two folders `img` and `ann`. Select what datasets will be uploaded.

3. Define destination project. Workspace will be created if not exist. If project already exists then error appears. Just change project name.

4. Press `Start upload` button. 

5. Link to created project and progress bars are available in output section. 

6. App shuts down automatically on finish. Or you can stop it manually from app settings page.
