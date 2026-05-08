import os
import subprocess
import urllib.error
import urllib.request

import pytest


OUTCAR_URL = 'https://raw.githubusercontent.com/keeeto/VASP-Elastic/refs/heads/master/OUTCAR'
OUTCAR_005_URL = 'https://raw.githubusercontent.com/keeeto/VASP-Elastic/master/OUTCAR.005'


def _run_converter(script, outcar):
    result = subprocess.run(
        [script, '-f', outcar],
        check=False,
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.dirname(__file__)),
    )
    return result


@pytest.mark.parametrize('outcar_url', [OUTCAR_URL, OUTCAR_005_URL])
def test_ase2force_matches_vasp2force(tmp_path, outcar_url):
    outcar = tmp_path / 'OUTCAR'
    try:
        with urllib.request.urlopen(outcar_url, timeout=30) as response:
            outcar.write_bytes(response.read())
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        pytest.skip(f'Could not download sample OUTCAR: {exc}')

    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    ase2force = os.path.join(root, 'util', 'ase2force')
    vasp2force = os.path.join(root, 'util', 'vasp2force')

    ase_result = _run_converter(ase2force, str(outcar))
    vasp_result = _run_converter(vasp2force, str(outcar))

    assert ase_result.returncode == 0, ase_result.stderr
    assert vasp_result.returncode == 0, vasp_result.stderr
    assert ase_result.stdout == vasp_result.stdout
