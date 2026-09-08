from flask import Blueprint, send_from_directory
import os


director_static = Blueprint(
    "director_static",
    __name__
)


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(__file__)
    )
)



@director_static.route(
    "/director/css/<path:filename>"
)
def director_css(filename):

    return send_from_directory(
        os.path.join(
            BASE_DIR,
            "ui",
            "v92",
            "css"
        ),
        filename
    )



@director_static.route(
    "/director/js/<path:filename>"
)
def director_js(filename):

    return send_from_directory(
        os.path.join(
            BASE_DIR,
            "ui",
            "v92",
            "js"
        ),
        filename
    )
