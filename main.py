#!/usr/bin/env python3
import atexit
import enum
import http
import shutil
import sys
from pathlib import Path
from tempfile import mkdtemp

if sys.version_info < (3, 8):
    message = (
        "The Python version "
        + ".".join(map(str, sys.version_info[:3]))
        + " is not supported.\n"
        + "Use Python 3.8 or newer."
    )
    try:
        import tkinter
    except ImportError:
        input(message)  # wait for the user to see the text
    else:
        print(message, file=sys.stderr)

        import tkinter.messagebox

        _root = tkinter.Tk()
        _root.withdraw()
        tkinter.messagebox.showerror(title="Outdated Python", message=message)
        _root.destroy()

    exit(1)

if sys.version_info < (3, 10):

    def list_files(path: Path, *, suffix: "str | None" = None) -> "list[Path]":
        files: "list[Path]" = []
        if path.name.startswith("."):
            # ignore hidden files
            return []
        if path.is_dir():
            for file in path.iterdir():
                files.extend(list_files(file, suffix=suffix))
        elif path.is_file() and (suffix in (None, path.suffix)):
            files.append(path.absolute())
        return files

    me: Path = Path(__file__).resolve()
    my_parent: Path = me.parent

    annotations_needed: bool = False
    for f in list_files(my_parent):
        if f.is_file():
            if f.suffix == me.suffix:
                lines: "list[str]" = f.read_text().splitlines()
                if not any(line.startswith("from __future__ import annotations") for line in lines):
                    annotations_needed = True

    if annotations_needed:
        tmp_dir: Path = Path(mkdtemp())
        sys.path.insert(0, str(tmp_dir))

        for f in list_files(my_parent):
            if f.is_file():
                (tmp_dir / f.relative_to(my_parent)).parent.mkdir(parents=True, exist_ok=True)
                if f.suffix == me.suffix:
                    lines: "list[str]" = f.read_text().splitlines()
                    if not any(line.startswith("from __future__ import annotations") for line in lines):
                        lines.insert(0, "from __future__ import annotations")
                    new_text: str = "\n".join(lines)
                    new_text = new_text.replace("ParamSpec", "TypeVar")
                    (tmp_dir / f.relative_to(my_parent)).write_text(new_text)
                else:
                    (tmp_dir / f.relative_to(my_parent)).write_bytes(f.read_bytes())
            elif f.is_dir():
                (tmp_dir / f.relative_to(my_parent)).mkdir()

        atexit.register(shutil.rmtree, tmp_dir, ignore_errors=True)

if sys.version_info < (3, 11):

    class HTTPMethod(enum.Enum):
        CONNECT = "CONNECT"
        DELETE = "DELETE"
        GET = "GET"
        HEAD = "HEAD"
        OPTIONS = "OPTIONS"
        PATCH = "PATCH"
        POST = "POST"
        PUT = "PUT"
        TRACE = "TRACE"

    http.HTTPMethod = HTTPMethod


if __name__ == "__main__":
    try:
        from pycatsearch import main
    except ImportError:
        __author__ = "StSav012"
        __original_name__ = "pycatsearch"

        try:
            from updater import update_with_pip

            update_with_pip(__original_name__)

            from pycatsearch import main_gui as main
        except ImportError:
            from updater import update_with_pip, update_from_github, update_with_git

            update_with_git() or update_from_github(__author__, __original_name__)

            from src.pycatsearch import main_gui as main
    main()
