# -*- coding: utf-8 -*-

# Copyright 2018, IBM.
#
# This source code is licensed under the Apache License, Version 2.0 found in
# the LICENSE.txt file in the root directory of this source tree.

# TODO(mtreinish): Remove after 0.7 and the deprecated methods are removed
# pylint: disable=unused-argument


"""
Two quantum circuit drawers based on:
    0. Ascii art
    1. LaTeX
    2. Matplotlib
"""
import json

import errno
import logging
import os
import subprocess
import tempfile
import warnings

from PIL import Image

from qiskit.tools.visualization import _error
from qiskit.tools.visualization import _latex
from qiskit.tools.visualization import _text
from qiskit.tools.visualization import _utils
from qiskit.tools.visualization import _matplotlib

logger = logging.getLogger(__name__)


def plot_circuit(circuit,
                 basis="id,u0,u1,u2,u3,x,y,z,h,s,sdg,t,tdg,rx,ry,rz,"
                       "cx,cy,cz,ch,crz,cu1,cu3,swap,ccx,cswap",
                 scale=0.7,
                 style=None):
    """Plot and show circuit (opens new window, cannot inline in Jupyter)"""
    warnings.warn('The plot_circuit() function is deprecated and will be '
                  'removed in the future. Instead use circuit_drawer() with '
                  'the `interactive` flag set true', DeprecationWarning)
    image = circuit_drawer(circuit, scale=scale, style=style)
    if image:
        image.show()


