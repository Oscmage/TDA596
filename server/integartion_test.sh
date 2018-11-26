#!/usr/bin/env bash

curl -d 'entry=t'1 -X 'POST' 'http://10.1.0.1:80/board' &
curl -d 'entry=t'2 -X 'POST' 'http://10.1.0.2:80/board' &
curl -d 'entry=t'3 -X 'POST' 'http://10.1.0.3:80/board' &
curl -d 'entry=t'4 -X 'POST' 'http://10.1.0.4:80/board' &
done