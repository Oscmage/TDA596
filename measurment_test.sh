#!/usr/bin/env bash

for i in `seq 1 20`; do
	curl -d 'entry=t'i -X 'POST' 'http://10.1.0.1:80/board' &
	curl -d 'entry=t'i -X 'POST' 'http://10.1.0.2:80/board' &
	curl -d 'entry=t'i -X 'POST' 'http://10.1.0.3:80/board' &
	curl -d 'entry=t'i -X 'POST' 'http://10.1.0.4:80/board' &
#	curl -d 'entry=t'i -X 'POST' 'http://10.1.0.5:80/board' &
#	curl -d 'entry=t'i -X 'POST' 'http://10.1.0.6:80/board' &
#	curl -d 'entry=t'i -X 'POST' 'http://10.1.0.7:80/board' &
#	curl -d 'entry=t'i -X 'POST' 'http://10.1.0.8:80/board' &
done
