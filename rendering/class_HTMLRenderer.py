# -----------------------------------------------------------------------------
# ---------------------------- class HTMLRenderer -----------------------------
# -----------------------------------------------------------------------------
# This renderer creates a longstring in a HTML format, with interactive
# features managed by JavScript.
# A hidden form is dynamically altered by user interaction, and can be resolved
# on submission, serverside.

from rendering.class_Renderer import Renderer


class HTMLRenderer(Renderer):

    def __init__(self, gm):
        super().__init__(gm)

