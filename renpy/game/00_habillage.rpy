


init -5 python:
    POLICE_TITRE = "assets/fonts/KenneyFuture.ttf"
    POLICE_ETROITE = "assets/fonts/KenneyFutureNarrow.ttf"
    POLICE_TERMINAL = "assets/fonts/ShareTechMono-Regular.ttf"

    def carte(nom, survol=False, grise=False):
        """Cadre extensible à partir d'un sprite Kenney (CC0)."""
        image = "assets/ui/%s.png" % nom
        if survol:
            image = im.MatrixColor(image, im.matrix.brightness(0.12))
        if grise:
            image = im.MatrixColor(image, im.matrix.opacity(0.62))
        return Frame(image, 14, 34, 14, 6)

image bg ville = "assets/bg_ville.png"
image bg capuchon = "assets/bg_capuchon.png"
image visage hacker = "assets/visage_hacker.png"
image visage badge = "assets/visage_badge.png"
image visage ombre = "assets/visage_ombre.png"
image visage salle = Fixed(
    Transform("visage hacker", zoom=0.33, xpos=0, ypos=64),
    Transform("visage badge", zoom=0.33, xpos=64, ypos=64),
    Transform("visage ombre", zoom=0.33, xpos=128, ypos=64),
    xysize=(192, 192))


transform panorama:
    subpixel True
    xoffset 0
    linear 45.0 xoffset -120
    linear 45.0 xoffset 0
    repeat


transform respiration:
    subpixel True
    ease 2.4 yoffset -5
    ease 2.4 yoffset 0
    repeat

transform entree:
    alpha 0.0
    linear 0.35 alpha 1.0
