import pymunk


class Table:
    def __init__(self, space, width, height):
        self.width = width
        self.height = height
        self.margin = 60
        self.pocket_radius = 30

        # Positions des trous
        mw, mh, m = width, height, self.margin
        self.pockets = [
            (m, m), (mw / 2, m - 15), (mw - m, m),
            (m, mh - m), (mw / 2, mh - m + 15), (mw - m, mh - m)
        ]

        self._build_walls(space)

    # Le build_walls utilise des relations au lieu de coordonées, c'est utile pour savoir ou placer les trous
    #@author : Gemini.
    def _build_walls(self, space):
        th = 40
        gap = self.pocket_radius * 2.0
        m_phys = 20
        w, h = self.width, self.height

        walls_coords = [
            ((m_phys, self.margin + gap), (m_phys, h - self.margin - gap)),
            ((w - m_phys, self.margin + gap), (w - m_phys, h - self.margin - gap)),
            ((self.margin + gap, m_phys), (w / 2 - gap, m_phys)),
            ((w / 2 + gap, m_phys), (w - self.margin - gap, m_phys)),
            ((self.margin + gap, h - m_phys), (w / 2 - gap, h - m_phys)),
            ((w / 2 + gap, h - m_phys), (w - self.margin - gap, h - m_phys))
        ]

        for a, b in walls_coords:
            wall = pymunk.Segment(space.static_body, a, b, th)
            wall.elasticity = 0.7
            wall.friction = 0.5
            space.add(wall)