import subprocess
import json
from pathlib import Path
from shutil import copyfileobj
from urllib.error import URLError
from urllib.request import urlopen

import pytest


TEST_DATA_API_URL = 'https://api.github.com/repos/potfit/test_data/contents/ase?ref=main'
TEST_DATA_BASE_URL = 'https://raw.githubusercontent.com/potfit/test_data/refs/heads/main/ase'


def _list_test_data_files():
    with urlopen(TEST_DATA_API_URL) as response:
        entries = json.load(response)
    return sorted(
        entry['name']
        for entry in entries
        if entry.get('type') == 'file' and entry['name'].startswith('OUTCAR')
    )


def _download_test_data(data_dir):
    data_dir.mkdir(parents=True, exist_ok=True)
    for file_name in _list_test_data_files():
        url = f'{TEST_DATA_BASE_URL}/{file_name}'
        destination = data_dir / file_name
        try:
            with urlopen(url) as response, destination.open('wb') as output:
                copyfileobj(response, output)
        except (OSError, URLError) as exc:
            raise RuntimeError(f'failed to download {url}') from exc


def _run_converter(script, outcar):
    result = subprocess.run(
        [str(script), '-f', str(outcar)],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[2],
    )
    return result


@pytest.fixture(scope='session')
def ase2force_test_data(tmp_path_factory):
    data_dir = tmp_path_factory.mktemp('ase2force')
    _download_test_data(data_dir)
    return data_dir


def test_ase2force_test_data_download(ase2force_test_data):
    for file_name in _list_test_data_files():
        assert (ase2force_test_data / file_name).is_file()


def pytest_generate_tests(metafunc):
    if 'outcar_name' in metafunc.fixturenames:
        metafunc.parametrize('outcar_name', _list_test_data_files())


def test_ase2force_matches_vasp2force(ase2force_test_data, outcar_name):
    outcar = ase2force_test_data / outcar_name
    root = Path(__file__).resolve().parents[2]
    ase2force = root / 'util' / 'ase2force'
    vasp2force = root / 'util' / 'vasp2force'

    ase_result = _run_converter(ase2force, str(outcar))
    vasp_result = _run_converter(vasp2force, str(outcar))

    assert ase_result.returncode == 0, ase_result.stderr
    assert vasp_result.returncode == 0, vasp_result.stderr
    assert ase_result.stdout == vasp_result.stdout


def test_ase2force_reports_unsupported_format(tmp_path):
    root = Path(__file__).resolve().parents[2]
    ase2force = root / 'util' / 'ase2force'
    invalid_outcar = tmp_path / 'invalid.outcar'
    invalid_outcar.write_text(
        'vasp\n'
        'this file is not a valid OUTCAR for ASE\n'
    )

    result = _run_converter(ase2force, str(invalid_outcar))

    assert result.returncode != 0
    assert 'ASE format not supported' in result.stderr
