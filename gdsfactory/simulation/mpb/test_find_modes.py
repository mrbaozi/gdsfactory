import numpy as np

from gdsfactory.simulation.mpb.find_neff import find_neff
from gdsfactory.simulation.mpb.get_mode_solver_rib import get_mode_solver_rib


def test_find_modes():
    ms = get_mode_solver_rib(wg_width=0.45)
    modes = find_neff(mode_solver=ms)
    m1 = modes[1]
    m2 = modes[2]
    neff1 = 2.342628111145838
    neff2 = 1.7286034634949181

    assert np.isclose(m1.neff, neff1), (m1.neff, neff1)
    assert np.isclose(m2.neff, neff2), (m2.neff, neff2)


if __name__ == "__main__":
    test_find_modes()
    # ms = get_mode_solver_rib(wg_width=0.45)
    # modes = find_neff(mode_solver=ms)
    # m1 = modes[1]
    # m2 = modes[2]
    # neff1 = 2.342628111145838
    # neff2 = 1.7286034634949181

    # assert np.isclose(m1.neff, neff1), (m1.neff, neff1)
    # assert np.isclose(m2.neff, neff2), (m2.neff, neff2)