def circuit_drawer(circuit,
                   scale=0.7,
                   filename=None,
                   style=None,
                   output=None,
                   interactive=False,
                   line_length=None,
                   plot_barriers=True,
                   reverse_bits=False):
    """Draw a quantum circuit to different formats (set by output parameter):
    0. text: ASCII art TextDrawing that can be printed in the console.
    1. latex: high-quality images, but heavy external software dependencies
    2. matplotlib: purely in Python with no external dependencies

    Args:
        circuit (QuantumCircuit): the quantum circuit to draw
        scale (float): scale of image to draw (shrink if < 1)
        filename (str): file path to save image to
        style (dict or str): dictionary of style or file name of style file.
            This option is only used by the `mpl`, `latex`, and `latex_source`
            output types. If a str is passed in that is the path to a json
            file which contains that will be open, parsed, and then used just
            as the input dict.
        output (TextDrawing): Select the output method to use for drawing the circuit.
            Valid choices are `text`, `latex`, `latex_source`, `mpl`. Note if
            one is not specified it will use latex and if that fails fallback
            to mpl. However this behavior is deprecated and in a future release
            the default will change.
        interactive (bool): when set true show the circuit in a new window
            (cannot inline in Jupyter). Note when used with the latex_source
            output type this has no effect.
        line_length (int): Sets the length of the lines generated by `text`
            output type. This useful when the drawing does not fit in the
            console. If None (default), it will try to guess the console width
            using shutil.get_terminal_size(). If you don't want pagination at
            all, set `line_length=-1`.
        reverse_bits (bool): When set to True reverse the bit order inside
            registers for the output visualization.
        plot_barriers (bool): Enable/disable drawing barriers in the output
            circuit. Defaults to True.

    Returns:
        PIL.Image: (output `latex`) an in-memory representation of the image
            of the circuit diagram.
        matplotlib.figure: (output `mpl`) a matplotlib figure object for the
            circuit diagram.
        String: (output `latex_source`). The LaTeX source code.
        TextDrawing: (output `text`). A drawing that can be printed as ascii art
    Raises:
        VisualizationError: when an invalid output method is selected
        ImportError: when the output methods requieres non-installed libraries.

    .. _style-dict-doc:

    The style dict kwarg contains numerous options that define the style of the
    output circuit visualization. While the style dict is used by the `mpl`,
    `latex`, and `latex_source` outputs some options in that are only used
    by the `mpl` output. These options are defined below, if it is only used by
    the `mpl` output it is marked as such:

        textcolor (str): The color code to use for text. Defaults to
            `'#000000'` (`mpl` only)
        subtextcolor (str): The color code to use for subtext. Defaults to
            `'#000000'` (`mpl` only)
        linecolor (str): The color code to use for lines. Defaults to
            `'#000000'` (`mpl` only)
        creglinecolor (str): The color code to use for classical register lines
            `'#778899'`(`mpl` only)
        gatetextcolor (str): The color code to use for gate text `'#000000'`
            (`mpl` only)
        gatefacecolor (str): The color code to use for gates. Defaults to
            `'#ffffff'` (`mpl` only)
        barrierfacecolor (str): The color code to use for barriers. Defaults to
            `'#bdbdbd'` (`mpl` only)
        backgroundcolor (str): The color code to use for the background.
            Defaults to `'#ffffff'` (`mpl` only)
        fontsize (int): The font size to use for text. Defaults to 13 (`mpl`
            only)
        subfontsize (int): The font size to use for subtext. Defaults to 8
            (`mpl` only)
        displaytext (dict): A dictionary of the text to use for each element
            type in the output visualization. The default values are:
            {
                'id': 'id',
                'u0': 'U_0',
                'u1': 'U_1',
                'u2': 'U_2',
                'u3': 'U_3',
                'x': 'X',
                'y': 'Y',
                'z': 'Z',
                'h': 'H',
                's': 'S',
                'sdg': 'S^\\dagger',
                't': 'T',
                'tdg': 'T^\\dagger',
                'rx': 'R_x',
                'ry': 'R_y',
                'rz': 'R_z',
                'reset': '\\left|0\\right\\rangle'
            }
            You must specify all the necessary values if using this. There is
            no provision for passing an incomplete dict in. (`mpl` only)
        displaycolor (dict): The color codes to use for each circuit element.
            By default all values default to the value of `gatefacecolor` and
            the keys are the same as `displaytext`. Also, just like
            `displaytext` there is no provision for an incomplete dict passed
            in. (`mpl` only)
        latexdrawerstyle (bool): When set to True enable latex mode which will
            draw gates like the `latex` output modes. (`mpl` only)
        usepiformat (bool): When set to True use radians for output (`mpl`
            only)
        fold (int): The number of circuit elements to fold the circuit at.
            Defaults to 20 (`mpl` only)
        cregbundle (bool): If set True bundle classical registers (`mpl` only)
        plotbarrier (bool): Enable/disable drawing barriers in the output
            circuit. Defaults to True. This is deprecated in the style dict
            and will be removed in a future release. Use the `plot_barriers`
            kwarg instead.
        showindex (bool): If set True draw an index. (`mpl` only)
        compress (bool): If set True draw a compressed circuit (`mpl` only)
        figwidth (int): The maximum width (in inches) for the output figure.
            (`mpl` only)
        dpi (int): The DPI to use for the output image. Defaults to 150 (`mpl`
            only)
        margin (list): `mpl` only
        creglinestyle (str): The style of line to use for classical registers.
            Choices are `'solid'`, `'doublet'`, or any valid matplotlib
            `linestyle` kwarg value. Defaults to `doublet`(`mpl` only)
        reversebits (bool): When set to True reverse the bit order inside
            registers for the output visualization. This is deprecated in the
            style dict and will be removed in a future release use the
            `reverse_bits` kwarg instead.

    """
    im = None
    image = None
    if style:
        if 'reversebits' in style:
            warnings.warn('The reversebits key in style is deprecated and will'
                          'not work in the future. Instead use the '
                          '``reverse_bits`` kwarg.', DeprecationWarning)
            reverse_bits = style.get('reversebits')
        if 'plotbarrier' in style:
            warnings.warn('The plotbarrier key in style is deprecated and will'
                          'not work in the future. Instead use the '
                          '``plot_barriers`` kwarg.', DeprecationWarning)
            plot_barriers = style.get('plotbarrier')

    if not output:
        warnings.warn('The current behavior for the default output will change'
                      ' in a future release. Instead of trying latex and '
                      'falling back to mpl on failure it will just use '
                      '"text" by default', DeprecationWarning)
        try:
            image = _latex_circuit_drawer(circuit, scale, filename, style)
        except (OSError, subprocess.CalledProcessError, FileNotFoundError):
            if _matplotlib.HAS_MATPLOTLIB:
                image = _matplotlib_circuit_drawer(circuit, scale, filename,
                                                   style)
            else:
                raise ImportError('The default output needs matplotlib. '
                                  'Run "pip install matplotlib" before.')
    else:
        if output == 'text':
            return _text_circuit_drawer(circuit, filename=filename,
                                        line_length=line_length,
                                        reversebits=reverse_bits,
                                        plotbarriers=plot_barriers)
        elif output == 'latex':
            image = _latex_circuit_drawer(circuit, scale=scale,
                                          filename=filename, style=style,
                                          plot_barriers=plot_barriers,
                                          reverse_bits=reverse_bits)
        elif output == 'latex_source':
            return _generate_latex_source(circuit,
                                          filename=filename, scale=scale,
                                          style=style,
                                          plot_barriers=plot_barriers,
                                          reverse_bits=reverse_bits)
        elif output == 'mpl':
            image = _matplotlib_circuit_drawer(circuit, scale=scale,
                                               filename=filename, style=style,
                                               plot_barriers=plot_barriers,
                                               reverse_bits=reverse_bits)
        else:
            raise _error.VisualizationError(
                'Invalid output type %s selected. The only valid choices '
                'are latex, latex_source, text, and mpl' % output)
    if image and interactive:
        image.show()
    return image

