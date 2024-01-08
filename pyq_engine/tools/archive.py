import argparse
import sigmf
from pathlib import Path


def main():
    parser = argparse.ArgumentParser('pyq-archive')
    parser.add_argument('metafile', type=Path)
    parser.add_argument('--outputdir', '-o', type=Path, default='.')
    options = parser.parse_args()

    arc = options.outputdir / (options.metafile.stem + '.sigmf')

    if not options.metafile.exists():
        print('input file doesn\'t exist')
        return

    meta = sigmf.sigmffile.fromfile(options.metafile.as_posix())

    with open(arc, 'wb') as out:
        meta.archive(fileobj=out)
    print(f'wrote: {arc}')


if __name__ == '__main__':
    main()
