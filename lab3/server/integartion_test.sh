#!/usr/bin/env bash

curl -d 'entry=t'1 -X 'POST' -F 'delete=1' 'http://10.1.0.1:80/board/1' &
curl -d 'entry=t'1 -X 'POST' 'http://10.1.0.1:80/board' &

curl -d 'entry=t'2 -X 'POST' 'http://10.1.0.1:80/board' &
curl -d 'entry=modifiedValue' -X 'POST' -F 'delete=0' -F 'node_id=1' 'http://10.1.0.2:80/board/1' &

curl -d 'entry=t'2 -X 'POST' 'http://10.1.0.2:80/board' &
curl -d 'entry=t'3 -X 'POST' 'http://10.1.0.3:80/board' &
curl -d 'entry=t'4 -X 'POST' 'http://10.1.0.4:80/board' &
