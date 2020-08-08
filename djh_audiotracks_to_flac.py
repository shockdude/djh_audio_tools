# DJH Audiotracks to FLAC v0.5
# Copyright (C) 2019 shockdude

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import os, sys
import subprocess
import shutil
import csv
import re
from mutagen.flac import FLAC

DJH1_SINGLE = "SinglePlayer"
DJH1_TRACK_FOLDER = "Medium"

DJH1_GUITAR = "TwoPlayer"
DJH1_GUITAR_FOLDER = "Guitar"
DJH1_SINGLE_FSB_NAME = "AudioTrack_Main.fsb"
DJH1_GUITAR_FSB_NAME = "AudioTrack_Main_P1.fsb"
DJH1_DJ_FSB_NAME = "AudioTrack_Main_P2.fsb"

DJH2_FSB_NAME = "DJ.fsb"

CSV_TAG_FILE = "djhero_tagging.csv"
# title;artist;composer;album;albumartist;track;year;
CSV_TITLE = 0
CSV_ARTIST = 1
CSV_COMPOSER = 2
CSV_ALBUM = 3
CSV_ALBUM_ARTIST = 4
CSV_TRACK = 5
CSV_DATE = 6

def extract_fsb_to_flac(fsb_path, out_name = None):
	# check if fsb is valid
	fsb_filename = os.path.basename(fsb_path)
	fsb_name, fsb_ext = os.path.splitext(fsb_filename)
	if fsb_ext.lower() != ".fsb":
		print("Error: {} is not a .fsb file.".format(fsb_filename))
		return None
		
	if out_name == None:
		out_name = fsb_name
		
	out_name = out_name + ".flac"

	try:
		vgm_out = subprocess.run(["vgmstream/test.exe", "-i", "-p", fsb_filename], capture_output = True)
		if vgm_out.returncode != 0:
			print("Error: Failed to extract {} with vgmstream".format(fsb_filename))
			exit(1)
			return None
		
		sox_out = subprocess.run(["sox/sox.exe", "-t", ".wav", "-", out_name, "-D",
								   "remix", "-m", "1,3,5", "2,4,6",
								   "rate", "-v", "44100"], input = vgm_out.stdout)
		if sox_out.returncode != 0:
			print("Error: Failed to mix vgmstream output with sox")
			exit(1)
			return None
	except FileNotFoundError:
		print("Error: Missing tools (vgmstream or sox)")
		exit(1)
	
	return out_name
	
def extract_fsb_to_raw_wav(fsb_path, out_name = None):
	# check if fsb is valid
	fsb_filename = os.path.basename(fsb_path)
	fsb_name, fsb_ext = os.path.splitext(fsb_filename)
	if fsb_ext.lower() != ".fsb":
		print("Error: {} is not a .fsb file.".format(fsb_filename))
		return None
		
	if out_name == None:
		out_name = fsb_name
		
	out_name = out_name + ".wav"
	
	# extract files from fsb with vgmstream
	try:
		vgm_out = subprocess.run(["vgmstream/test.exe", "-i", "-o", out_name, fsb_filename], stdout=subprocess.DEVNULL)
		if vgm_out.returncode != 0:
			print("Error: Failed to extract {} with vgmstream".format(fsb_filename))
			exit(1)
			return None
	except FileNotFoundError:
		print("Error: Missing tools (vgmstream)")
		exit(1)
	
	return out_name

def get_tags_from_csv(track_number):
	try:
		with open(CSV_TAG_FILE, "r", encoding='utf-8') as tag_file:
			tag_csv = csv.reader(tag_file, delimiter=";")
			for row in tag_csv:
				if row[CSV_TRACK] == track_number:
					return row
		print("Warning: Couldn't find tag for {} in tag file {}".format(track_number, CSV_TAG_FILE))
		return None
	except:
		print("Warning: Error with getting tags from {}, no tags written".format(CSV_TAG_FILE))
		return None

