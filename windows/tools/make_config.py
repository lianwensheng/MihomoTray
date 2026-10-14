"""Write <outdir>/config.ini from AppConfig.DefaultIni so the shipped file always matches the built-in default.
usage: make_config.py [outfile=dist/config.ini] [theme=light] [--force]
Existing files are never overwritten unless --force is given (keeps the user's secret).
Exit code 0 = written or identical, 2 = existing file differs and was left alone."""
import re, os, sys
root = os.path.join(os.path.dirname(__file__), '..')
force = '--force' in sys.argv
argv = [a for a in sys.argv[1:] if a != '--force']
out = argv[0] if len(argv) > 0 else 'dist/config.ini'
theme = argv[1] if len(argv) > 1 else 'light'
src = open(os.path.join(root, 'src/AppConfig.cs'), encoding='utf-8').read()
m = re.search(r'DefaultIni =\s*(.*?);\s*\n\s*public static string DefaultIniFor', src, re.S).group(1)
s = ''.join(re.findall(r'"((?:[^"\\]|\\.)*)"', m))
s = re.sub(r'\\(.)', lambda x: {'r': '\r', 'n': '\n', '"': '"', '\\': '\\'}[x.group(1)], s)
s = s.replace('{theme}', theme)
path = out if os.path.isabs(out) else os.path.join(root, out)
if os.path.exists(path) and not force:
    if open(path, encoding='utf-8-sig', newline='').read() == s:
        sys.exit(0)
    print('skip %s: already exists (not overwritten; use --force to regenerate)' % out)
    sys.exit(2)
open(path, 'w', encoding='utf-8-sig', newline='').write(s)
