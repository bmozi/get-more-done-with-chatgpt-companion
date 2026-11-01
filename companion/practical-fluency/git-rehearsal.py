"""Run only in an automatically created disposable folder; no remote/network."""
import subprocess,tempfile,json
from pathlib import Path
with tempfile.TemporaryDirectory(prefix='book-git-practice-') as td:
 p=Path(td)
 def git(*args):return subprocess.check_output(['git','-C',td,*args],stderr=subprocess.STDOUT).decode().strip()
 git('init');git('config','user.name','Fictional local practice');git('config','user.email','practice@example.invalid');git('switch','-c','practice')
 note=p/'note.txt';note.write_text('draft one\n');git('add','note.txt');git('commit','-m','First practice note');first=git('rev-parse','HEAD')
 note.write_text('draft two\n');delta=git('diff','--','note.txt');assert '-draft one' in delta and '+draft two' in delta
 git('add','note.txt');git('commit','-m','Second practice note');second=git('rev-parse','HEAD')
 note.write_text('temporary third edit\n');(p/'scratch.txt').write_text('untracked practice\n');git('restore','--source=HEAD','--','note.txt')
 assert note.read_text()=='draft two\n' and git('show','HEAD~1:note.txt')=='draft one';assert '?? scratch.txt' in git('status','--short')
 print(json.dumps({'kind':'actual local Git rehearsal in disposable folder','commits':[first,second],'diff_checked':True,'tracked_file_restored':True,'untracked_file_remains':True,'remote_used':False},indent=2))
