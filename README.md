<div align="center" markdown>

<img src="https://i.imgur.com/2Frrx7i.png"/>

# Remote Import

<p align="center">

  <a href="#Overview">Overview</a> •
  <a href="#How-To-Run">How To Run</a> •
  <a href="#How-To-Use">How To Use</a>
</p>

[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervise.ly/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/remote-import)
[![views](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/remote-import&counter=views&label=views)](https://supervise.ly)
[![used by teams](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/remote-import&counter=downloads&label=used%20by%20teams)](https://supervise.ly)
[![runs](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/remote-import&counter=runs&label=runs&123)](https://supervise.ly)

</div>

## Overview

Application tags images in project. User can choose percentage of images that will be tagged as "train" or "val" and several additional options. Neural Networks will use these tags to split data into training/validation datasets. 

<img src="https://i.imgur.com/KA8kXBr.png"/>




# remote-import

## Prepare access to your data

cd to the directory with data
`cd to folder`

and then 

`docker run -p 8088:80 -v $(pwd):/mnt/data jetbrainsinfra/nginx-file-listing:0.2`

then go to page in your browser and check that files can be viewed or downloaded 

`http://localhost:8088/`

RECOMMENDED FOR ENTERPRISES

## How to use
- avoid using special characters in name, replace spaces with `_` or `-`
- existing datasets will be skipped. 
- app will be stopped automatically at the end
- app stops on error
- import images will be added later

## How to keep data private
