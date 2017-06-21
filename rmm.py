import subprocess
import sys
import json
import shlex
import csv

#	@author Victor Renan Covalski Junes <vrcjunes@inf.ufpel.edu.br>
#	@author	Henrique Pereira Borges 	<hpborges@inf.ufpel.edu.br>

# Funcao para pegar o SSIM e PSNR 
def get_stats(video_stream, output):
	arg = 'ffmpeg -i ' + video_stream + ' -i ' + output + ' -lavfi "ssim;[0:v][1:v]psnr" -f null -' 
	stats = subprocess.Popen( shlex.split(arg) , stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
	
	#parse values
	lines = stats.communicate()[0].splitlines()
	result = dict()

	for l in lines:
		if l.startswith('[Parsed_ssim_0 @'):
			# ssim data
			l = l[l.find(']')+7:].split(' ')
			for d in l:
				if(d.startswith('All:')):
					result['ssim'] = d.split(':')[1]
				
		elif l.startswith('[Parsed_psnr_1 @'):
			# psnr data
			l = l[l.find(']')+7:].split(' ')
			for d in l:
				if(d.startswith('average:')):
					result['psnr'] = d.split(':')[1]
		
	return result

def reencode(target, writer, profile = 'ultrafast'):
	#width, height, bitrate and duration of the video #v:0 ignores the audio stream
	arg = 'ffprobe -v quiet -print_format json -select_streams '\
	      'v:0 -show_entries stream=r_frame_rate,height,width,bit_rate,duration {}'.format(target)
	result = subprocess.Popen(shlex.split(arg),stdout=subprocess.PIPE)
	result.wait()
	file_info = json.loads(result.communicate()[0].decode("utf-8"))

	#parsing metadata
	original_bitrate = float(file_info['streams'][0]['bit_rate'])
	resolution = '{}x{}'.format(file_info['streams'][0]['width'],file_info['streams'][0]['height'])
	h = int(resolution.split('x')[0])
	w = int(resolution.split('x')[1])

	# Write target file to csv
	row['archive'] = target
	row['resolution'] = resolution
	row['bitrate'] = original_bitrate
	row['SSIM'] = 'N/A'
	row['PSNR'] = 'N/A'
	writer.writerow(row) 

	#get frame rate
	r_frame_rate = file_info['streams'][0]['r_frame_rate']
	target_fps = 1 + int(int(r_frame_rate.split('/')[0]) / int(r_frame_rate.split('/')[1]))
	i_frame_interval = target_fps*2


	#calculate target bitrate
	target_bitrate = [0.8,0.6,0.4,0.2]

	for b in target_bitrate:
		print '.',
		sys.stdout.flush()
		output = '{}x{}_{}.mp4'.format(h,w,int(b*100))
		bitrate = b * original_bitrate
		arg = 'ffmpeg -loglevel 0 -y -r {0} -i {1} -c:v libx264 -preset {2} -crf 22 '\
		      '-x264-params keyint={3}:min-keyint={3}:scenecut=-1 -strict experimental '\
			  '-b:v {4} -bufsize {4} -minrate {4} -maxrate {4} {5}'\
			  ''.format(target_fps, target, profile,i_frame_interval, bitrate, output)
		subprocess.Popen(shlex.split(arg), stderr = subprocess.STDOUT).wait()

		# Gerar os dados de qualidade
		stats = get_stats(target, output)

		# Escrever no csv
		row['archive'] = output
		row['resolution'] = resolution
		row['bitrate'] = bitrate
		row['SSIM'] = stats['ssim']
		row['PSNR'] = stats['psnr']
		writer.writerow(row)
	print

original_file = sys.argv[1] #filename

#output this to CSV
arq = open('out.csv', 'w')
header = ['archive' ,'resolution', 'bitrate', 'PSNR', 'SSIM']
writer = csv.DictWriter(arq, fieldnames = header)
writer.writeheader()
row = dict()

#############################################
### 

#separate video stream
# print 'Spliting video'
# video_stream =  'video_stream.mp4'
# arg = 'ffmpeg -loglevel 0 -i {} -an -c copy {} -y'.format(original_file, video_stream)
# subprocess.Popen(shlex.split(arg)).wait()

# #separate audio stream
# print 'Spliting audio'
# audio_stream = 'audio_stream.aac'
# arg = 'ffmpeg -loglevel 0 -i {} -r {} -vn -c copy {} -y'.format(original_file, target_fps, audio_stream)
# subprocess.Popen(shlex.split(arg)).wait()

# print 'Joining'
# target_1080 = 'target_1080.mp4'
# arg = 'ffmpeg -loglevel 0 -i {} -i {} -c:v copy -c:a aac -strict experimental {} -y'.format(video_stream, audio_stream, target_1080)
# subprocess.Popen(shlex.split(arg)).wait()


print 'reencoding'
# Resolucao original

print '1080p'
reencode(original_file, writer)

print '720p'
# Encode target video
target_720 = 'target_720.mp4'
arg = 'ffmpeg -loglevel 0 -i {} -vf scale=-1:720 -strict experimental {} -y'.format(original_file, target_720)
subprocess.Popen(shlex.split(arg), stderr=subprocess.PIPE).wait()
reencode(target_720, writer)

print '480p'
# Encode target video
target_480 = 'target_480.mp4'
arg = 'ffmpeg -loglevel 0 -i {} -vf scale=-1:480 -strict experimental {} -y'.format(original_file, target_480)
subprocess.Popen(shlex.split(arg), stderr=subprocess.PIPE).wait()
reencode(target_480, writer)
