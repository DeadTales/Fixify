"""Regresión del método de enfoque utilizado después del login, sin abrir Tk."""
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from ui.sistema_gestion import SistemaGestion


class WindowFocusTests(unittest.TestCase):
    def test_raise_window_and_release_priority(self):
        window = Mock(spec=SistemaGestion)
        window.winfo_exists.return_value = True

        SistemaGestion.bring_to_front(window)

        window.deiconify.assert_called_once()
        window.lift.assert_called_once()
        window.focus_force.assert_called_once()
        window.attributes.assert_called_with('-topmost', True)
        window.after.assert_called_once_with(250, window._release_topmost)

        SistemaGestion._release_topmost(window)
        window.attributes.assert_called_with('-topmost', False)

    def test_closed_window_is_ignored(self):
        window = Mock(spec=SistemaGestion)
        window.winfo_exists.return_value = False

        SistemaGestion.bring_to_front(window)

        window.lift.assert_not_called()
