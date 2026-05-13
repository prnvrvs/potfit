import subprocess
from pathlib import Path

import pytest


DATA_DIR = Path(__file__).resolve().parents[1] / 'data' / 'ase2force'


def _run_converter(script, outcar):
    result = subprocess.run(
        [str(script), '-f', str(outcar)],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[2],
    )
    return result


@pytest.mark.parametrize('outcar_name', ['OUTCAR_example_1', 'OUTCAR_example_1.gz'])
def test_ase2force_matches_vasp2force(outcar_name):
    outcar = DATA_DIR / outcar_name
    root = Path(__file__).resolve().parents[2]
    ase2force = root / 'util' / 'ase2force'
    vasp2force = root / 'util' / 'vasp2force'

    ase_result = _run_converter(ase2force, str(outcar))
    vasp_result = _run_converter(vasp2force, str(outcar))

    assert ase_result.returncode == 0, ase_result.stderr
    assert vasp_result.returncode == 0, vasp_result.stderr
    assert ase_result.stdout == vasp_result.stdout
