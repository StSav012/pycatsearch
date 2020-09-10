import http.client
import io
import urllib.request
import zipfile
from pathlib import Path


def update(user: str, repo_name: str, branch: str = 'master'):
    extraction_root: Path = Path.cwd()
    url: str = f'https://github.com/{user}/{repo_name}/archive/{branch}.zip'
    r: http.client.HTTPResponse = urllib.request.urlopen(url)
    if r.getcode() == 200:
        with zipfile.ZipFile(io.BytesIO(r.read())) as inner_zip:
            root: Path = Path(f'{repo_name}-{branch}/')
            for member in inner_zip.infolist():
                if member.is_dir():
                    continue
                content: bytes = inner_zip.read(member)
                (extraction_root / Path(member.filename).relative_to(root)).parent.mkdir(parents=True, exist_ok=True)
                with (extraction_root / Path(member.filename).relative_to(root)).open('wb') as f_out:
                    f_out.write(content)
