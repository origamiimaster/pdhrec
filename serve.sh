#/bin/bash
eleventy --formats=html,css,js,liquid,md --output=build

python3 -m http.server --directory build