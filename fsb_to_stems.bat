%~dp0\vgmstream\test.exe -i -o temp.wav %1
%~dp0\sox\sox.exe temp.wav %1_stem0.wav remix -m 1 2
%~dp0\sox\sox.exe temp.wav %1_stem1.wav remix -m 3 4
%~dp0\sox\sox.exe temp.wav %1_stem2.wav remix -m 5 6
del temp.wav