def write_tags(audio_file):
	audio_name, audio_ext = os.path.splitext(audio_file)
	
	if len(audio_name) >= 6 and audio_name[0:3] == "DJH":
		song_track = audio_name[3:]
	else:
		song_track = audio_name

	song_tags = get_tags_from_csv(song_track)
	if song_tags == None:
		return audio_file

	song_title = song_tags[CSV_TITLE]
	song_artist = song_tags[CSV_ARTIST]
	song_album_artist = song_tags[CSV_ALBUM_ARTIST]
	song_album = song_tags[CSV_ALBUM]
	song_composer = song_tags[CSV_COMPOSER]
	song_date = song_tags[CSV_DATE]
	song_comment = song_album + " Rip"
	
	# filter out illegal characters from filename
	tagged_file = re.sub(r'[\\/*?:"<>|]',"",song_track + " - " + song_title + audio_ext)
	
	# blindly assuming the input file is a FLAC
	flacfile = FLAC(audio_file)
	# delete existing tags, if any
	flacfile.delete()
	# add new tags
	flacfile.tags.append(("TITLE", song_title))
	flacfile.tags.append(("ARTIST", song_artist))
	flacfile.tags.append(("ALBUMARTIST", song_album_artist))
	flacfile.tags.append(("ALBUM", song_album))
	flacfile.tags.append(("COMPOSER", song_composer))
	flacfile.tags.append(("DATE", song_date))
	flacfile.tags.append(("TRACKNUMBER", song_track))
	flacfile.tags.append(("COMMENT", song_comment))
	flacfile.save()
	
	os.rename(audio_file, tagged_file)
	return tagged_file
	
def extract_fsb_to_working_folder(working_folder, fsb_name, track_id = None, raw_wav = False):
	current_path = os.path.abspath(".")

	if not os.path.isfile(fsb_name):
		print("Error: could not find FSB {}".format(fsb_name))
		return	
	
	shutil.copy(fsb_name, working_folder)
	os.chdir(working_folder)
	if raw_wav:
		fsb_outfile = extract_fsb_to_raw_wav(fsb_name, track_id)
	else:
		fsb_outfile = extract_fsb_to_flac(fsb_name, track_id)
	os.remove(fsb_name)
	
	if fsb_outfile == None:
		print("Error extracting FSB")
		os.chdir(current_path)
		return None

	os.chdir(current_path)
	return fsb_outfile

def extract_djh1_single(track_id, working_folder):
	current_path = os.path.abspath(".")
	
	if not os.path.isdir(DJH1_TRACK_FOLDER):
		print("Error: could not find track folder \"{}\" for song {}".format(DJH1_TRACK_FOLDER, track_id))
		return
	
	os.chdir(DJH1_TRACK_FOLDER)
	fsb_outfile = extract_fsb_to_working_folder(working_folder, DJH1_SINGLE_FSB_NAME, track_id)
	if fsb_outfile == None:
		os.chdir(current_path)
		return None

	os.chdir(working_folder)
	mix_out = write_tags(fsb_outfile)
	os.chdir(current_path)
	return mix_out
	
