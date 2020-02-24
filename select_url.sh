#!/usr/bin/env sh

logfile='ping.log'

: > $logfile

sed -E 's#https?:##;s#/##g' url | while read line
do
	ping -c 10 -n $line >> $logfile
	echo >> $logfile
done

awk '/statistics/{
	domain[NR] = $2
}
/transmitted/{
	loss_rate[NR-1] = $7
}
/round-trip/{
	split($4, delays, "/")
	avg[NR-2] = delays[2]
}
END {
	for(key in domain) {
		print key, domain[key], loss_rate[key], avg[key]
	}
}
' $logfile | sort -k4 -n
