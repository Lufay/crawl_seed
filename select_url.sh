#!/usr/bin/env sh

sed -E 's#https?:##;s#/##g' url | while read line
do
	ping -c 10 -n $line
	echo
done