# -----------------------------------------------------------------------------
# Plot style sheet option
# -----------------------------------------------------------------------------
def qx_color_scheme():
    """Return default style for matplotlib_circuit_drawer (IBM QX style)."""
    return {
        "comment": "Style file for matplotlib_circuit_drawer (IBM QX Composer style)",
        "textcolor": "#000000",
        "gatetextcolor": "#000000",
        "subtextcolor": "#000000",
        "linecolor": "#000000",
        "creglinecolor": "#b9b9b9",
        "gatefacecolor": "#ffffff",
        "barrierfacecolor": "#bdbdbd",
        "backgroundcolor": "#ffffff",
        "fold": 20,
        "fontsize": 13,
        "subfontsize": 8,
        "figwidth": -1,
        "dpi": 150,
        "displaytext": {
            "id": "id",
            "u0": "U_0",
            "u1": "U_1",
            "u2": "U_2",
            "u3": "U_3",
            "x": "X",
            "y": "Y",
            "z": "Z",
            "h": "H",
            "s": "S",
            "sdg": "S^\\dagger",
            "t": "T",
            "tdg": "T^\\dagger",
            "rx": "R_x",
            "ry": "R_y",
            "rz": "R_z",
            "reset": "\\left|0\\right\\rangle"
        },
        "displaycolor": {
            "id": "#ffca64",
            "u0": "#f69458",
            "u1": "#f69458",
            "u2": "#f69458",
            "u3": "#f69458",
            "x": "#a6ce38",
            "y": "#a6ce38",
            "z": "#a6ce38",
            "h": "#00bff2",
            "s": "#00bff2",
            "sdg": "#00bff2",
            "t": "#ff6666",
            "tdg": "#ff6666",
            "rx": "#ffca64",
            "ry": "#ffca64",
            "rz": "#ffca64",
            "reset": "#d7ddda",
            "target": "#00bff2",
            "meas": "#f070aa"
        },
        "latexdrawerstyle": True,
        "usepiformat": False,
        "cregbundle": False,
        "plotbarrier": False,
        "showindex": False,
        "compress": True,
        "margin": [2.0, 0.0, 0.0, 0.3],
        "creglinestyle": "solid",
        "reversebits": False
    }


# -----------------------------------------------------------------------------
# _text_circuit_drawer
# -----------------------------------------------------------------------------


def _text_circuit_drawer(circuit, filename=None, line_length=None, reversebits=False,
                         plotbarriers=True):
    """
    Draws a circuit using ascii art.
    Args:
        circuit (QuantumCircuit): Input circuit
        filename (str): optional filename to write the result
        line_length (int): Optional. Breaks the circuit drawing to this length. This
                   useful when the drawing does not fit in the console. If
                   None (default), it will try to guess the console width using
                   shutil.get_terminal_size(). If you don't want pagination
                   at all, set line_length=-1.
        reversebits (bool): Rearrange the bits in reverse order.
        plotbarriers (bool): Draws the barriers when they are there.
    Returns:
        TextDrawing: An instances that, when printed, draws the circuit in ascii art.
    """
    qregs, cregs, ops = _utils._get_instructions(circuit, reversebits=reversebits)
    text_drawing = _text.TextDrawing(qregs, cregs, ops)
    text_drawing.plotbarriers = plotbarriers
    text_drawing.line_length = line_length

    if filename:
        text_drawing.dump(filename)
    return text_drawing


