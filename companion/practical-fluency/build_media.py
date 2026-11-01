"""Construct original reference media; not an AI-provider generation or listening trial."""
from pathlib import Path
import argparse,hashlib,json,math,subprocess,wave,struct,textwrap
from PIL import Image,ImageDraw,ImageFont
p=argparse.ArgumentParser();p.add_argument('--book',choices=['chatgpt','claude'],required=True);p.add_argument('--ffmpeg',required=True);a=p.parse_args();d=Path(__file__).resolve().parent/'media';d.mkdir(exist_ok=True)
chat=a.book=='chatgpt';duration=20 if chat else 24;part=[6,7,7] if chat else [8,8,8]
script=('Before borrowing, read the notice. Membership and deposit are different amounts. Ask about any fee the notice leaves unstated. Keep the answer with your visit card.' if chat else 'Open the checklist. Compare each item with the supplied kit list. Mark only what you actually checked. Export the handoff note before resetting the page.')
(d/'narration.txt').write_text(script+'\n');subprocess.run(['/usr/bin/say','-v','Samantha','-r','150','-o',str(d/'narration-source.aiff'),'-f',str(d/'narration.txt')],check=True)
run=lambda args:subprocess.run([a.ffmpeg,'-hide_banner','-loglevel','error','-y',*args],check=True)
run(['-i',str(d/'narration-source.aiff'),'-ar','24000','-ac','1',str(d/'narration.wav')])
notes=[261.63,329.63,392,329.63,293.66,349.23,392,261.63] if chat else [293.66,349.23,440,392,349.23,329.63,293.66,293.66]
rate=24000;samples=[]
for f in notes:
 for i in range(rate):
  envelope=min(1,i/(rate*.04),(rate-i)/(rate*.15));samples.append(int(8000*max(0,envelope)*math.sin(2*math.pi*f*i/rate)))
with wave.open(str(d/'original-cue.wav'),'wb') as out:out.setnchannels(1);out.setsampwidth(2);out.setframerate(rate);out.writeframes(struct.pack('<'+'h'*len(samples),*samples))
(d/'score.json').write_text(json.dumps({'original_authored_reference':True,'frequencies_hz':notes,'seconds_each':1,'synthesis':'sine tones with edge fade; no provider or borrowed recording'},indent=2)+'\n')
labels=([('Read the notice','Find the supplied membership and deposit terms.'),('Compare the amounts','A stated subtotal is not necessarily the complete cost.'),('Keep the unanswered question','Ask about any fee the notice leaves unstated.')] if chat else [('Compare with the kit list','Use the supplied source before marking an item.'),('Mark only checked items','A checked box records the action you actually performed.'),('Export before resetting','Keep the handoff note before clearing local state.')])
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',38);bold=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf',54)
for n,(title,body) in enumerate(labels,1):
 im=Image.new('RGB',(1280,720),'#102e35' if not chat else '#07162f');dr=ImageDraw.Draw(im);dr.text((80,70),f'Practice reference / {n}',fill='#ffcf73',font=font);dr.text((80,190),title,fill='#fff4dd',font=bold)
 for j,line in enumerate(textwrap.wrap(body,46)):dr.text((80,330+j*55),line,fill='white',font=font)
 dr.text((80,620),'Original constructed cards; not a live interface demonstration.',fill='#cdd6dd',font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',26));im.save(d/f'frame-{n}.png')
concat=''.join(f"file 'frame-{n}.png'\nduration {sec}\n" for n,sec in enumerate(part,1))+"file 'frame-3.png'\n";(d/'sequence.txt').write_text(concat)
srt='';start=0
for n,((title,body),sec) in enumerate(zip(labels,part),1):
 fmt=lambda t:f'00:00:{t:02},000'
 srt+=f'{n}\n{fmt(start)} --> {fmt(start+sec)}\n{title}\n\n';start+=sec
(d/'captions.srt').write_text(srt)
segments=([ 'Before borrowing, read the notice.', 'Membership and deposit are different amounts.', 'Ask about any fee the notice leaves unstated. Keep the answer with your visit card.' ] if chat else [ 'Open the checklist. Compare each item with the supplied kit list.', 'Mark only what you actually checked.', 'Export the handoff note before resetting the page.' ])
for n,(text,sec) in enumerate(zip(segments,part),1):
    (d/f'segment-{n}.txt').write_text(text+'\n')
    subprocess.run(['/usr/bin/say','-v','Samantha','-r','150','-o',str(d/f'segment-{n}.aiff'),'-f',str(d/f'segment-{n}.txt')],check=True)
    run(['-i',str(d/f'segment-{n}.aiff'),'-af','apad','-t',str(sec),'-ar','24000','-ac','1',str(d/f'segment-{n}.wav')])
(d/'audio-sequence.txt').write_text(''.join(f"file 'segment-{n}.wav'\n" for n in range(1,4)))
run(['-f','concat','-safe','0','-i',str(d/'audio-sequence.txt'),'-c','copy',str(d/'video-narration.wav')])
run(['-f','concat','-safe','0','-i',str(d/'sequence.txt'),'-i',str(d/'video-narration.wav'),'-vf','fps=25,format=yuv420p','-af','apad','-t',str(duration),'-c:v','libx264','-preset','fast','-crf','24','-c:a','aac','-movflags','+faststart',str(d/'reference.mp4')])
run(['-i',str(d/'narration.wav'),'-stream_loop','-1','-i',str(d/'original-cue.wav'),'-filter_complex','[1:a]volume=0.08[m];[0:a][m]amix=inputs=2:duration=first:normalize=0','-ar','24000',str(d/'narration-with-cue.wav')])
files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(d.iterdir()) if p.is_file() and p.name!='MANIFEST.json'}
(d/'MANIFEST.json').write_text(json.dumps({'kind':'constructed original local reference artifacts; no live AI-provider generation','book':a.book,'video_duration_seconds':duration,'video_frame_pixels':[1280,720],'narration':'macOS Samantha text-to-speech, original script; not voice cloning','cue':'original eight-note score and deterministic synthesis','caption_role':'section-title text, separate from full narration transcript','generator_script':'../build_media.py','files':files,'checks_pending':['human listen-back','native editor workflow','live generative-service trial if chosen','independent audience comprehension']},indent=2)+'\n')
print(a.book,'reference video/audio/score/captions generated')
