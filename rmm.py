import subprocess
import sys
import json
import shlex

#	@author Victor Renan Covalski Junes <vrcjunes@inf.ufpel.edu.br>
#	@author	Henrique Pereira Borges 	<hpborges@inf.ufpel.edu.br>

original_file = sys.argv[1] #filename

profile = sys.argv[2]

#width, height, bitrate and duration of the video #v:0 ignores the audio stream
print 'Getting metadata'
result = subprocess.Popen(['ffprobe', 
						'-v','quiet',
						'-print_format', 'json',
						'-select_streams','v:0',
						'-show_entries','stream=r_frame_rate,width,height,bit_rate,duration',
						original_file],stdout=subprocess.PIPE)

file_info = json.loads(result.communicate()[0].decode("utf-8"))


#output this to CSV

#parsing metadata
original_bitrate = float(file_info['streams'][0]['bit_rate'])
resolution = '{}x{}'.format(file_info['streams'][0]['width'],file_info['streams'][0]['height'])
h = int(resolution.split('x')[0])
w = int(resolution.split('x')[1])

#get frame rate
r_frame_rate = file_info['streams'][0]['r_frame_rate']
target_fps = 1 + int(int(r_frame_rate.split('/')[0]) / int(r_frame_rate.split('/')[1]))

#calculate target bitrate
target_bitrate = [1.0,0.8,0.6,0.4,0.2]
target_bitrate[:] = [int(x*original_bitrate) for x in target_bitrate]

video_stream =  'video_stream.mp4'

print 'Spliting video'

#separate video stream
subprocess.Popen(['ffmpeg',
				'-i',original_file,
				'-an','-c','copy',video_stream],stderr=subprocess.PIPE) #redirecting stderr in order to make script run silently

print 'Spliting audio'
#separate audio stream
subprocess.Popen(['ffmpeg',
				'-i',original_file,
				'-r',str(target_fps),
				'-vn','-c','copy','audio_stream.m4a'],stderr=subprocess.PIPE)

#prepare string for x264-params
i_frame_interval = target_fps*2

print 'reecoding video'

#encode for 1920x1080(1080p)
print '1080p',
for x in target_bitrate: 
	print x,
	output = '{}_{}.mp4'.format(1080,x)

	result = subprocess.Popen(['ffmpeg', '-y',
	'-r',str(target_fps),
	'-i',video_stream,
	'-c:v','libx264',
	'-preset', profile,
	'-crf','22',
	'-x264-params', 'keyint={0}:min-keyint={0}:scenecut=-1'.format(i_frame_interval),
	'-b:v','{}'.format(x),
	'-bufsize', '{}'.format(x),
	'-minrate', '{}'.format(x),
	'-maxrate', '{}'.format(x),
	output], stderr=subprocess.STDOUT, stdout=subprocess.PIPE) #ffmpeg outputs to stderr
	
	result.wait()

	# Gerar os dados de qualidade
	arg = 'ffmpeg -i ' + video_stream + ' -i ' + output + ' -lavfi "ssim;[0:v][1:v]psnr" -f null -' 
	stats = subprocess.Popen( shlex.split(arg) , stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

	stats.wait()

	#parse values
	lines = stats.communicate()[0].splitlines()

	print len(lines)

	for l in lines:
		if l.startswith('[Parsed_ssim_0 @'):
			# ssim data
			l = l[l.find(']')+7:].split(' ')
			for d in l:
				if(d.startswith('(')):
					print d[1:-1]
				else:
					sp = d.split(':')
					print sp[0], sp[1]

		elif l.startswith('[Parsed_psnr_1 @'):
			# psnr data
			l = l[l.find(']')+7:].split(' ')
			for d in l:
				sp = d.split(':')
				print sp[0], sp[1]

	exit(1)

print 
print '720p'
for x in target_bitrate: 
	print x,
	output = '{}_{}.mp4'.format(720,x)

	result = subprocess.Popen(['ffmpeg', '-y',
	'-r',str(target_fps),
	'-i',video_stream,
	'-c:v','libx264',
	'-preset', profile,
	'-crf','22',
	'-x264-params', 'keyint={0}:min-keyint={0}:scenecut=-1'.format(i_frame_interval),
	'-b:v','{}'.format(x),
	'-bufsize', '{}'.format(x),
	'-minrate', '{}'.format(x),
	'-maxrate', '{}'.format(x),
	'-vf', 'scale={}:{}'.format(2*h/3,2*w/3),
	output], stderr=subprocess.PIPE).wait() #ffmpeg outputs to stderr
	

print 
print '480p'
for x in target_bitrate: 
	print x,
	output = '{}_{}.mp4'.format(480,x)

	result = subprocess.Popen(['ffmpeg', '-y',
	'-r',str(target_fps),
	'-i',video_stream,
	'-c:v','libx264',
	'-preset', profile,
	'-crf','22',
	'-x264-params', 'keyint={0}:min-keyint={0}:scenecut=-1'.format(i_frame_interval),
	'-b:v','{}'.format(x),
	'-bufsize', '{}'.format(x),
	'-minrate', '{}'.format(x),
	'-maxrate', '{}'.format(x),
	'-vf', 'scale={}:{}'.format(h/3,w/3),
	output], stderr=subprocess.PIPE).wait()

print