# -----------------------------------------------------------------------------
# latex_circuit_drawer
# -----------------------------------------------------------------------------

def latex_circuit_drawer(circuit,
                         basis="id,u0,u1,u2,u3,x,y,z,h,s,sdg,t,tdg,rx,ry,rz,"
                               "cx,cy,cz,ch,crz,cu1,cu3,swap,ccx,cswap",
                         scale=0.7,
                         filename=None,
                         style=None):
    """Draw a quantum circuit based on latex (Qcircuit package)

    Requires version >=2.6.0 of the qcircuit LaTeX package.

    Args:
        circuit (QuantumCircuit): a quantum circuit
        basis (str): comma separated list of gates
        scale (float): scaling factor
        filename (str): file path to save image to
        style (dict or str): dictionary of style or file name of style file

    Returns:
        PIL.Image: an in-memory representation of the circuit diagram

    Raises:
        OSError: usually indicates that ```pdflatex``` or ```pdftocairo``` is
                 missing.
        CalledProcessError: usually points errors during diagram creation.
    """
    warnings.warn('The latex_circuit_drawer() function is deprecated and will '
                  'be removed in a future release. Instead use the '
                  'circuit_drawer() function with the `output` kwarg set to '
                  '`latex`.', DeprecationWarning)
    return _latex_circuit_drawer(circuit, scale=scale,
                                 filename=filename, style=style)


def _latex_circuit_drawer(circuit,
                          scale=0.7,
                          filename=None,
                          style=None,
                          plot_barriers=True,
                          reverse_bits=False):
    """Draw a quantum circuit based on latex (Qcircuit package)

    Requires version >=2.6.0 of the qcircuit LaTeX package.

    Args:
        circuit (QuantumCircuit): a quantum circuit
        scale (float): scaling factor
        filename (str): file path to save image to
        style (dict or str): dictionary of style or file name of style file
        reverse_bits (bool): When set to True reverse the bit order inside
            registers for the output visualization.
        plot_barriers (bool): Enable/disable drawing barriers in the output
            circuit. Defaults to True.

    Returns:
        PIL.Image: an in-memory representation of the circuit diagram

    Raises:
        OSError: usually indicates that ```pdflatex``` or ```pdftocairo``` is
                 missing.
        CalledProcessError: usually points errors during diagram creation.
    """
    tmpfilename = 'circuit'
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmppath = os.path.join(tmpdirname, tmpfilename + '.tex')
        _generate_latex_source(circuit, filename=tmppath,
                               scale=scale, style=style,
                               plot_barriers=plot_barriers,
                               reverse_bits=reverse_bits)
        image = None
        try:

            subprocess.run(["pdflatex", "-halt-on-error",
                            "-output-directory={}".format(tmpdirname),
                            "{}".format(tmpfilename + '.tex')],
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                           check=True)
        except OSError as ex:
            if ex.errno == errno.ENOENT:
                logger.warning('WARNING: Unable to compile latex. '
                               'Is `pdflatex` installed? '
                               'Skipping latex circuit drawing...')
            raise
        except subprocess.CalledProcessError as ex:
            with open('latex_error.log', 'wb') as error_file:
                error_file.write(ex.stdout)
            logger.warning('WARNING Unable to compile latex. '
                           'The output from the pdflatex command can '
                           'be found in latex_error.log')
            raise
        else:
            try:
                base = os.path.join(tmpdirname, tmpfilename)
                subprocess.run(["pdftocairo", "-singlefile", "-png", "-q",
                                base + '.pdf', base])
                image = Image.open(base + '.png')
                image = _utils._trim(image)
                os.remove(base + '.png')
                if filename:
                    image.save(filename, 'PNG')
            except OSError as ex:
                if ex.errno == errno.ENOENT:
                    logger.warning('WARNING: Unable to convert pdf to image. '
                                   'Is `poppler` installed? '
                                   'Skipping circuit drawing...')
                raise
        return image


