# Docker Regions dashboard
Italy regions docker image for [Covid-Dashboard](https://github.com/alex27riva/Covid-dashboard) thesis project.

## Building
`docker build -t dash_regioni:latest .`

## Run
`docker run --restart=always --name dashboard_regioni -d -p 8052:8050 dash_regioni`