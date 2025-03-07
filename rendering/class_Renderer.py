# -----------------------------------------------------------------------------
# ------------------------------ class Renderer -------------------------------
# -----------------------------------------------------------------------------
# Grandfather class for renderers.

class Renderer():

    def __init__(self, render_object):
        self.render_object = render_object # instance of Abstract_Output

    def main_output():
        pass # here, child methods are called to manage different parts of the output, which is obtained from self.gm.abstract_output methods

    # TODO don't forget interactive elements!