def generate_latex_source(circuit, filename=None,
                          basis="id,u0,u1,u2,u3,x,y,z,h,s,sdg,t,tdg,rx,ry,rz,"
                                "cx,cy,cz,ch,crz,cu1,cu3,swap,ccx,cswap",
                          scale=0.7, style=None):
    """Convert QuantumCircuit to LaTeX string.

    Args:
        circuit (QuantumCircuit): input circuit
        scale (float): image scaling
        filename (str): optional filename to write latex
        basis (str): optional comma-separated list of gate names
        style (dict or str): dictionary of style or file name of style file

    Returns:
        str: Latex string appropriate for writing to file.
    """
    warnings.warn('The generate_latex_source() function is deprecated and will'
                  ' be removed in a future release. Instead use the '
                  'circuit_drawer() function with the `output` kwarg set to '
                  '`latex_source`.', DeprecationWarning)
    return _generate_latex_source(circuit, filename=filename,
                                  scale=scale, style=style)


def _generate_latex_source(circuit, filename=None,
                           scale=0.7, style=None, reverse_bits=False,
                           plot_barriers=True):
    """Convert QuantumCircuit to LaTeX string.

    Args:
        circuit (QuantumCircuit): input circuit
        scale (float): image scaling
        filename (str): optional filename to write latex
        style (dict or str): dictionary of style or file name of style file
        reverse_bits (bool): When set to True reverse the bit order inside
            registers for the output visualization.
        plot_barriers (bool): Enable/disable drawing barriers in the output
            circuit. Defaults to True.

    Returns:
        str: Latex string appropriate for writing to file.
    """
    qregs, cregs, ops = _utils._get_instructions(circuit,
                                                 reversebits=reverse_bits)
    qcimg = _latex.QCircuitImage(qregs, cregs, ops, scale, style=style,
                                 plot_barriers=plot_barriers,
                                 reverse_bits=reverse_bits)
    latex = qcimg.latex()
    if filename:
        with open(filename, 'w') as latex_file:
            latex_file.write(latex)
    return latex


# -----------------------------------------------------------------------------
# matplotlib_circuit_drawer
# -----------------------------------------------------------------------------

def matplotlib_circuit_drawer(circuit,
                              basis='id,u0,u1,u2,u3,x,y,z,h,s,sdg,t,tdg,rx,ry,rz,'
                                    'cx,cy,cz,ch,crz,cu1,cu3,swap,ccx,cswap',
                              scale=0.7,
                              filename=None,
                              style=None):
    """Draw a quantum circuit based on matplotlib.
    If `%matplotlib inline` is invoked in a Jupyter notebook, it visualizes a circuit inline.
    We recommend `%config InlineBackend.figure_format = 'svg'` for the inline visualization.

    Args:
        circuit (QuantumCircuit): a quantum circuit
        basis (str): comma separated list of gates
        scale (float): scaling factor
        filename (str): file path to save image to
        style (dict or str): dictionary of style or file name of style file

    Returns:
        PIL.Image: an in-memory representation of the circuit diagram
    """
    warnings.warn('The matplotlib_circuit_drawer() function is deprecated and '
                  'will be removed in a future release. Instead use the '
                  'circuit_drawer() function with the `output` kwarg set to '
                  '`mpl`.', DeprecationWarning)
    return _matplotlib_circuit_drawer(circuit, scale=scale,
                                      filename=filename, style=style)


def _matplotlib_circuit_drawer(circuit,
                               scale=0.7,
                               filename=None,
                               style=None,
                               plot_barriers=True,
                               reverse_bits=False):
    """Draw a quantum circuit based on matplotlib.
    If `%matplotlib inline` is invoked in a Jupyter notebook, it visualizes a circuit inline.
    We recommend `%config InlineBackend.figure_format = 'svg'` for the inline visualization.

    Args:
        circuit (QuantumCircuit): a quantum circuit
        scale (float): scaling factor
        filename (str): file path to save image to
        style (dict or str): dictionary of style or file name of style file
        reverse_bits (bool): When set to True reverse the bit order inside
            registers for the output visualization.
        plot_barriers (bool): Enable/disable drawing barriers in the output
            circuit. Defaults to True.


    Returns:
        matplotlib.figure: a matplotlib figure object for the circuit diagram
    """
    qcd = _matplotlib.MatplotlibDrawer(scale=scale, style=style,
                                       plot_barriers=plot_barriers,
                                       reverse_bits=reverse_bits)
    qcd.parse_circuit(circuit)
    return qcd.draw(filename)