def extract_djh1_guitar(track_id, working_folder):
	current_path = os.path.abspath(".")

	if not os.path.isdir(DJH1_GUITAR_FOLDER):
		print("Error: could not find guitar folder \"{}\" for song {}".format(DJH1_GUITAR_FOLDER, track_id))
		return
	
	os.chdir(DJH1_GUITAR_FOLDER)
	fsb_outfile = extract_fsb_to_working_folder(working_folder, DJH1_GUITAR_FSB_NAME, track_id, raw_wav = True)
	if fsb_outfile == None:
		os.chdir(current_path)
		return None
	
	os.chdir(working_folder)
	g_name = "g_" + fsb_outfile
	os.rename(fsb_outfile, g_name)
		
	os.chdir(current_path)
	if not os.path.isdir(DJH1_TRACK_FOLDER):
		print("Error: could not find {} for song {}".format(fsb_name, track_id))
		return None

	os.chdir(DJH1_TRACK_FOLDER)
	fsb_outfile = extract_fsb_to_working_folder(working_folder, DJH1_DJ_FSB_NAME, track_id, raw_wav = True)
	if fsb_outfile == None:
		os.chdir(current_path)
		return None
	
	os.chdir(working_folder)
	s_name = "s_" + fsb_outfile
	os.rename(fsb_outfile, s_name)
	
	fsb_outfile = track_id+".flac"
	try:
		sox_out = subprocess.run(["sox/sox.exe", "-M", g_name, s_name, fsb_outfile,
									"remix", "-m", "1,3,5,7,9", "2,4,6,8,10",
								    "rate", "-v", "44100"])
		if sox_out.returncode != 0:
			print("Error: Failed to mix vgm output with sox")
			exit(1)
			return None
	except FileNotFoundError:
		print("Error: Missing tools (vgmstream or sox)")
		exit(1)
		
	os.remove(s_name)
	os.remove(g_name)
	
	os.chdir(working_folder)
	mix_out = write_tags(fsb_outfile)
	os.chdir(current_path)
	return mix_out
	
def extract_djh2(track_id, working_folder):
	current_path = os.path.abspath(".")
	fsb_outfile = extract_fsb_to_working_folder(working_folder, DJH2_FSB_NAME, track_id)
	if fsb_outfile == None:
		os.chdir(current_path)
		return None
		
	os.chdir(working_folder)
	mix_out = write_tags(fsb_outfile)
	os.chdir(current_path)
	return mix_out

def usage_and_exit():
	print("Run with an Audiotracks folder in the same directory")
	print("Or drag a folder of DJHXXX folders onto the script")
	print("Or drag an FSB file onto this script.")
	print("Or from the command line: {} [Audiotracks folder]".format(os.path.basename(__file__)))
	input("\nPress Enter to exit")
	exit(1)
	
def main():
	print("")
	print("DJ Hero Audiotracks to FLAC, v0.5")
	print("")
	
	if len(sys.argv) < 2:
		audiotracks_dir = "Audiotracks"
	elif os.path.isfile(sys.argv[1]):
		# fsb file
		fsb_file = sys.argv[1]
		fsb_name, fsb_ext = os.path.splitext(fsb_file)
		if fsb_ext.lower() != ".fsb":
			usage_and_exit()
			
		fsb_outfile = extract_fsb_to_flac(fsb_file)
		if fsb_outfile == None:
			print("Failed to extract {}".format(fsb_file))
			exit(1)
		else:
			print("Extracted FSB to {}".format(fsb_outfile))
		exit(0)
	else:
		audiotracks_dir = sys.argv[1]

	if not os.path.isdir(audiotracks_dir):
		usage_and_exit()
	
	working_folder = os.path.abspath(".")
	os.chdir(audiotracks_dir)
	failed_tracks = []
	
	for track_id in os.listdir("."):
		if os.path.isdir(track_id):
			print("Extracting {}".format(track_id))
			os.chdir(track_id)
			extract_out = None
			# DJH265 has an extra SinglePlayer folder
			# DJH405 has an extra TwoPlayer folder
			if os.path.isdir(DJH1_GUITAR) and track_id != "DJH405":
				os.chdir(DJH1_GUITAR)
				extract_out = extract_djh1_guitar(track_id, working_folder)
				os.chdir("..")
			elif os.path.isdir(DJH1_SINGLE) and track_id != "DJH265":
				os.chdir(DJH1_SINGLE)
				extract_out = extract_djh1_single(track_id, working_folder)
				os.chdir("..")
			else: # assume DJH2 folder
				extract_out = extract_djh2(track_id, working_folder)
			os.chdir("..")
			
			if extract_out == None:
				print("Failed to extract {}".format(track_id))
				failed_tracks.append(track_id)
			else:
				print("Extracted to {}".format(extract_out))

	print("Done")

if __name__ == "__main__":
	main()