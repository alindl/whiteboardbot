#!/bin/bash
#@Synopsis Enhances a whiteboard picture through more contrast, improving legibility
#@Copyright 2021 University of Salzburg
#@License GNU GPL v3.0
#@Author Andreas Lindlbauer

trap 'rm -f $tmp1 $tmp1c $tmp2 $tmp2c $tmp0 $tmp0c $tmpR1 $tmpR2 $tmpG1 $tmpG2 $tmpB1 $tmpB2;' 0
trap 'rm -f $tmp1 $tmp1c $tmp2 $tmp2c $tmp0 $tmp0c $tmpR1 $tmpR2 $tmpG1 $tmpG2 $tmpB1 $tmpB2; exit 1' 1 2 3 15

infile="$1"
tmp0="/tmp/tmpA.mpc" #A
tmp0c="/tmp/tmpA.cache" #A
tmp1="/tmp/tmpT.mpc" #T
tmp1c="/tmp/tmpT.cache" #T
tmp2="/tmp/tmpM.mpc" #M
tmp2c="/tmp/tmpM.cache" #M
outfile="$2"

convert -quiet "$infile" +repage "$tmp0"

getAverage()
	{
    mean=$(convert "$infile" -format "%[mean]" info:)
    mean=$(convert xc: -format "%[fx:100*$mean/quantumrange]" info:)
    ave=$(convert xc: -format "%[fx:100*$mean/$maskmean]" info:)
	[ "$ave" = "0" ] || [ "$ave" = "0.0" ] && ave=100
    ratio=$(convert xc: -format "%[fx:100/$ave]" info:)
	}

convert $tmp0 -contrast-stretch 0 $tmp0

tmpR1="/tmp/autowhite_R.mpc"
tmpR2="/tmp/autowhite_R.cache"
tmpG1="/tmp/autowhite_G.mpc"
tmpG2="/tmp/autowhite_G.cache"
tmpB1="/tmp/autowhite_B.mpc"
tmpB2="/tmp/autowhite_B.cache"

convert $tmp0 -channel R -separate $tmpR1
convert $tmp0 -channel G -separate $tmpG1
convert $tmp0 -channel B -separate $tmpB1
convert $tmp0 -colorspace HSB -channel G -negate -channel GB -separate \
    -compose multiply -composite +channel \
    -contrast-stretch 0,0.01% -fill black +opaque white \
    $tmp2
mean=$(convert "$infile" -format "%[mean]" info:)
mean=$(convert xc: -format "%[fx:100*$mean/quantumrange]" info:)
maskmean=$mean
convert $tmpR1 $tmp2 -compose multiply -composite $tmp1
getAverage "$tmp1"
redratio=$ratio
convert $tmpG1 $tmp2 -compose multiply -composite $tmp1
getAverage "$tmp1"
greenratio=$ratio
convert $tmpB1 $tmp2 -compose multiply -composite $tmp1
getAverage "$tmp1"
blueratio=$ratio
convert $tmp0 -color-matrix "$redratio 0 0 0 $greenratio 0 0 0 $blueratio" $tmp0

w=$(convert -ping $tmp0 -format "%w" info:)
h=$(convert -ping $tmp0 -format "%h" info:)

width=$(convert xc: -format "%[fx:2*$w]" info:)
height=$(convert xc: -format "%[fx:2*$h]" info:)

delx=$(convert xc: -format "%[fx:($w-$width)/2]" info:)
dely=$(convert xc: -format "%[fx:($h-$height)/2]" info:)

convert \( $tmp0 -virtual-pixel white -set option:distort:viewport "${width}"x"${height}""${delx}""${dely}" -distort SRT "2 0" \) \
		\( -clone 0 -colorspace gray -negate -lat 25x25+3% -contrast-stretch 0 -blur 1x65535 -level 60x100% \) \
		-compose copy_opacity -composite -fill "white" -opaque none -alpha off \
		-modulate 100,200 \
		"$outfile"
